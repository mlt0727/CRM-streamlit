# 进销存 + CRM 系统（Streamlit + MySQL）

根据你的流程图实现：入库 → 卖出/出库 → 客户信息 → 发票/送货单，以及 CRM、维修记录。

## 一、一步步该怎么做（总览）

| 步骤 | 内容 | 说明 |
|------|------|------|
| 1 | 安装环境 | Python 3.8+、MySQL 8.0、依赖包 |
| 2 | 创建数据库与表 | 执行 `sql/schema.sql` 建库建表 |
| 3 | 配置与运行 | 配置环境变量，运行 Streamlit |
| 4 | 登录与权限 | 两个老板账号，均为最高权限，通过登录页进入 |
| 5 | 功能开发顺序 | 入库 → 客户 → 出库/卖出 → 发票与送货单 → 维修记录 |

## 二、技术选型

- **应用框架**：Streamlit（纯 Python）
- **数据库**：MySQL
- **账号**：2 个老板账号，同权（最高权限）

## 三、功能模块（对应流程图）

1. **入库**：记录 价钱、型号、数量、进价
2. **出库/卖出**：关联客户（客户名、电话、地址），扣减库存
3. **出库产出**：出发票、出送货单（可打印/导出）
4. **CRM**：客户管理、进销存汇总
5. **维修记录**：可选，与客户/产品关联

## 四、快速开始

```bash
# 1) 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate        # Windows

# 2) 安装依赖
pip install -r requirements.txt

# 3) 初始化数据库（在 MySQL 客户端中执行）
mysql -u root -p < sql/schema.sql

# 4) 配置环境变量（示例）
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=你的密码
export DB_NAME=mycrm

# 5) 运行 Streamlit
streamlit run streamlit_app.py
# 浏览器访问 http://127.0.0.1:8501
```

## 五、默认账号（两老板，最高权限）

首次运行且数据库已建表后，程序会自动创建两个管理员账号：

| 账号   | 密码   | 说明   |
|--------|--------|--------|
| boss1  | 123456 | 老板一 |
| boss2  | 123456 | 老板二 |

上线后请修改默认密码并妥善保管。

## 六、把数据库放到云上（推荐方案）

目标：让任何电脑都能连接同一套数据。

### 方案 A（推荐）：使用云托管 MySQL

可选服务：Aiven、Railway、PlanetScale（MySQL 兼容）、阿里云 RDS、腾讯云 MySQL、AWS RDS。

步骤：

1. 在云平台创建 MySQL 实例。
2. 在云平台白名单中放行你的应用出口 IP（或临时 0.0.0.0/0 + 强密码，仅短期调试）。
3. 拿到连接信息：`host`、`port`、`user`、`password`、`database`。
4. 用本地 MySQL 客户端导入结构（和数据）：

```bash
# 导出本地数据库
mysqldump -u root -p mycrm > mycrm.sql

# 导入到云数据库
mysql -h <cloud-host> -P <cloud-port> -u <cloud-user> -p <cloud-db> < mycrm.sql
```

5. 在运行 Streamlit 的环境中更新环境变量：

```bash
export DB_HOST=<cloud-host>
export DB_PORT=<cloud-port>
export DB_USER=<cloud-user>
export DB_PASSWORD=<cloud-password>
export DB_NAME=<cloud-db>
```

6. 重新启动应用：`streamlit run streamlit_app.py`。

### 方案 B：自建云服务器 MySQL（不太推荐新手）

你需要自己做：防火墙、MySQL 安全加固、自动备份、监控和故障恢复。除非你熟悉运维，否则优先选择托管 MySQL。

## 七、部署注意事项（很重要）

1. **不要把数据库密码写死在代码里**，使用环境变量。
2. 云数据库务必开启 **自动备份**（至少每天一次）。
3. 生产环境不要使用 root，创建最小权限业务账号。
4. 为数据库连接开启 SSL（云平台通常支持）。
5. 若你把 Streamlit 部署到云（如 Streamlit Community Cloud / Render / Railway），同样使用该平台的 Secrets 或 Environment Variables 注入 DB 配置。

---

后续可按「入库 → 客户 → 出库 → 单据 → 维修」顺序逐步实现和测试。
