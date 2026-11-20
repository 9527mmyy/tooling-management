# -*- coding: utf-8 -*-
"""从原系统抽取源码快照到 src/，并施加单机化补丁。

原系统目录只读不写，保证零改动、零风险。

用法：python sync_src.py

注：曾尝试把 routes/export.py 与 routes/import_tools.py 的顶层 openpyxl 导入改成
惰性加载（可省约 210ms 启动时间）。但 Python 的模块级 __getattr__ 只拦截
`module.attr` 形式的属性访问，不会拦截函数体内的裸名字查找（`Font(...)`），
改用代理对象又过于非常规，收益与风险不成比例，故放弃。
"""

import base64
import os
import shutil
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
# 原系统仓库与本工程的相对关系：<repo>/backend + <repo>/desktop
SRC_IN = os.path.normpath(os.path.join(HERE, os.pardir, 'backend'))
DST = os.path.join(HERE, 'src')
OVERLAY = os.path.join(HERE, 'overlay')

# 不抽取的内容
SKIP_DIRS = {'venv', '__pycache__', '.ruff_cache', 'uploads', 'temp', 'devtools'}
SKIP_FILES = {'tooling.db', 'tooling.db-shm', 'tooling.db-wal'}

# 按文件分组的补丁：(目标文件相对路径, [(原文, 替换, 是否允许出现多次), ...])
FILE_PATCHES = [
    ('app.py', [
        # 1) 引入 paths
        (
            "from flask import Flask, send_from_directory, make_response, redirect\n",
            "from flask import Flask, send_from_directory, make_response, redirect\n"
            "import paths\n",
            False,
        ),
        # 2) 静态/模板目录改绝对路径（send_from_directory 依赖 CWD，打包后会失效）
        (
            "app = Flask(__name__, static_folder='static', template_folder='templates')",
            "app = Flask(__name__, static_folder=paths.resource_path('static'), "
            "template_folder=paths.resource_path('templates'))",
            False,
        ),
        # 3) 数据目录改可写目录（__file__ 在打包后指向只读临时目录）
        (
            "basedir = os.path.abspath(os.path.dirname(__file__))",
            "basedir = paths.data_dir()",
            False,
        ),
        # 4) 会话密钥改由 paths 统一管理
        #    2026-11-04 原系统把 _read_secret 重写成「环境变量 > 密钥文件 > 现场生成」，
        #    旧补丁整段精确匹配必然失配。这里只改赋值行：函数定义留在副本里成为死代码，
        #    不再被调用，也不会往 basedir 上级写 _secrets。
        #    打包版的密钥仍由 paths.secret_key() 落在 %LOCALAPPDATA%\ToolingManagement，
        #    与上一版完全一致，覆盖安装后已登录会话不受影响。
        (
            "app.config['SECRET_KEY'] = _read_secret('TOOLING_SECRET_KEY')",
            "app.config['SECRET_KEY'] = paths.secret_key()",
            False,
        ),
        # 5) 模板目录（3 处）
        (
            "send_from_directory('templates',",
            "send_from_directory(paths.resource_path('templates'),",
            True,
        ),
        # 6) 监听参数
        (
            "app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)",
            "app.run(debug=False, host=paths.host(), port=paths.port(), "
            "threaded=True, use_reloader=False)",
            False,
        ),
        # 7) 单机版免登录（只认本机来源）+ 主界面内嵌服务函数
        (
            "from models import db\ndb.init_app(app)\n",
            "from models import db\n"
            "db.init_app(app)\n"
            "\n"
            "\n"
            "@app.before_request\n"
            "def _auto_login_local():\n"
            "    \"\"\"单机版：本机访问自动以管理员身份建立会话，不再要求输入密码。\"\"\"\n"
            "    from flask import request, session as _s\n"
            "    if 'user_id' in _s:\n"
            "        return\n"
            "    if request.remote_addr not in ('127.0.0.1', '::1'):\n"
            "        return\n"
            "    from models import User\n"
            "    from datetime import datetime as _dt\n"
            "    admin = User.query.filter_by(username='admin').first()\n"
            "    if not admin:\n"
            "        return\n"
            "    _s.permanent = True\n"
            "    _s['user_id'] = admin.id\n"
            "    _s['username'] = admin.username\n"
            "    _s['user_no'] = admin.user_no\n"
            "    _s['role'] = admin.role\n"
            "    _s['last_activity'] = _dt.now().isoformat()\n"
            "\n"
            "\n"
            "def _serve_embedded_index():\n"
            "    \"\"\"返回内嵌在程序里的主界面：磁盘上不留明文 HTML。\"\"\"\n"
            "    import _web_index\n"
            "    response = make_response(_web_index.INDEX_HTML)\n"
            "    response.headers['Content-Type'] = 'text/html; charset=utf-8'\n"
            "    response.headers['Cache-Control'] = "
            "'no-store, no-cache, must-revalidate, max-age=0'\n"
            "    response.headers['Pragma'] = 'no-cache'\n"
            "    response.headers['Expires'] = '0'\n"
            "    return response\n",
            False,
        ),
        # 8) 两个入口路由改为返回内嵌界面（原为从磁盘读 templates/index.html）
        (
            "    response = make_response(send_from_directory("
            "paths.resource_path('templates'), 'index.html'))\n"
            "    response.headers['Cache-Control'] = "
            "'no-store, no-cache, must-revalidate, max-age=0'\n"
            "    response.headers['Pragma'] = 'no-cache'\n"
            "    response.headers['Expires'] = '0'\n"
            "    return response",
            "    return _serve_embedded_index()",
            True,   # / 与 /tooling 两处
        ),
    ]),
]


