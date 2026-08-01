"""
补录缺失的「建档记录」(in_storage_records)。

背景
----
详情页「记录」时间线里的「建档」节点来自 tools.in_storage_records（入库记录）。
经核查：446 个工装中仅 2 个有 in_storage_records，其余 444 个缺失，导致详情页看不到建档记录。

策略
----
对【没有】in_storage_records 的工装，补建一条建档记录：
  - storage_date（入库日期）: 优先用 tools.storage_date；为空则用 tools.created_at 的日期；再为空用今天。
  - operator（操作人）      : 真实建档人信息缺失，统一标记为「系统补录」（便于后续识别哪些是补的）。
  - storage_location（存放位置）: 工装表无该字段，留空（时间线显示 -）。
  - remark（备注）          : 「历史建档记录补录」。
  - supplier/batch_no/quantity: 留空/默认 1。

幂等性
------
仅给「当前没有」in_storage_records 的工装补建；已存在的 2 条真实记录不动。
重复运行不会产生重复记录。

用法
----
  python devtools/backfill_filing_records.py            # 实际执行
  python devtools/backfill_filing_records.py --dry-run  # 只统计不写入
"""
import argparse
import os
import sys
from datetime import datetime, date

# 让脚本能 import 到同级 backend 下的 app / models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Tool, InStorageRecord


def pick_storage_date(tool: Tool) -> date:
    if tool.storage_date:
        return tool.storage_date
    if tool.created_at:
        return tool.created_at.date()
    return date.today()


def main():
    parser = argparse.ArgumentParser(description="补录缺失的建档记录")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写入")
    args = parser.parse_args()

    with app.app_context():
        tools = Tool.query.all()
        missing = [t for t in tools if not t.in_storage_records]
        print(f"工装总数: {len(tools)}")
        print(f"已有建档记录: {len(tools) - len(missing)}")
        print(f"缺失需补录: {len(missing)}")

        if args.dry_run:
            print("[DRY-RUN] 未做任何修改。")
            return

        created = 0
        for t in missing:
            sd = pick_storage_date(t)
            rec = InStorageRecord(
                tool_id=t.id,
                storage_date=sd,
                supplier="",
                batch_no="",
                quantity=1,
                storage_location="",
                operator="系统补录",
                remark="历史建档记录补录",
            )
            db.session.add(rec)
            created += 1
            # 分批 flush，降低单次事务体积
            if created % 100 == 0:
                db.session.flush()

        db.session.commit()
        print(f"已补录建档记录: {created} 条")
        # 复检
        remaining = Tool.query.filter(
            ~Tool.id.in_(
                db.session.query(InStorageRecord.tool_id).distinct()
            )
        ).count()
        print(f"补录后仍未建档的工装: {remaining}")


if __name__ == "__main__":
    main()
