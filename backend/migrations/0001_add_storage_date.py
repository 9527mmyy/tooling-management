"""迁移 0001：为 tools 表新增 storage_date（入库时间）列。

回填策略：优先取该工装最早一笔入库记录的日期；若无入库记录，则回退到完工日期（purchase_date）。
仅回填 storage_date 为 NULL 的行，故重复执行安全。
"""
from sqlalchemy import text


def upgrade(db):
    with db.engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(tools)")).fetchall()]
        if 'storage_date' not in cols:
            conn.execute(text("ALTER TABLE tools ADD COLUMN storage_date DATE"))

        conn.execute(text("""
            UPDATE tools SET storage_date = COALESCE(
                (SELECT MIN(storage_date) FROM in_storage_records
                 WHERE in_storage_records.tool_id = tools.id),
                purchase_date
            ) WHERE storage_date IS NULL
        """))
