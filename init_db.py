# -*- coding: utf-8 -*-
"""
一键执行 schema.sql 建表（在 Cursor 里没有“执行 SQL”时用这个）。
在项目根目录运行：python init_db.py
"""
import pymysql
from pathlib import Path

from config import Config

def _split_sql(sql: str):
    stmts = []
    buf = []
    in_single = False
    in_double = False
    in_backtick = False
    escape = False
    for ch in sql:
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\":
            buf.append(ch)
            escape = True
            continue
        if ch == "'" and not in_double and not in_backtick:
            in_single = not in_single
            buf.append(ch)
            continue
        if ch == '"' and not in_single and not in_backtick:
            in_double = not in_double
            buf.append(ch)
            continue
        if ch == "`" and not in_single and not in_double:
            in_backtick = not in_backtick
            buf.append(ch)
            continue
        if ch == ";" and not in_single and not in_double and not in_backtick:
            stmt = "".join(buf).strip()
            buf = []
            if stmt:
                stmts.append(stmt)
            continue
        buf.append(ch)
    last = "".join(buf).strip()
    if last:
        stmts.append(last)
    return stmts

def main():
    base = Path(__file__).resolve().parent
    schema_file = base / "sql" / "schema.sql"
    if not schema_file.exists():
        print("找不到 sql/schema.sql")
        return

    # 1. 先建库（连接时不指定 database）
    conn_no_db = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn_no_db.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS mycrm DEFAULT CHARACTER SET utf8mb4")
        conn_no_db.commit()
        print("数据库 mycrm 已就绪")
    finally:
        conn_no_db.close()

    # 2. 连接 mycrm 并执行 schema.sql
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
    )
    sql = schema_file.read_text(encoding="utf-8")
    try:
        with conn.cursor() as cur:
            for stmt in _split_sql(sql):
                s = stmt.strip()
                if not s:
                    continue
                # 忽略 MySQL CLI 专用指令
                if s.lower().startswith("delimiter "):
                    continue
                cur.execute(s)
            # 兼容已创建旧表：补充品类字段
            try:
                cur.execute(
                    "ALTER TABLE product "
                    "ADD COLUMN category VARCHAR(64) DEFAULT NULL COMMENT '品类/大类（如 洗衣机、烘干机）' "
                    "AFTER id"
                )
            except Exception:
                pass
        conn.commit()
        print("schema.sql 执行成功，表已创建。")
    except Exception as e:
        print("执行出错:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
