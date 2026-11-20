# -*- coding: utf-8 -*-
"""全新安装时写入的示例台账（仅 3 条，便于认识界面，可随时删除）。

调用条件由 launcher 控制：只有数据目录里原本没有 tooling.db 时才 seed。
覆盖安装 / 已有台账的机器一律不写，不会污染真实数据。

本文件属于打包工程 overlay，随 sync_src.py 复制进 src/，不改动原系统源码。
"""

# 编号统一 DEMO- 前缀、名称带「示例」，一眼能与真实台账区分。
DEMO_TOOLS = [
    {
        'code': 'DEMO-001',
        'name': '示例-焊接定位夹具',
        'drawing_no': 'DEMO-TZ-001',
        'spec': '示例规格 300x200',
        'category': '夹具类',
        'level': 'A',
        'factory': '示例分厂',
        'team': '示例班组',
        'status': '在库',
        'remark': '示例数据，可直接在系统里删除',
        'universality': '通用',
        'created_by': '示例',
    },
    {
        'code': 'DEMO-002',
        'name': '示例-装配检具',
        'drawing_no': 'DEMO-TZ-002',
        'spec': '示例规格 L500',
        'category': '量具类',
        'level': 'B',
        'factory': '示例分厂',
        'team': '示例班组',
        'status': '在库',
        'remark': '示例数据，可直接在系统里删除',
        'universality': '通用',
        'created_by': '示例',
    },
    {
        'code': 'DEMO-003',
        'name': '示例-钎焊工装',
        'drawing_no': 'DEMO-TZ-003',
        'spec': '示例规格 400x300',
        'category': '夹具类',
        'level': 'A',
        'factory': '示例分厂',
        'team': '示例班组',
        'status': '在库',
        'remark': '示例数据，可直接在系统里删除',
        'universality': '专用',
        'product_drawing_no': 'DEMO-CP-001',
        'created_by': '示例',
    },
]


def seed(app, db):
    """写入示例台账，返回实际写入条数。已有任何台账时不写。"""
    from models import Tool
    with app.app_context():
        if Tool.query.count() > 0:
            return 0
        n = 0
        for item in DEMO_TOOLS:
            if Tool.query.filter_by(code=item['code']).first():
                continue
            db.session.add(Tool(**item))
            n += 1
        if n:
            db.session.commit()
        return n
