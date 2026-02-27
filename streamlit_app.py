import time

import pandas as pd
import streamlit as st

import db
from auth import AdminUser


def require_login():
    if "user" not in st.session_state:
        st.switch_page("streamlit_app.py")


def page_login():
    st.title("CRM")
    st.subheader("登录")

    username = st.text_input("账号", placeholder="boss1 / boss2 / lingtong")
    password = st.text_input("密码", type="password", placeholder="默认123456")
    if st.button("登录", type="primary"):
        user = AdminUser.check_password(username, password)
        if user:
            st.session_state["user"] = {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
            }
            st.success("登录成功")
            time.sleep(0.3)
            st.rerun()
        else:
            st.error("账号或密码错误")


def sidebar_user():
    user = st.session_state.get("user")
    if not user:
        return
    with st.sidebar:
        st.markdown(
            f"**当前用户：** {user['display_name'] or user['username']}  \n"
        )
        if st.button("退出登录"):
            st.session_state.clear()
            st.rerun()


def page_dashboard():
    st.title("概览")
    st.write("流程：添加产品，入库产品，库存查询，客户管理，出库产品，维修记录。")

    col1, col2, col3 = st.columns(3)
    with col1:
        p_count = db.execute_one("SELECT COUNT(*) AS n FROM product")["n"]
        st.metric("产品型号数", p_count)
    with col2:
        c_count = db.execute_one("SELECT COUNT(*) AS n FROM customer")["n"]
        st.metric("客户数", c_count)
    with col3:
        s_count = db.execute_one("SELECT COUNT(*) AS n FROM sale_order")["n"]
        st.metric("销售单数", s_count)


def page_products():
    st.title("产品&型号")

    with st.expander("添加产品", expanded=True):
        with st.form("add_product"):
            category = st.text_input("洗衣机, 烘干机")
            model = st.text_input("型号", help="必填")
            col1, col2 = st.columns(2)
            with col1:
                price = st.number_input("售价", min_value=0.0, value=0.0, step=0.01)
            with col2:
                cost_price = st.number_input("进价", min_value=0.0, value=0.0, step=0.01)
            submitted = st.form_submit_button("保存")
        if submitted:
            if not model.strip():
                st.error("型号不能为空")
            else:
                try:
                    db.execute_insert(
                        "INSERT INTO product (category, model, price, cost_price, quantity) "
                        "VALUES (%s, %s, %s, %s, 0)",
                        (category or None, model.strip(), price, cost_price),
                    )
                    st.success("产品已添加")
                except Exception as e:
                    if "Duplicate" in str(e) or "uk_model" in str(e):
                        st.error("该型号已存在")
                    else:
                        st.error(f"添加失败：{e}")

    rows = db.execute_all(
        "SELECT id, category, model, price, cost_price, quantity "
        "FROM product ORDER BY category, model"
    )
    st.write("当前产品：")
    if rows:
        df = pd.DataFrame(rows)
        df = df.rename(
            columns={
                "id": "ID",
                "category": "品类",
                "model": "型号",
                "price": "售价",
                "cost_price": "进价",
                "quantity": "库存数量",
            }
        )
        st.dataframe(df, use_container_width=True)


def page_stock_in():
    st.title("入库")

    products = db.execute_all(
        "SELECT id, category, model, price, cost_price, quantity "
        "FROM product ORDER BY category, model"
    )
    if not products:
        st.info("暂无产品，请先在“产品&型号”中添加。")
        return

    with st.form("stock_in_form"):
        product_options = {
            f"{(p['category'] + ' - ') if p['category'] else ''}{p['model']}（库存 {p['quantity']}）": p[
                "id"
            ]
            for p in products
        }
        product_label = st.selectbox("产品", list(product_options.keys()))
        quantity = st.number_input("数量", min_value=1, value=1, step=1)
        cost_price = st.number_input("进价", min_value=0.0, value=0.0, step=0.01)
        note = st.text_input("备注（可选）")
        submitted = st.form_submit_button("入库")

    if submitted:
        product_id = product_options[product_label]
        db.execute_insert(
            "INSERT INTO stock_in (product_id, quantity, cost_price, note) VALUES (%s, %s, %s, %s)",
            (product_id, quantity, cost_price, note or None),
        )
        db.execute_update(
            "UPDATE product SET quantity = quantity + %s WHERE id = %s",
            (quantity, product_id),
        )
        st.success("入库成功")

    records = db.execute_all(
        "SELECT s.created_at, p.category, p.model, s.quantity, s.cost_price, s.note "
        "FROM stock_in s JOIN product p ON s.product_id = p.id "
        "ORDER BY s.id DESC LIMIT 100"
    )
    st.write("最近入库记录：")
    if records:
        df = pd.DataFrame(records)
        df = df.rename(
            columns={
                "created_at": "时间",
                "category": "品类",
                "model": "型号",
                "quantity": "数量",
                "cost_price": "进价",
                "note": "备注",
            }
        )
        st.dataframe(df, use_container_width=True)


