"""
一次性数据修补：回填 A/B 级工装缺失的「下次检定日期」

背景
    系统按「等级 + 基准日」推算下次检定日期（A=半年，B=一年，C=不检定）。
    但前端推算逻辑挂在 Vue watch 上，只在「新增保存」或「等级/入库时间发生变化」的
    瞬间执行，且不回填存量。因此等级早已调好、但下次检定日期为空的记录会被永久漏掉，
    也不会进入「检定提醒」（提醒接口过滤 next_inspection_date != None）。

    典型漏项：GZ020395-00 / GZ020396-00 / GZ020397-00 / GZ020398-00
    （2026-09-21 批量由 C 调为 A，入库时间 2026-09-18，应排 2027-03-18）

算法
    加月后对齐月末，避免 JS/朴素实现的溢出进位问题：
      2026-08-31 + 6 月 = 2027-02-28（而非 2027-03-03）
      2026-12-31 + 6 月 = 2027-06-30（而非 2027-07-01）

用法
    python fix_next_inspection_dates.py            # 只读预览（dry-run）
    python fix_next_inspection_dates.py --apply    # 实际写入
"""
import sqlite3
import calendar
import datetime
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tooling.db")
APPLY = "--apply" in sys.argv


def add_months(d, months):
    """加 N 个月，若目标月无该日则对齐到月末（避免溢出进位）。"""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return datetime.date(y, m, min(d.day, last_day))


def calc_next_inspection(level, storage_date):
    """按等级与入库时间推算下次检定日期；C 级或无基准日返回 None。"""
    if not storage_date or level not in ("A", "B"):
        return None
    base = datetime.date.fromisoformat(str(storage_date)[:10])
    return add_months(base, 6 if level == "A" else 12)


def main():
    if not os.path.exists(DB_PATH):
        print("找不到数据库: %s" % DB_PATH)
        return 1

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cur.execute(
        """
        SELECT id, code, level, storage_date, next_inspection_date
          FROM tools
         WHERE level IN ('A', 'B')
           AND storage_date IS NOT NULL AND storage_date <> ''
           AND (next_inspection_date IS NULL OR next_inspection_date = '')
         ORDER BY id
        """
    )
    rows = [dict(r) for r in cur.fetchall()]

    print("待补算记录: %d 条" % len(rows))
    plan = []
    for r in rows:
        nd = calc_next_inspection(r["level"], r["storage_date"])
        if nd is None:
            continue
        plan.append((r["id"], r["code"], r["level"], str(r["storage_date"]), str(nd)))
        print("  id=%-4s %-14s 等级=%s  入库=%s  ->  下次检定=%s"
              % (r["id"], r["code"], r["level"], r["storage_date"], nd))

    if not plan:
        print("\n无待补算记录，未做任何改动。")
        con.close()
        return 0

    if not APPLY:
        print("\n[DRY-RUN] 未写入数据库。确认无误后加 --apply 执行。")
        con.close()
        return 0

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.executemany(
        "UPDATE tools SET next_inspection_date = ?, updated_at = ? WHERE id = ?",
        [(p[4], now, p[0]) for p in plan],
    )
    con.commit()
    print("\n[APPLY] 已提交 %d 行，updated_at = %s" % (len(plan), now))

    ids = ",".join(str(p[0]) for p in plan)
    cur.execute(
        "SELECT id, code, level, storage_date, next_inspection_date, updated_at "
        "FROM tools WHERE id IN (%s) ORDER BY id" % ids
    )
    print("--- 写入后复核 ---")
    for r in cur.fetchall():
        d = dict(r)
        print("  id=%-4s %-14s 等级=%s 入库=%s 下次检定=%s"
              % (d["id"], d["code"], d["level"], d["storage_date"], d["next_inspection_date"]))

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
