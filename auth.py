# -*- coding: utf-8 -*-
"""登录与权限：两个老板账号，均为最高权限"""
from werkzeug.security import check_password_hash, generate_password_hash
import db

class AdminUser:
    def __init__(self, id, username, display_name):
        self.id = id
        self.username = username
        self.display_name = display_name or username

    # 兼容 Flask-Login 所需的几个属性/方法（Streamlit 也能直接复用这个类）
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get(user_id):
        row = db.execute_one(
            "SELECT id, username, display_name FROM admin_user WHERE id = %s",
            (user_id,),
        )
        if not row:
            return None
        return AdminUser(row["id"], row["username"], row["display_name"])

    @staticmethod
    def get_by_username(username):
        row = db.execute_one(
            "SELECT id, username, display_name FROM admin_user WHERE username = %s",
            (username,),
        )
        if not row:
            return None
        return AdminUser(row["id"], row["username"], row["display_name"])

    @staticmethod
    def check_password(username, password):
        row = db.execute_one(
            "SELECT id, username, password_hash, display_name FROM admin_user WHERE username = %s",
            (username,),
        )
        if not row or not check_password_hash(row["password_hash"], password):
            return None
        return AdminUser(row["id"], row["username"], row["display_name"])

    @staticmethod
    def ensure_default_admins():
        """确保默认管理员存在（已存在则跳过；不存在则创建）。"""
        defaults = [
            ("boss1", "123456", "boss1"),
            ("boss2", "123456", "boss2"),
            ("lingtong", "gbhnjmkI23", "Lingtong"),
        ]
        for username, raw_password, display_name in defaults:
            exists = db.execute_one(
                "SELECT id FROM admin_user WHERE username = %s",
                (username,),
            )
            if exists:
                continue
            password_hash = generate_password_hash(raw_password, method="pbkdf2:sha256")
            db.execute_insert(
                "INSERT INTO admin_user (username, password_hash, display_name) VALUES (%s, %s, %s)",
                (username, password_hash, display_name),
            )
