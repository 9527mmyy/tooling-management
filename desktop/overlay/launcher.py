# -*- coding: utf-8 -*-
"""工装管理系统 · 单机版启动器（打包工程文件，不属于原系统源码）。

流程：
  1. 启动前校验程序文件完整性，被改动则告警（防替换 / 防篡改）
  2. 探测端口是否已有本系统实例在跑；有则直接开窗口（天然单实例）
  3. 否则在后台线程里起 Flask 服务（只监听 127.0.0.1，不对外网 / 局域网开放）
  4. 端口就绪后用 pywebview 打开原生窗口指向本机地址
  5. 窗口关闭即退出（后台线程为 daemon）

登录：打包版对本机来源自动以管理员身份建立会话，不再要求输入密码；
非本机来源不会被自动登录（服务本身也只监听本机，外部访问不到）。

性能注意：本机探测一律**绕过系统代理**。本机若配了 http_proxy，
urllib 会把 127.0.0.1 的请求也交给代理，连不上就干等到超时（实测白耗 2 秒）。

启动各阶段耗时写入日志（`[启动计时]` 前缀），用于诊断启动慢。
"""

import atexit
import os
import socket
import subprocess
import sys
import threading
import time

_PROC_T0 = time.time()

_BASE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

import paths  # noqa: E402

WINDOW_TITLE = '工装管理系统'
START_TIMEOUT = 40.0
LOG_MAX_BYTES = 2 * 1024 * 1024

# 完整性校验（签名密钥必须与 make_integrity.py 中的 KEY 一致）
_INTEGRITY_KEY = b'tooling-mgmt-integrity-v1-2026'
_INTEGRITY_FILE = 'integrity.json'

# 无窗口模式（--service）：不弹任何对话框，避免无人值守时被阻塞
_HEADLESS = False

def _tick(label):
    """记录启动阶段耗时与时刻（写日志），用于诊断启动慢。"""
    print(f'[启动计时] {label}: {time.time() - _PROC_T0:.3f}s'
          f'（{time.strftime("%H:%M:%S")}）')


def _setup_logging():
    """把 stdout / stderr 收进数据目录的 UTF-8 日志文件。

    console=False 的打包形态下 stdout 默认编码是 GBK（Windows ANSI），
    原系统源码里的 emoji 输出会抛 UnicodeEncodeError，把 Flask 线程打挂。
    这里统一重定向为 UTF-8 文件，顺带留下运行日志。
    """
    try:
        logfile = os.path.join(paths.data_dir(), 'app.log')
        try:
            if os.path.getsize(logfile) > LOG_MAX_BYTES:
                os.replace(logfile, logfile + '.1')
        except OSError:
            pass
        f = open(logfile, 'a', encoding='utf-8', buffering=1)
        sys.stdout = f
        sys.stderr = f
        return f
    except Exception:
        class _Null:
            encoding = 'utf-8'

            def write(self, *_a):
                return 0

            def flush(self):
                pass

        sys.stdout = _Null()
        sys.stderr = _Null()
        return None


def _msgbox(text, title=WINDOW_TITLE, flags=0x10):
    """可见提示。返回 MessageBox 的返回值（IDYES = 6）。

    无窗口模式下改为写日志，不弹窗（否则无人值守时会被对话框挂住）。
    """
    if _HEADLESS:
        print(f'[提示] {text.replace(chr(10), " | ")}')
        return 0
    try:
        import ctypes
        return ctypes.windll.user32.MessageBoxW(0, text, title, flags)
    except Exception:
        print(text)
        return 0


def _verify_integrity():
    """校验程序文件是否被改动。

    返回 (是否通过, 有问题的文件列表, 补充说明)。
    未打包的开发模式不校验（源码调试时文件本来就在变）。
    """
    if not paths.is_frozen():
        return True, [], ''

    import hashlib
    import hmac
    import json

    base = os.path.dirname(sys.executable)
    manifest = os.path.join(base, _INTEGRITY_FILE)
    if not os.path.isfile(manifest):
        return False, [], f'缺少完整性清单文件 {_INTEGRITY_FILE}'

    try:
        with open(manifest, encoding='utf-8') as f:
            doc = json.load(f)
    except Exception as exc:
        return False, [], f'完整性清单无法解析：{exc}'

    files = doc.get('files') or {}
    sig = doc.get('sig') or ''
    payload = json.dumps(files, sort_keys=True, separators=(',', ':'))
    expect = hmac.new(_INTEGRITY_KEY, payload.encode('utf-8'),
                      hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expect):
        return False, [], '完整性清单签名不匹配（清单本身被篡改）'

    changed = []
    for rel, want in files.items():
        p = os.path.join(base, rel.replace('/', os.sep))
        if not os.path.isfile(p):
            changed.append(rel + '  [文件缺失]')
            continue
        h = hashlib.sha256()
        try:
            with open(p, 'rb') as f:
                for chunk in iter(lambda: f.read(1 << 20), b''):
                    h.update(chunk)
        except OSError:
            changed.append(rel + '  [无法读取]')
            continue
        if h.hexdigest() != want:
            changed.append(rel)

    return (not changed), changed, ''


