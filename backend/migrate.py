"""数据库迁移脚本：为已有数据库添加新列。

使用方法：
    cd backend
    python migrate.py

该脚本会检查 media 表的列，自动添加缺失的新列。
已存在的列不会被修改或删除。
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "asmr_manager.db")

# 需要确保存在的列定义：(表名, 列名, 列类型, 默认值)
COLUMNS_TO_ENSURE = [
    ("media", "cover_url", "TEXT", None),
    ("media", "description", "TEXT", None),
    ("media", "metadata_source", "VARCHAR(20)", None),
    ("scan_jobs", "organized_files", "INTEGER", "0"),
]


def get_existing_columns(cursor: sqlite3.Cursor, table: str) -> set[str]:
    """获取表的现有列名"""
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在: {DB_PATH}")
        print("首次启动时会自动创建表，无需迁移。")
        return

    print(f"连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    applied = 0
    skipped = 0

    for table, column, col_type, default in COLUMNS_TO_ENSURE:
        existing = get_existing_columns(cursor, table)
        if column in existing:
            skipped += 1
            continue

        # 添加新列
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
        if default is not None:
            sql += f" DEFAULT {default}"

        try:
            cursor.execute(sql)
            print(f"  ✓ {table}.{column} 已添加 ({col_type})")
            applied += 1
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"  - {table}.{column} 已存在，跳过")
                skipped += 1
            else:
                print(f"  ✗ {table}.{column} 添加失败: {e}")

    conn.commit()
    conn.close()

    print(f"\n迁移完成：添加 {applied} 列，跳过 {skipped} 列")


if __name__ == "__main__":
    migrate()
