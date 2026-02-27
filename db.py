# -*- coding: utf-8 -*-
"""MySQL 连接与简单封装（纯 Python，用 PyMySQL）"""
import pymysql
from contextlib import contextmanager
from config import Config

def get_connection():
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

@contextmanager
def get_cursor(commit=True):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()

def execute_one(sql, args=None):
    with get_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchone()

def execute_all(sql, args=None):
    with get_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchall()

def execute_insert(sql, args=None):
    with get_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.lastrowid

def execute_update(sql, args=None):
    with get_cursor() as cur:
        return cur.execute(sql, args or ())
