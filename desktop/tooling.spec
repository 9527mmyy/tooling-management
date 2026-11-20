# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：工装管理系统 单机版（onedir）。"""

import os

SRC = os.path.join(os.path.abspath(SPECPATH), 'src')
ICON = os.path.join(os.path.abspath(SPECPATH), 'assets', 'app.ico')

hidden = [
    'paths', 'demo_data', 'app', 'models', 'version', 'scrap_models',
    'routes',
    'routes.auth', 'routes.tools', 'routes.borrows', 'routes.inspections',
    'routes.attachments', 'routes.scraps', 'routes.org', 'routes.configs',
    'routes.export', 'routes.import_tools', 'routes.in_storage',
    'sqlalchemy.dialects.sqlite',
    'webview',
    'webview.platforms.edgechromium',
    'clr_loader',
    'pythonnet',
]

a = Analysis(
    [os.path.join(SRC, 'launcher.py')],
    pathex=[SRC],
    binaries=[],
    datas=[
        (os.path.join(SRC, 'templates'), 'templates'),
        (os.path.join(SRC, 'static'), 'static'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'pytest', 'IPython', 'notebook',
    ],
    noarchive=False,
    optimize=0,
)

# 主界面 HTML 已内嵌进 _web_index.py（PYZ 内），磁盘上不再保留明文副本
a.datas = [d for d in a.datas
           if not d[0].replace('\\', '/').endswith('templates/index.html')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ToolingManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON if os.path.isfile(ICON) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ToolingManagement',
)
