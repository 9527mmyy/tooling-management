# 🛠️ 工装管理系统

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/flask-3.0%2B-lightgrey" alt="Flask 3.0+"/>
  <img src="https://img.shields.io/badge/vue.js-3.0-brightgreen" alt="Vue.js 3"/>
  <img src="https://img.shields.io/badge/status-stable-success" alt="Status: Stable"/>
</p>

一款面向制造业的工装夹具管理系统，实现工装全生命周期管理——从入库台账、借用归还到定期鉴定、资料归档。

## 📋 功能概览

| 功能 | 说明 |
|------|------|
| 🔐 **登录/权限** | 管理员与普通员工双角色，权限分离 |
| 📦 **工装台账** | 工装增删改查，支持图号、分类、等级管理 |
| 📎 **入库资料** | 新工装入库时上传图纸/说明书/合格证 |
| 🔍 **搜索筛选** | 按编号、名称、状态、分厂、班组多维度筛选 |
| 📤 **Excel导入** | 下载模板 → 批量导入工装，编号重复自动跳过 |
| 📋 **鉴定记录** | 定期鉴定 + 上传鉴定报告，保证合规性 |
| 🔄 **借用/归还** | 工装借用流程 + 领用人跟踪 |
| 🏭 **组织架构** | 分厂 → 班组树形组织管理 |
| 📊 **统计看板** | ECharts 可视化展示工装状态分布 |
| 🗑️ **报废管理** | 报废申请+审核流程 |

## 🖥️ 截图预览

> *截图待补充——将截图放入 `docs/screenshots/` 后更新链接即可*

## 🚀 快速开始

### 前置条件

- Python 3.9+（[下载](https://www.python.org/downloads/)）
- Windows 7+/Linux/macOS

### 方式一：一键安装（Windows）

```bat
git clone https://github.com/your-username/tooling-management.git
cd tooling-management
双击 backend\setup.bat    # 自动安装依赖 + 初始化
双击 backend\start.bat     # 启动服务
```

### 方式二：手动安装（跨平台）

```bash
git clone https://github.com/your-username/tooling-management.git
cd tooling-management/backend
pip install -r requirements.txt
python app.py
```

### 访问系统

浏览器打开 **http://localhost:5000**

### 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |

> ⚠️ **首次使用请立即修改默认密码！**

## 🧱 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | Python Flask 3.x | 轻量 Web 框架 |
| **数据库** | SQLite (开发) / MySQL (生产) | 开发即用，生产可迁 |
| **ORM** | Flask-SQLAlchemy | 数据库模型管理 |
| **前端** | Vue.js 3 + Element Plus | CDN 引入，无需构建 |
| **可视化** | ECharts 5 | 数据看板图表 |
| **认证** | Flask Session | Session + 密码哈希 |
| **导入** | openpyxl | Excel 模板导入 |

## 📁 目录结构

```
tooling-management/
├── backend/                  # Flask 后端
│   ├── app.py               # 应用主入口
│   ├── models.py            # 数据库模型（6张表）
│   ├── requirements.txt     # Python 依赖
│   ├── setup.bat            # 一键安装脚本（Windows）
│   ├── start.bat            # 一键启动脚本
│   ├── backup_db.py         # 数据库自动备份工具
│   ├── routes/              # API 路由
│   │   ├── auth.py          # 登录/用户管理
│   │   ├── tools.py         # 工装 CRUD
│   │   ├── borrows.py       # 借用/归还
│   │   ├── inspections.py   # 鉴定记录
│   │   ├── attachments.py   # 文件上传/下载
│   │   ├── import_tools.py  # Excel 导入
│   │   ├── export.py        # 数据导出
│   │   ├── org.py           # 组织架构
│   │   ├── scraps.py        # 报废管理
│   │   └── configs.py       # 系统配置
│   ├── static/              # 前端静态资源
│   │   └── libs/            # CDN 库（Vue/Element/axios/ECharts）
│   ├── templates/           # HTML 模板
│   │   └── index.html       # 主页面（Vue SPA）
│   └── uploads/             # 上传文件存储
├── frontend/                # Vue 源码（开发中）
├── LICENSE                  # MIT 许可证
└── README.md                # 本文件
```

## 🗄️ 数据库模型

| 表 | 说明 | 核心字段 |
|----|------|---------|
| `users` | 用户表 | 用户名、角色、密码哈希 |
| `tools` | 工装主表 | 编号、图号、名称、分类、等级、状态、分厂、班组 |
| `borrow_records` | 借用记录 | 工装、借用人、时间、归还状态 |
| `inspections` | 鉴定记录 | 工装、鉴定日期、报告附件、结果 |
| `attachments` | 附件表 | 工装关联的图纸/说明书/合格证 |
| `operation_logs` | 操作日志 | 用户操作审计记录 |

## 📦 生产部署建议

- **数据库**：迁移至 MySQL/MariaDB，修改 `app.py` 中 SQLAlchemy 连接串即可
- **WSGI 服务器**：使用 Gunicorn（Linux）或 Waitress（Windows）替代 flask dev server
- **反向代理**：Nginx 代理静态文件 + 转发 API 请求
- **开机自启**：Linux 用 systemd，Windows 用任务计划或 NSSM 注册为服务
- **数据备份**：内置 `backup_db.py`，配合 cron/任务计划每日自动备份

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交改动：`git commit -m 'feat: add something'`
4. 推送：`git push origin feature/your-feature`
5. 发起 Pull Request

## 📄 许可证

本项目采用 [MIT License](LICENSE)，可以自由使用、修改和分发。
