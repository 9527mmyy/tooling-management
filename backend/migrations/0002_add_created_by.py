"""迁移 0002：为 tools 表新增 created_by（建档人）列。

回填策略：优先取该工装最早一笔入库记录的操作人（operator）；若无则留空。
仅回填 created_by 为 NULL 的行，故重复执行安全。
"""
from sqlalchemy import text


def upgrade(db):
    with db.engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(tools)")).fetchall()]
        if 'created_by' not in cols:
            conn.execute(text("ALTER TABLE tools ADD COLUMN created_by VARCHAR(80)"))

        conn.execute(text("""
            UPDATE tools SET created_by = (
                SELECT operator FROM in_storage_records
                WHERE in_storage_records.tool_id = tools.id
                  AND operator IS NOT NULL AND operator != ''
                ORDER BY storage_date ASC LIMIT 1
            ) WHERE created_by IS NULL
        """))
