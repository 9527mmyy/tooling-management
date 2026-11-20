# -*- coding: utf-8 -*-
"""为打包产物生成完整性校验清单（带 HMAC 签名，防篡改）。

用法：python make_integrity.py

产物：build\\dist\\ToolingManagement\\integrity.json
  { "files": { "相对路径": "sha256", ... }, "sig": "hmac-sha256(清单)" }

启动器（overlay/launcher.py）会读取并校验它。签名密钥两边必须一致。
"""

import hashlib
import hmac
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, 'build', 'dist', 'ToolingManagement')
OUT_NAME = 'integrity.json'

# 必须与 overlay/launcher.py 中的 _INTEGRITY_KEY 一致
KEY = b'tooling-mgmt-integrity-v1-2026'


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    if not os.path.isdir(DIST):
        raise SystemExit(f'找不到打包产物目录：{DIST}\n请先运行 PyInstaller 构建。')

    out = os.path.join(DIST, OUT_NAME)
    if os.path.isfile(out):
        os.remove(out)

    entries = {}
    for root, _dirs, files in os.walk(DIST):
        for name in files:
            p = os.path.join(root, name)
            rel = os.path.relpath(p, DIST).replace('\\', '/')
            if rel == OUT_NAME or rel.startswith('unins'):
                continue
            entries[rel] = sha256_file(p)

    payload = json.dumps(entries, sort_keys=True, separators=(',', ':'))
    sig = hmac.new(KEY, payload.encode('utf-8'), hashlib.sha256).hexdigest()

    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'files': entries, 'sig': sig}, f,
                  sort_keys=True, separators=(',', ':'))

    total = sum(os.path.getsize(os.path.join(DIST, k.replace('/', os.sep)))
                for k in entries)
    print(f'完整性清单已生成：{out}')
    print(f'  文件数 {len(entries)} 个，合计 {total / 1048576:.1f} MB')


if __name__ == '__main__':
    main()
