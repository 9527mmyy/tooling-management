"""
工装管理系统 - 数据库自动备份脚本
每天执行一次，用 SQLite .backup API 生成一致性快照，保留最近 N 天
"""
import sqlite3
import os
import sys
import shutil
import datetime
import glob

# === 配置 =============================================
DB_PATH = os.path.join(os.path.dirname(__file__), "tooling.db")
BACKUP_DIR = r"D:\tooling-backup"
RETENTION_DAYS = 30
LOG_FILE = os.path.join(os.path.dirname(__file__), "backup_db.log")
# ======================================================

os.makedirs(BACKUP_DIR, exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def backup():
    if not os.path.exists(DB_PATH):
        log(f"[ERROR] 源数据库不存在: {DB_PATH}")
        return False

    db_size_kb = os.path.getsize(DB_PATH) // 1024
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    bak_path = os.path.join(BACKUP_DIR, f"tooling_{timestamp}.db")

    try:
        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(bak_path)
        src.backup(dst, pages=-1, progress=None)
        dst.close()
        src.close()

        bak_size_kb = os.path.getsize(bak_path) // 1024
        log(f"[OK] 备份完成: {os.path.basename(bak_path)} "
            f"(源 {db_size_kb} KB -> 备份 {bak_size_kb} KB)")
        return True
    except Exception as e:
        log(f"[ERROR] 备份失败: {e}")
        return False

def cleanup():
    """删除超过 RETENTION_DAYS 天的旧备份"""
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=RETENTION_DAYS)
    removed = 0

    for f in glob.glob(os.path.join(BACKUP_DIR, "tooling_*.db")):
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        if mtime < cutoff:
            os.remove(f)
            removed += 1
            log(f"[CLEAN] 删除旧备份: {os.path.basename(f)} (修改时间 {mtime.strftime('%Y-%m-%d')})")

    if removed == 0:
        log(f"[INFO] 无超过 {RETENTION_DAYS} 天的旧备份需要清理")
    else:
        log(f"[CLEAN] 共清理 {removed} 个旧备份")

    # 统计当前备份数量与总大小
    all_baks = glob.glob(os.path.join(BACKUP_DIR, "tooling_*.db"))
    total_size = sum(os.path.getsize(f) for f in all_baks) // 1024
    log(f"[INFO] 当前备份: {len(all_baks)} 个, 总计 {total_size} KB")

if __name__ == "__main__":
    log("=== 开始数据库备份 ===")
    ok = backup()
    cleanup()
    log("=== 备份结束 ===\n")
    sys.exit(0 if ok else 1)