def page_customers():
    st.title("客户")

    with st.form("add_customer"):
        name = st.text_input("客户名")
        phone = st.text_input("电话", value="")
        address = st.text_input("地址", value="")
        note = st.text_input("备注", value="")
        submitted = st.form_submit_button("添加客户")
    if submitted:
        if not name.strip():
            st.error("客户名不能为空")
        else:
            db.execute_insert(
                "INSERT INTO customer (name, phone, address, note) VALUES (%s, %s, %s, %s)",
                (name.strip(), phone or None, address or None, note or None),
            )
            st.success("客户已添加")

    rows = db.execute_all(
        "SELECT id, name, phone, address, note, created_at FROM customer ORDER BY id DESC"
    )
    if rows:
        df = pd.DataFrame(rows)
        df = df.rename(
            columns={
                "id": "ID",
                "name": "客户名",
                "phone": "电话",
                "address": "地址",
                "note": "备注",
                "created_at": "创建时间",
            }
        )
        st.dataframe(df, use_container_width=True)


def page_sales():
    st.title("出库")

    products = db.execute_all(
        "SELECT id, category, model, price, quantity FROM product WHERE quantity > 0 "
        "ORDER BY category, model"
    )
    customers = db.execute_all(
        "SELECT id, name, phone, address FROM customer ORDER BY name"
    )

    if not products:
        st.info("暂无可出库的产品，请先入库。")
        return
    if not customers:
        st.info("暂无客户，请先添加客户。")
        return

    product_options = {
        f"{(p['category'] + ' - ') if p['category'] else ''}{p['model']}（库存 {p['quantity']}）": p[
            "id"
        ]
        for p in products
    }
    customer_options = {f"{c['name']} {c['phone'] or ''}": c["id"] for c in customers}

    with st.form("sale_form"):
        customer_label = st.selectbox("客户", list(customer_options.keys()))
        product_label = st.selectbox("产品", list(product_options.keys()))
        quantity = st.number_input("数量", min_value=1, value=1, step=1)
        # 默认单价用产品售价
        default_price = 0.0
        selected_id = product_options[product_label]
        for p in products:
            if p["id"] == selected_id:
                default_price = float(p["price"] or 0)
                break
        unit_price = st.number_input(
            "单价", min_value=0.0, value=default_price, step=0.01
        )
        submitted = st.form_submit_button("出库")

    if submitted:
        from datetime import datetime

        customer_id = customer_options[customer_label]
        product_id = product_options[product_label]
        prod = db.execute_one(
            "SELECT id, quantity FROM product WHERE id = %s", (product_id,)
        )
        if not prod or prod["quantity"] < quantity:
            st.error("库存不足")
        else:
            total = quantity * unit_price
            order_no = (
                "SO"
                + datetime.now().strftime("%Y%m%d%H%M%S")
                + str(datetime.now().microsecond)[:3]
            )
            order_id = db.execute_insert(
                "INSERT INTO sale_order (order_no, customer_id, total_amount) "
                "VALUES (%s, %s, %s)",
                (order_no, customer_id, total),
            )
            db.execute_insert(
                "INSERT INTO sale_order_item ("
                "order_id, product_id, quantity, unit_price"
                ") VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, unit_price),
            )
            db.execute_update(
                "UPDATE product SET quantity = quantity - %s WHERE id = %s",
                (quantity, product_id),
            )
            st.success(f"出库成功，单号：{order_no}")

    rows = db.execute_all(
        "SELECT "
        "  o.order_no, o.total_amount, o.created_at, "
        "  c.name AS customer_name, c.phone, "
        "  GROUP_CONCAT("
        "    CONCAT("
        "      CASE WHEN p.category IS NULL OR p.category = '' "
        "           THEN '' ELSE CONCAT(p.category, ' - ') END,"
        "      p.model, ' x', i.quantity"
        "    ) SEPARATOR '；'"
        "  ) AS items_summary "
        "FROM sale_order o "
        "JOIN customer c ON o.customer_id = c.id "
        "LEFT JOIN sale_order_item i ON i.order_id = o.id "
        "LEFT JOIN product p ON p.id = i.product_id "
        "GROUP BY o.id "
        "ORDER BY o.id DESC "
        "LIMIT 100"
    )
    st.write("最近销售单：")
    if rows:
        df = pd.DataFrame(rows)
        df = df.rename(
            columns={
                "order_no": "单号",
                "total_amount": "金额",
                "created_at": "时间",
                "customer_name": "客户",
                "phone": "电话",
                "items_summary": "商品明细",
            }
        )
        st.dataframe(df, use_container_width=True)


