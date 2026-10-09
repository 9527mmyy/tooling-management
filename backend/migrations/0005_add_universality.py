"""迁移 0005：为 tools 表新增 universality（通用性）与 product_drawing_no（专用产品图号）两列。

背景：详情页需要登记工装的通用性（通用 / 专用）。选「专用」时须填写该工装所服务的
**产品图号**（注意：不是工装自身的图号 drawing_no，两者是不同概念）。

存量数据：459 条老数据全部归为「通用」，其 product_drawing_no 留空。

幂等：先判断列是否存在再操作，重复执行安全。
"""
from sqlalchemy import text


def upgrade(db):
    with db.engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(tools)")).fetchall()]

        if 'universality' not in cols:
            # SQLite 的 ADD COLUMN 会把 DEFAULT 值回填到存量行
            conn.execute(text("ALTER TABLE tools ADD COLUMN universality VARCHAR(10) DEFAULT '通用'"))

        if 'product_drawing_no' not in cols:
            conn.execute(text("ALTER TABLE tools ADD COLUMN product_drawing_no VARCHAR(100)"))

        # 兜底：把可能残留的空值统一为「通用」（含列已存在但为 NULL 的情况）
        conn.execute(text("UPDATE tools SET universality = '通用' WHERE universality IS NULL OR universality = ''"))