def _port_open(host, port, timeout=0.2):
    """端口是否已被占用（短超时：本机连接若被安全软件丢包不会立即拒绝）。"""
    probe = '127.0.0.1' if host in ('0.0.0.0', '::', '') else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((probe, port)) == 0


def _is_our_service(port):
    """确认占用端口的是本系统而非其他程序。

    必须绕过系统代理：本机若配了 http_proxy，urllib 会把 127.0.0.1 的请求
    也交给代理，代理连不上就干等到超时（实测多花 2 秒）。
    """
    import json
    import urllib.request
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/api/health', timeout=1.5) as r:
            data = json.loads(r.read().decode('utf-8'))
        return data.get('service') == 'tooling-management'
    except Exception:
        return False


def _wait_ready(port, timeout=START_TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _SRV['err'] is not None:
            return False          # 绑定失败，不必再等满超时
        if _is_our_service(port):
            return True
        time.sleep(0.05)
    return False


# 服务对象与启动结果：主进程要能主动关掉监听，才能把端口立刻让出来
_SRV = {'obj': None, 'err': None}


def _close_listen(srv):
    try:
        srv.server_close()
    except Exception:
        pass


def _stop_server():
    """停掉后台服务并释放端口。窗口关闭与进程退出各调一次，重复调用无害。"""
    srv = _SRV.get('obj')
    _SRV['obj'] = None
    if srv is None:
        return
    try:
        srv.shutdown()            # 让 serve_forever() 退出
    except Exception:
        pass
    _close_listen(srv)


def _serve(port):
    """后台线程：起 WSGI 服务。

    用 make_server 而不是 app.run —— 拿到服务对象后，窗口关闭时可以主动
    shutdown() 把监听端口立刻释放。否则上一次刚退出、端口还没让出来的那
    一瞬间再启动，就会被误判成「端口已被其他程序占用」。
    """
    # 是否「全新安装」必须在 import app 之前判定：import 会执行 db.create_all() 建库。
    # 已有台账的机器（覆盖安装）fresh=False，绝不写示例数据。
    fresh = not os.path.isfile(paths.data_path('tooling.db'))
    try:
        _tick('开始导入 app')
        from app import app
        _tick('app 导入完成（含路由注册与建库）')
        if fresh:
            try:
                import demo_data
                from models import db as _db
                n = demo_data.seed(app, _db)
                print('[示例] 全新安装写入 %d 条示例工装（DEMO-*，可删除）' % n)
            except Exception as exc:
                print('[WARN] 示例数据写入失败（不影响使用）：%s' % exc)
        from werkzeug.serving import make_server
        srv = make_server(paths.host(), port, app, threaded=True)
        _SRV['obj'] = srv
        _tick('监听已建立')
    except Exception as exc:
        _SRV['err'] = exc
        return
    try:
        srv.serve_forever()
    finally:
        _close_listen(srv)


def _is_maximized():
    """窗口当前是否处于最大化状态。"""
    try:
        import ctypes

        u = ctypes.windll.user32

        class _WP(ctypes.Structure):
            _fields_ = [('length', ctypes.c_uint), ('flags', ctypes.c_uint),
                        ('showCmd', ctypes.c_uint),
                        ('ptMin', ctypes.c_long * 2), ('ptMax', ctypes.c_long * 2),
                        ('rc', ctypes.c_long * 4)]

        hwnd = u.FindWindowW(None, WINDOW_TITLE)
        if not hwnd:
            return False
        wp = _WP()
        wp.length = ctypes.sizeof(wp)
        return bool(u.GetWindowPlacement(hwnd, ctypes.byref(wp))) and wp.showCmd == 3
    except Exception:
        return False


def _ensure_maximized(win, delay=0.6):
    """兜底确认窗口最终是最大化的。

    create_window 的 maximized=True 在部分机器上要等 WebView2 布局完才生效，
    表现是「先冒出小窗口、过一两秒才铺满」。这里等窗口先正常显示出来，再用
    pywebview 自己的 maximize() 补一次（走 GUI 层，不绕过布局，避免错位）；
    一旦确认已最大化就收手，之后不再干预，用户可以自由还原窗口。
    """
    time.sleep(delay)
    deadline = time.time() + 15
    while time.time() < deadline:
        if _is_maximized():
            _tick('窗口已最大化')
            return
        try:
            win.maximize()
        except Exception:
            pass
        time.sleep(0.3)


def _port_owner(port):
    """查出占用端口的进程，用于报错时给出可操作的信息。查不到返回空串。"""
    try:
        out = subprocess.run(
            ['netstat', '-ano', '-p', 'tcp'],
            capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ''
    for line in out.splitlines():
        if f':{port}' not in line or 'LISTENING' not in line.upper():
            continue
        parts = line.split()
        pid = parts[-1]
        name = ''
        try:
            info = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/NH', '/FO', 'CSV'],
                capture_output=True, text=True, timeout=5).stdout
            name = info.split(',')[0].strip('"')
        except Exception:
            pass
        return f'占用进程：{name or "未知"}（PID {pid}）'
    return ''


def _probe_existing(port, grace=8.0):
    """端口上是否已有本系统实例在跑。返回 (已有实例, 占用者说明)。

    给一段宽限期：上一实例刚关闭时，监听端口往往还没释放完（进程在收尾、
    连接还在 TIME_WAIT），此时连得上但服务已不响应。若那一刻就下结论，会
    误报成「端口已被其他程序占用」——表现就是关掉再开报端口问题、再开一次
    又正常。这里反复确认，端口一旦空出来就照常启动自己的服务。
    """
    if not _port_open(paths.host(), port):
        return False, ''
    deadline = time.time() + grace
    while True:
        if _is_our_service(port):
            return True, ''
        if not _port_open(paths.host(), port):
            return False, ''      # 端口已空出，说明只是上一实例的残留
        if time.time() >= deadline:
            return False, _port_owner(port)
        time.sleep(0.4)


def main():
    global _HEADLESS
    _setup_logging()
    _tick('日志就绪')
    headless = '--service' in sys.argv[1:]
    _HEADLESS = headless

    # 启动前先验完整性
    ok, changed, note = _verify_integrity()
    _tick('完整性校验完成')
    if not ok:
        if changed:
            detail = '\n'.join(changed[:12])
            if len(changed) > 12:
                detail += f'\n…… 另有 {len(changed) - 12} 个文件'
        else:
            detail = note
        msg = ('程序文件完整性校验未通过，检测到以下文件被修改、替换或缺失：\n\n'
               + detail
               + '\n\n为避免使用被篡改的程序，已停止启动。\n'
                 '若确认是误删或被安全软件改动，请重新运行安装包恢复原文件。')
        print('完整性校验失败：\n' + msg)
        if not headless:
            _msgbox(msg, flags=0x10)   # MB_ICONERROR + 仅「确定」
        return 3

    port = paths.port()
    # 先做零成本的端口探测，只有端口确实开着才发 HTTP 请求确认身份
    already, owner = _probe_existing(port)
    _tick(f'端口探测完成（{port} 已有实例={already}）')

    if not already:
        if owner:
            _msgbox(f'端口 {port} 已被其他程序占用，无法启动。\n{owner}\n\n'
                    f'请关闭该程序后重试；若它必须常驻，可在数据目录下的 '
                    f'config.json 里写 {{"port": 8788}} 换个端口。')
            return 1
        atexit.register(_stop_server)
        server = threading.Thread(target=_serve, args=(port,),
                                  name='flask', daemon=True)
        server.start()
        if not _wait_ready(port):
            err = _SRV['err']
            if err is not None:
                _msgbox(f'服务启动失败（端口 {port}）：{err}\n\n'
                        f'多半是端口被占用或被安全软件拦截。')
            else:
                _msgbox(f'服务启动超时（端口 {port}）。\n'
                        f'请检查数据目录权限或被安全软件拦截。')
            return 1
        _tick('Flask 服务就绪')
    else:
        server = None
        if headless:
            return 0  # 已有实例在跑，服务模式无需重复启动

    if headless:
        # 只提供服务，不开窗口（脚本 / 调试用）
        try:
            while True:
                if server is not None and not server.is_alive():
                    _msgbox('服务线程异常退出，请查看数据目录下的 app.log。')
                    return 1
                time.sleep(5)
        except KeyboardInterrupt:
            pass
        return 0

    _tick('开始导入 webview')
    import webview
    _tick('webview 导入完成')

    # 单窗口：窗口先以品牌底色出现，页面渲染后由前端启动占位播放动画，再淡出到主界面。
    # 不另开启动画面窗口——两个窗口要各自初始化一遍 WebView2，实测多花 1~2 秒，
    # 且第二个窗口的 HTML 往往还没画出来就被销毁，屏幕上只留一片纯色。
    win = webview.create_window(
        WINDOW_TITLE,
        # app=1：告诉页面这是单机窗口，标题栏已经有系统名，侧边栏不再重复显示
        f'http://127.0.0.1:{port}/?app=1',
        width=1360, height=880, min_size=(1024, 680),
        maximized=True,                    # 打开即铺满屏幕；保留标题栏，便于最小化 / 关闭
        background_color='#1e3a8a',        # WebView2 首帧前的底色，与启动画面同色系
    )
    _tick('窗口对象已创建，进入事件循环（此后由 WebView2 接管）')

    # 窗口一关就把监听端口放掉，下一次启动不用等上一次收尾
    try:
        win.events.closed += lambda: _stop_server()
    except Exception:
        pass

    # 窗口显示后补一次最大化（shown 事件 + 延迟轮询兜底）
    try:
        win.events.shown += lambda: win.maximize()
    except Exception:
        pass
    threading.Thread(target=_ensure_maximized, args=(win,),
                     name='maximize', daemon=True).start()

    webview.start()
    _stop_server()      # 兜底：事件没触发时，退出前也要把端口让出来
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # 顶层兜底，保证无控制台时用户能看到原因
        import traceback
        _msgbox(f'启动失败：{exc}\n\n{traceback.format_exc()[-1200:]}')
        sys.exit(1)
