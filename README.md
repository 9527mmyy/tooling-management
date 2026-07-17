# 🛠️ 工装管理系统 / Tooling Management System

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/flask-3.0%2B-lightgrey" alt="Flask 3.0+"/>
  <img src="https://img.shields.io/badge/vue.js-3.0-brightgreen" alt="Vue.js 3"/>
  <img src="https://img.shields.io/badge/status-stable-success" alt="Status: Stable"/>
</p>

<p align="center">
  <b>中文</b> · 一款面向制造业的工装夹具管理系统，实现工装全生命周期管理——从入库台账、借用归还到定期鉴定、资料归档。
  <br>
  <b>English</b> · A tooling & fixture management system for manufacturing, covering the full lifecycle from inventory registration, borrowing/returning, to periodic inspection and documentation archiving.
</p>

---

## 📋 功能概览 / Features

| 中文 | English |
|------|---------|
| 🔐 **登录/权限** — 管理员与普通员工双角色，权限分离 | Login with role-based access control (admin / operator) |
| 📦 **工装台账** — 增删改查，支持图号、分类、等级管理 | Full CRUD for tooling records with drawing no., category & grade |
| 📎 **入库资料** — 新工装入库时上传图纸/说明书/合格证 | Attach drawings, manuals & certificates on tool registration |
| 🔍 **搜索筛选** — 按编号、名称、状态、分厂、班组多维度筛选 | Multi-dimensional search by code, name, status, plant & team |
| 📤 **Excel导入** — 下载模板→批量导入，编号重复自动跳过 | Batch import via Excel template with duplicate skip |
| 📋 **鉴定记录** — 定期鉴定 + 上传鉴定报告 | Periodic inspection tracking with report upload |
| 🔄 **借用/归还** — 工装借用流程 + 领用人跟踪 | Tool borrowing workflow with assignee tracking |
| 🏭 **组织架构** — 分厂→班组树形组织管理 | Plant → Team hierarchical organization tree |
| 📊 **统计看板** — ECharts 可视化展示工装状态分布 | ECharts dashboard for tool status visualization |
| 🗑️ **报废管理** — 报废申请 + 审核流程 | Scrap request with review workflow |

## 🖥️ 截图预览 / Screenshots

> *截图待补充——将截图放入 `docs/screenshots/` 后更新链接即可*
>
> *Screenshots coming soon — place them in `docs/screenshots/` and update the links.*

---

## 🚀 快速开始 / Quick Start

### 前置条件 / Prerequisites

