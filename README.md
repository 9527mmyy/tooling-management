# 工装管理系统

## 项目简介

川润液压工装管理系统，用于管理工装夹具的台账、借用归还、定期鉴定和资料上传。

## 技术栈

- **后端**: Python Flask + SQLite
- **前端**: Vue.js 3 + Element Plus
- **部署**: 本地开发 → 腾讯云（MySQL）

## 快速开始

### 1. 首次安装

双击 `backend\setup.bat`，自动安装依赖和初始化数据库。

### 2. 启动系统

双击 `backend\start.bat`，浏览器访问 http://localhost:5000

### 3. 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

## 功能模块

| 模块 | 说明 |
|------|------|
| 登录/登出 | 账号密码认证 |
| 工装台账 | 增删改查工装信息 |
| 入库资料上传 | 新工装入库时上传图纸/说明书/合格证 |
| 鉴定记录 | 定期鉴定 + 上传鉴定报告 |
| 借用/归还 | 工装借用与归还流程 |
| 搜索筛选 | 按编号、名称、状态筛选 |
| 权限控制 | 管理员/普通员工权限分离 |

## 数据库表

1. **users** - 用户表
2. **tools** - 工装表
3. **borrow_records** - 借用记录表
4. **inspections** - 鉴定记录表
5. **attachments** - 附件表
6. **operation_logs** - 操作日志表

## 目录结构

```
tooling-management/
├── backend/           # Flask 后端
│   ├── app.py         # 主入口
│   ├── models.py      # 数据库模型（6张表）
│   ├── routes/        # API路由
│   │   ├── auth.py    # 登录/用户管理
│   │   ├── tools.py   # 工装CRUD
│   │   ├── borrows.py # 借用/归还
│   │   ├── inspections.py  # 鉴定记录
│   │   └── attachments.py  # 文件上传/下载
│   ├── uploads/       # 上传文件存储
│   ├── setup.bat      # 一键安装
│   ├── start.bat      # 一键启动
│   └── requirements.txt
├── frontend/          # Vue.js 前端
└── README.md
```

## 后续计划

- [ ] 前端 Vue.js 界面开发
- [ ] 鉴定到期提醒
- [ ] 数据导出 Excel
- [ ] 迁移腾讯云 MySQL
