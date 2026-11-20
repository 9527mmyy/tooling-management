# -*- coding: utf-8 -*-
"""运行路径与运行参数解析（单机打包版覆盖文件）。

本文件由打包工程覆盖进 src/，不属于原系统源码。

同一套代码要能跑两种形态：

  1. 服务模式 / 开发模式（直接 python app.py，未打包）
     资源与数据都在 src/ 目录下。

  2. 单机模式（PyInstaller 打包后的 exe，sys.frozen 为真）
     只读资源（templates / static）在 exe 的解压目录里；
     可写数据（数据库 / 上传件 / 密钥）落到用户级数据目录；
     服务只监听 127.0.0.1，不对局域网 / 外网开放。

判定依据只有 sys.frozen。未打包时所有函数退化为原行为。
"""

import os
import sys

# 数据目录名
APP_DIR_NAME = 'ToolingManagement'

# 单机版默认监听端口。5000 是服务端常见端口，单机版另取其一避免冲突。
DEFAULT_PORT_FROZEN = 8765
# 未打包调试时的端口。不用 5000：该端口通常是联网版主系统在用，
# 调试启动器会把它误判成本系统实例而直接连过去（表现为弹出联网版的登录页）。
DEFAULT_PORT_DEV = 18765

# 旧服务部署的密钥文件：可用 TOOLING_LEGACY_SECRET 环境变量指向，默认不读取。
_LEGACY_SECRET = os.environ.get('TOOLING_LEGACY_SECRET', '')


def is_frozen():
    """是否为 PyInstaller 打包后的运行形态。"""
    return bool(getattr(sys, 'frozen', False))


def _here():
    return os.path.dirname(os.path.abspath(__file__))


def resource_dir():
    """只读资源根目录（templates / static 所在处）。"""
    if is_frozen():
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return _here()


def _writable(d):
    try:
        os.makedirs(d, exist_ok=True)
        probe = os.path.join(d, '.write_probe')
        with open(probe, 'w', encoding='utf-8') as f:
            f.write('ok')
        os.remove(probe)
        return True
    except OSError:
        return False


def data_dir():
    """可写数据根目录（tooling.db / uploads / secret.key 所在处）。

    打包形态优先用 %LOCALAPPDATA%（单机自用，用户级目录，无需特殊权限），
    不可写时回退到 %ProgramData% 与用户主目录。
    """
    override = os.environ.get('TOOLING_DATA_DIR')
    if override:
        os.makedirs(override, exist_ok=True)
        return override
    if not is_frozen():
        return _here()

    candidates = []
    if os.environ.get('LOCALAPPDATA'):
        candidates.append(os.path.join(os.environ['LOCALAPPDATA'], APP_DIR_NAME))
    if os.environ.get('PROGRAMDATA'):
        candidates.append(os.path.join(os.environ['PROGRAMDATA'], APP_DIR_NAME))
    candidates.append(os.path.join(os.path.expanduser('~'), '.' + APP_DIR_NAME))
    for d in candidates:
        if _writable(d):
            return d
    return candidates[-1]


def resource_path(*parts):
    return os.path.join(resource_dir(), *parts)


def data_path(*parts):
    return os.path.join(data_dir(), *parts)


def db_uri():
    """SQLAlchemy 数据库地址。"""
    return 'sqlite:///' + data_path('tooling.db')


def upload_dir():
    """上传件目录，确保存在后返回。"""
    d = data_path('uploads')
    os.makedirs(d, exist_ok=True)
    return d


def secret_key():
    """会话密钥。

    优先顺序：环境变量 > 数据目录密钥文件（首次运行自动生成）
              > 可选旧密钥文件（TOOLING_LEGACY_SECRET）> 现场生成并持久化。
    """
    v = os.environ.get('TOOLING_SECRET_KEY')
    if v:
        return v

    keyfile = data_path('secret.key')
    if os.path.isfile(keyfile):
        try:
            with open(keyfile, encoding='utf-8') as f:
                v = f.read().strip()
        except OSError:
            v = ''
        if v:
            return v

    # 未打包调试时，若显式指定了旧密钥文件则沿用
    if not is_frozen() and _LEGACY_SECRET:
        try:
            with open(_LEGACY_SECRET, encoding='utf-8') as f:
                v = f.read().strip()
        except OSError:
            v = ''
        if v:
            return v

    # 生成并持久化
    import secrets as _secrets
    v = _secrets.token_hex(32)
    try:
        with open(keyfile, 'w', encoding='utf-8') as f:
            f.write(v)
    except OSError:
        pass
    return v


def port():
    """监听端口：TOOLING_PORT 环境变量 > 数据目录 config.json > 默认值。"""
    env = os.environ.get('TOOLING_PORT')
    if env and env.isdigit():
        return int(env)
    cfg = data_path('config.json')
    if os.path.isfile(cfg):
        try:
            import json
            with open(cfg, encoding='utf-8') as f:
                p = json.load(f).get('port')
            if isinstance(p, int) and 1 <= p <= 65535:
                return p
        except (OSError, ValueError):
            pass
    return DEFAULT_PORT_FROZEN if is_frozen() else DEFAULT_PORT_DEV


def host():
    """监听地址：单机版只允许本机访问，不对外网 / 局域网开放。"""
    return os.environ.get('TOOLING_HOST') or '127.0.0.1'