- Python 3.9+（[下载 / Download](https://www.python.org/downloads/)）
- Windows 7+ / Linux / macOS

### 方式一：一键安装（Windows） / One-click Setup (Windows)

```bat
git clone https://github.com/your-username/tooling-management.git
cd tooling-management
双击 backend\setup.bat     # 自动安装依赖 + 初始化 / Auto install & init
双击 backend\start.bat      # 启动服务 / Start server
```

### 方式二：手动安装（跨平台） / Manual Setup (Cross-platform)

```bash
git clone https://github.com/your-username/tooling-management.git
cd tooling-management/backend
pip install -r requirements.txt
python app.py
```

### 访问系统 / Access

浏览器打开 / Open **http://localhost:5000**

### 默认账号 / Default Account

| 角色 / Role | 用户名 / Username | 密码 / Password |
|-------------|-------------------|-----------------|
| 管理员 / Admin | `admin` | `admin123` |

> ⚠️ **首次使用请立即修改默认密码！ / Change the default password immediately after first login!**

---

## 🧱 技术栈 / Tech Stack

| 层级 / Layer | 技术 / Technology | 说明 / Description |
|-------------|-------------------|-------------------|
| **后端框架 / Backend** | Python Flask 3.x | 轻量 Web 框架 / Lightweight web framework |
| **数据库 / Database** | SQLite (开发/Dev) / MySQL (生产/Prod) | 开发即用，生产可迁 / Dev-ready, production-migratable |
| **ORM** | Flask-SQLAlchemy | 数据库模型管理 / DB model management |
| **前端 / Frontend** | Vue.js 3 + Element Plus | CDN 引入，无需构建 / CDN-loaded, no build step |
| **可视化 / Charts** | ECharts 5 | 数据看板 / Dashboard |
| **认证 / Auth** | Flask Session | Session + 密码哈希 / Session + password hashing |
| **导入 / Import** | openpyxl | Excel 模板导入 / Excel template import |

---

## 📁 目录结构 / Directory Structure

```
tooling-management/
├── backend/                       # Flask 后端 / Flask backend
│   ├── app.py                    # 应用主入口 / Application entry
│   ├── models.py                 # 数据库模型(6表) / DB models (6 tables)
│   ├── requirements.txt          # Python 依赖 / Python dependencies
│   ├── setup.bat                 # 一键安装脚本(Windows) / One-click installer
│   ├── start.bat                 # 一键启动脚本 / One-click starter
│   ├── backup_db.py              # 数据库自动备份 / DB backup utility
│   ├── routes/                   # API 路由 / API routes
│   │   ├── auth.py               # 登录/用户 / Login & users
│   │   ├── tools.py              # 工装CRUD / Tooling CRUD
│   │   ├── borrows.py            # 借用/归还 / Borrowing & returns
│   │   ├── inspections.py        # 鉴定记录 / Inspections
│   │   ├── attachments.py        # 文件上传/下载 / File uploads
│   │   ├── import_tools.py       # Excel 导入 / Excel import
│   │   ├── export.py             # 数据导出 / Data export
│   │   ├── org.py                # 组织架构 / Organization tree
│   │   ├── scraps.py             # 报废管理 / Scrap management
│   │   └── configs.py            # 系统配置 / System config
│   ├── static/                   # 前端静态资源 / Static assets
│   │   └── libs/                 # CDN库(Vue/Element/ECharts/axios)
│   ├── templates/                # HTML 模板 / HTML templates
│   │   └── index.html            # 主页面(Vue SPA) / Main page
│   └── uploads/                  # 上传文件 / Uploaded files
├── frontend/                     # Vue 源码(开发中) / Vue source (WIP)
├── LICENSE                       # MIT 许可证 / MIT License
└── README.md                     # 本文件 / This file
```

---

## 🗄️ 数据库模型 / Database Models

| 表 / Table | 说明 / Description | 核心字段 / Key Fields |
|------------|-------------------|---------------------|
| `users` | 用户表 / Users | 用户名、角色、密码哈希 / username, role, password_hash |
| `tools` | 工装主表 / Tools | 编号、图号、名称、分类、等级、状态、分厂、班组 / code, drawing_no, name, category, grade, status, plant, team |
| `borrow_records` | 借用记录 / Borrowings | 工装、借用人、时间、归还状态 / tool, borrower, date, returned |
| `inspections` | 鉴定记录 / Inspections | 工装、鉴定日期、报告附件、结果 / tool, date, report, result |
| `attachments` | 附件表 / Attachments | 工装关联的图纸/说明书 / tool drawings, manuals |
| `operation_logs` | 操作日志 / Audit log | 用户操作审计 / user operation audit |

---

## 📦 生产部署建议 / Production Deployment

| 建议 / Suggestion | 说明 / Details |
|-------------------|----------------|
| **数据库 / Database** | 迁移至 MySQL/MariaDB，修改 `app.py` 中 SQLAlchemy 连接串 / Switch to MySQL by updating the SQLAlchemy connection string |
| **WSGI 服务器 / WSGI Server** | 使用 Gunicorn (Linux) 或 Waitress (Windows) 替代 dev server |
| **反向代理 / Reverse Proxy** | Nginx 代理静态文件 + 转发 API / Nginx for static files + API proxy |
| **开机自启 / Auto-start** | Linux 用 systemd，Windows 用任务计划或 NSSM 注册为服务 / systemd (Linux) or Task Scheduler / NSSM (Windows) |
| **数据备份 / Backup** | 内置 `backup_db.py`，配合 cron / 任务计划自动备份每日快照 / Use `backup_db.py` with cron / Task Scheduler for daily snapshots |

---

## 👤 作者 / Author

**Name**: moy  
**Email**: 891761065@qq.com

---

## 🤝 贡献 / Contributing

**中文**：欢迎提交 Issue 和 Pull Request！

**English**: Issues and Pull Requests are welcome!

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add something'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 许可证 / License

**中文**：本项目采用 [MIT License](LICENSE)，可以自由使用、修改和分发。

**English**: This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute.