def copy_tree():
    # 增量覆盖：不清空 src，避免触发批量删除限制；原系统删除的文件会残留，
    # 对本项目（templates / static 极少删文件）无实际影响。
    os.makedirs(DST, exist_ok=True)
    for root, dirs, files in os.walk(SRC_IN):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel = os.path.relpath(root, SRC_IN)
        target_root = DST if rel == '.' else os.path.join(DST, rel)
        os.makedirs(target_root, exist_ok=True)
        for f in files:
            if f in SKIP_FILES or f.endswith(('.log', '.pyc')):
                continue
            shutil.copy2(os.path.join(root, f), os.path.join(target_root, f))
    # 打包工程不保留任何业务数据库：早期版本残留的 tooling.db* 一律清掉。
    # spec 的 datas 本就不含它们，这里防止 src/ 被误当成分发素材。
    for _name in ('tooling.db', 'tooling.db-shm', 'tooling.db-wal'):
        _p = os.path.join(DST, _name)
        if os.path.isfile(_p):
            os.remove(_p)
            print('      清除残留数据库 ->', _name)
    print('[1/4] 源码快照完成 ->', DST)


def apply_overlay():
    for name in sorted(os.listdir(OVERLAY)):
        src = os.path.join(OVERLAY, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(DST, name))
            print('      覆盖 ->', name)


def embed_index():
    """把主界面 HTML 压缩内嵌成 Python 模块，编进 PYZ，磁盘上不留明文。"""
    src = os.path.join(SRC_IN, 'templates', 'index.html')
    if not os.path.isfile(src):
        print(f'[内嵌失败] 找不到源文件：{src}')
        sys.exit(2)
    with open(src, 'rb') as f:
        raw = f.read()

    data = base64.b64encode(zlib.compress(raw, 9)).decode('ascii')
    body = '\n'.join("    '%s'" % data[i:i + 96]
                     for i in range(0, len(data), 96))
    code = (
        "# -*- coding: utf-8 -*-\n"
        '"""主界面 HTML（构建时从原系统 templates/index.html 内嵌生成）。\n'
        "\n"
        "本文件由 sync_src.py 自动生成，请勿手工修改。\n"
        "内嵌目的是不在磁盘上留下明文界面代码。\n"
        '"""\n'
        "import base64\n"
        "import zlib\n"
        "\n"
        "_DATA = (\n"
        + body + "\n"
        ")\n"
        "\n"
        "INDEX_HTML = zlib.decompress(base64.b64decode(_DATA)).decode('utf-8')\n"
    )
    out = os.path.join(DST, '_web_index.py')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f'      内嵌主界面 -> _web_index.py（原 {len(raw)} 字节 → 内嵌 {len(data)} 字符）')


def patch_files():
    total = 0
    for rel, patches in FILE_PATCHES:
        p = os.path.join(DST, rel.replace('/', os.sep))
        if not os.path.isfile(p):
            print(f'[补丁失败] 目标文件不存在：{rel}')
            sys.exit(2)
        with open(p, encoding='utf-8-sig') as f:
            text = f.read()
        for old, new, many in patches:
            n = text.count(old)
            if n == 0:
                print(f'[补丁失败] {rel} 未命中：{old.splitlines()[0][:70]!r}')
                print('  原系统对应文件可能已改动，请检查 FILE_PATCHES 定义。')
                sys.exit(2)
            if not many and n > 1:
                print(f'[补丁警告] {rel} 命中 {n} 次（预期 1 次）：'
                      f'{old.splitlines()[0][:70]!r}')
            text = text.replace(old, new)
            total += 1
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
    print(f'[3/4] 补丁已应用：{total} 处，涉及 {len(FILE_PATCHES)} 个文件')


if __name__ == '__main__':
    copy_tree()
    apply_overlay()
    embed_index()
    patch_files()
    print('[4/4] 同步完成。')
