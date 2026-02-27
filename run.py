# -*- coding: utf-8 -*-
"""
进销存 + CRM 入口
两个老板账号登录同一网站，均为最高权限。
"""
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from config import Config
import db
from auth import AdminUser, AdminUser as User

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "请先登录。"

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))


# ---------- 登录 / 登出 ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            flash("请输入账号和密码", "error")
            return render_template("login.html")
        user = AdminUser.check_password(username, password)
        if user:
            login_user(user)
            return redirect(request.args.get("next") or url_for("index"))
        flash("账号或密码错误", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------- 首页（仪表盘） ----------
@app.route("/")
@login_required
def index():
    return render_template("index.html")


# ---------- 入库 ----------
@app.route("/stock-in")
@login_required
def stock_in_list():
    rows = db.execute_all(
        "SELECT s.*, p.model, p.price FROM stock_in s JOIN product p ON s.product_id = p.id ORDER BY s.id DESC LIMIT 100"
    )
    products = db.execute_all("SELECT id, category, model, price, cost_price, quantity FROM product ORDER BY model")
    return render_template("stock_in.html", records=rows, products=products)


@app.route("/stock-in/add", methods=["POST"])
@login_required
def stock_in_add():
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)
    cost_price = request.form.get("cost_price", type=float)
    note = (request.form.get("note") or "").strip()
    if not product_id or quantity is None or quantity < 1:
        flash("请选择产品并填写数量", "error")
        return redirect(url_for("stock_in_list"))
    if cost_price is None:
        cost_price = 0
    db.execute_insert(
        "INSERT INTO stock_in (product_id, quantity, cost_price, note) VALUES (%s, %s, %s, %s)",
        (product_id, quantity, cost_price, note or None),
    )
    db.execute_update(
        "UPDATE product SET quantity = quantity + %s WHERE id = %s",
        (quantity, product_id),
    )
    flash("入库成功", "success")
    return redirect(url_for("stock_in_list"))


# ---------- 产品（型号）管理（入库前需有产品） ----------
@app.route("/products")
@login_required
def product_list():
    rows = db.execute_all("SELECT * FROM product ORDER BY model")
    return render_template("products.html", products=rows)


@app.route("/products/add", methods=["POST"])
@login_required
def product_add():
    category = (request.form.get("category") or "").strip()
    model = (request.form.get("model") or "").strip()
    price = request.form.get("price", type=float) or 0
    cost_price = request.form.get("cost_price", type=float) or 0
    if not model:
        flash("请填写型号", "error")
        return redirect(url_for("product_list"))
    try:
        db.execute_insert(
            "INSERT INTO product (category, model, price, cost_price, quantity) VALUES (%s, %s, %s, %s, 0)",
            (category or None, model, price, cost_price),
        )
        flash("产品添加成功", "success")
    except Exception as e:
        if "Duplicate" in str(e) or "uk_model" in str(e):
            flash("该型号已存在", "error")
        else:
            flash("添加失败", "error")
    return redirect(url_for("product_list"))

@app.route("/inventory")
@login_required
def inventory():
    q = (request.args.get("model") or "").strip()
    products = []
    if q:
        products = db.execute_all(
            "SELECT id, category, model, price, cost_price, quantity FROM product WHERE model LIKE %s ORDER BY model",
            (f"%{q}%",),
        )
    return render_template("inventory.html", q=q, products=products)


# ---------- 客户（CRM） ----------
@app.route("/customers")
@login_required
def customer_list():
    rows = db.execute_all("SELECT * FROM customer ORDER BY id DESC")
    return render_template("customers.html", customers=rows)


@app.route("/customers/add", methods=["POST"])
@login_required
def customer_add():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    address = (request.form.get("address") or "").strip()
    note = (request.form.get("note") or "").strip()
    if not name:
        flash("请填写客户名", "error")
        return redirect(url_for("customer_list"))
    db.execute_insert(
        "INSERT INTO customer (name, phone, address, note) VALUES (%s, %s, %s, %s)",
        (name, phone or None, address or None, note or None),
    )
    flash("客户添加成功", "success")
    return redirect(url_for("customer_list"))


# ---------- 出库/销售 ----------
@app.route("/sales")
@login_required
def sale_list():
    rows = db.execute_all(
        "SELECT o.*, c.name AS customer_name, c.phone, c.address FROM sale_order o "
        "JOIN customer c ON o.customer_id = c.id ORDER BY o.id DESC LIMIT 100"
    )
    products = db.execute_all("SELECT id, category, model, price, quantity FROM product WHERE quantity > 0 ORDER BY model")
    customers = db.execute_all("SELECT id, name, phone, address FROM customer ORDER BY name")
    return render_template("sales.html", orders=rows, products=products, customers=customers)


@app.route("/sales/add", methods=["POST"])
@login_required
def sale_add():
    from datetime import datetime
    customer_id = request.form.get("customer_id", type=int)
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)
    unit_price = request.form.get("unit_price", type=float)
    if not customer_id or not product_id or not quantity or quantity < 1:
        flash("请选择客户、产品并填写数量", "error")
        return redirect(url_for("sale_list"))
    if unit_price is None:
        unit_price = 0
    # 检查库存
    prod = db.execute_one("SELECT id, quantity FROM product WHERE id = %s", (product_id,))
    if not prod or prod["quantity"] < quantity:
        flash("库存不足", "error")
        return redirect(url_for("sale_list"))
    total = quantity * unit_price
    order_no = "SO" + datetime.now().strftime("%Y%m%d%H%M%S") + str(datetime.now().microsecond)[:3]
    order_id = db.execute_insert(
        "INSERT INTO sale_order (order_no, customer_id, total_amount) VALUES (%s, %s, %s)",
        (order_no, customer_id, total),
    )
    db.execute_insert(
        "INSERT INTO sale_order_item (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
        (order_id, product_id, quantity, unit_price),
    )
    db.execute_update("UPDATE product SET quantity = quantity - %s WHERE id = %s", (quantity, product_id))
    flash("出库成功，单号：" + order_no, "success")
    return redirect(url_for("sale_list"))


# ---------- 维修记录 ----------
@app.route("/maintenance")
@login_required
def maintenance_list():
    rows = db.execute_all(
        "SELECT m.*, c.name AS customer_name, p.model AS product_model FROM maintenance m "
        "JOIN customer c ON m.customer_id = c.id LEFT JOIN product p ON m.product_id = p.id ORDER BY m.id DESC"
    )
    customers = db.execute_all("SELECT id, name FROM customer ORDER BY name")
    products = db.execute_all("SELECT id, model FROM product ORDER BY model")
    return render_template("maintenance.html", records=rows, customers=customers, products=products)


@app.route("/maintenance/add", methods=["POST"])
@login_required
def maintenance_add():
    customer_id = request.form.get("customer_id", type=int)
    product_id = request.form.get("product_id", type=int) or None
    content = (request.form.get("content") or "").strip()
    result = (request.form.get("result") or "").strip()
    if not customer_id:
        flash("请选择客户", "error")
        return redirect(url_for("maintenance_list"))
    db.execute_insert(
        "INSERT INTO maintenance (customer_id, product_id, content, result) VALUES (%s, %s, %s, %s)",
        (customer_id, product_id, content or None, result or None),
    )
    flash("维修记录添加成功", "success")
    return redirect(url_for("maintenance_list"))


# ---------- 启动时确保有两个老板账号 ----------
@app.before_request
def ensure_db():
    try:
        AdminUser.ensure_default_admins()
    except Exception:
        pass  # 未建表时忽略


if __name__ == "__main__":
    ensure_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