def page_inventory():
    st.title("库存查询")

    model_q = st.text_input("按型号搜索", placeholder="输入型号")
    if st.button("查询") or model_q:
        rows = db.execute_all(
            "SELECT category, model, price, cost_price, quantity "
            "FROM product WHERE model LIKE %s "
            "ORDER BY category, model",
            (f"%{model_q}%",),
        )
        if rows:
            df = pd.DataFrame(rows)
            df = df.rename(
                columns={
                    "category": "品类",
                    "model": "型号",
                    "price": "售价",
                    "cost_price": "进价",
                    "quantity": "库存数量",
                }
            )
            st.dataframe(df, use_container_width=True)


def page_maintenance():
    st.title("维修记录")

    customers = db.execute_all("SELECT id, name FROM customer ORDER BY name")
    products = db.execute_all("SELECT id, category, model FROM product ORDER BY category, model")

    if not customers:
        st.info("暂无客户，请先添加客户。")
        return

    customer_options = {c["name"]: c["id"] for c in customers}
    product_options = {
        f"{(p['category'] + ' - ') if p['category'] else ''}{p['model']}": p["id"]
        for p in products
    }

    with st.form("maint_form"):
        customer_label = st.selectbox("客户", list(customer_options.keys()))
        product_label = st.selectbox(
            "产品（可选）", ["—"] + list(product_options.keys())
        )
        content = st.text_input("维修内容")
        result = st.text_input("处理结果")
        submitted = st.form_submit_button("添加记录")

    if submitted:
        customer_id = customer_options[customer_label]
        product_id = None
        if product_label != "—":
            product_id = product_options[product_label]
        db.execute_insert(
            "INSERT INTO maintenance (customer_id, product_id, content, result) "
            "VALUES (%s, %s, %s, %s)",
            (customer_id, product_id, content or None, result or None),
        )
        st.success("维修记录已添加")

    rows = db.execute_all(
        "SELECT m.created_at, c.name AS customer_name, "
        "       p.model AS product_model, m.content, m.result "
        "FROM maintenance m "
        "JOIN customer c ON m.customer_id = c.id "
        "LEFT JOIN product p ON m.product_id = p.id "
        "ORDER BY m.id DESC"
    )
    if rows:
        df = pd.DataFrame(rows)
        df = df.rename(
            columns={
                "created_at": "登记时间",
                "customer_name": "客户",
                "product_model": "产品型号",
                "content": "维修内容",
                "result": "处理结果",
            }
        )
        st.dataframe(df, use_container_width=True)


def main():
    st.set_page_config(page_title="进销存 CRM", layout="wide")

    if "user" not in st.session_state:
        page_login()
        return

    sidebar_user()

    pages = {
        "首页": page_dashboard,
        "产品&型号": page_products,
        "入库": page_stock_in,
        "客户": page_customers,
        "出库": page_sales,
        "库存查询": page_inventory,
        "维修记录": page_maintenance,
    }
    choice = st.sidebar.radio("功能菜单", list(pages.keys()))
    pages[choice]()


if __name__ == "__main__":
    main()

# py -m streamlit run streamlit_app.py