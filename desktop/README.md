# 工装管理系统 · 单机版打包工程 / Tooling Management System — Desktop Build

把仓库中的联网版系统（`backend/`，Flask + SQLite + Vue 单页前端）封装成 Windows 单机可安装程序。**除发布时同步 `backend/version.py` 版本号外，本工程对原系统只读，不改动其运行数据。**

## 产物 / Artifacts

| 文件 / File | 说明 / Description |
|---|---|
| `build\installer\ToolingManagement-Setup-<版本>-<日期>.exe` | 安装包（分发用，约 19MB）/ Installer |
| `build\dist\ToolingManagement\` | 免安装运行目录（PyInstaller onedir，约 36MB）/ Portable |

安装后的形态：

- 双击桌面快捷方式，弹出**独立原生窗口**（pywebview + 系统 WebView2），不是浏览器标签页，无地址栏，任务栏有独立图标。
- **不需要登录**：本机打开直接进主界面，以管理员身份操作。
- 程序只监听 `127.0.0.1`，局域网与外网都无法访问。
- 数据（数据库 / 上传附件 / 密钥 / 日志）在 `%LOCALAPPDATA%\ToolingManagement`，与安装目录分离，卸载重装不丢数据。
- **安装包不含任何真实工装数据**。全新安装只写入 3 条 `DEMO-*` 示例工装（便于认识界面，可直接删除）；已有台账时一条示例都不会写。`sync_src.py` 每次构建都会清掉 `src/` 里残留的数据库文件。

## 与原系统的关系 / Relationship to the server build

本工程**不复制、不修改**原系统源码。构建时由 `sync_src.py`：

1. 从同仓库的 `backend/` 抽取源码快照到 `src\`（排除 venv / 数据库 / 上传件 / 日志）
2. 用 `overlay\` 下的文件覆盖 `paths.py`、`launcher.py`
3. 对 `app.py` 施加若干补丁（全部打在副本上），未命中即报错退出

原系统源码与运行数据始终保持干净、不受影响。

### app.py 的关键补丁

| # | 原代码 / Original | 改后 / Patched | 原因 / Reason |
|---|---|---|---|
| 1 | — | 顶部 `import paths` | 引入路径解析 |
| 2 | `static_folder='static'` 等相对路径 | `paths.resource_path(...)` | 打包后工作目录变化，相对路径会 404 |
| 3 | `basedir = os.path.dirname(__file__)` | `paths.data_dir()` | 打包后 `__file__` 指向只读临时目录 |
| 4 | 环境变量 / 仓库外密钥文件 | `paths.secret_key()` | 分发机器上不存在原部署路径 |
| 5 | `send_from_directory('templates', ...)` | 绝对路径版本 | 该函数按当前工作目录解析，打包后失效 |
| 6 | `port=5000`、`host='0.0.0.0'` | `paths.port()` / `paths.host()` | 单机版只监听本机，避开常用端口 |
| 7 | — | 新增 `_auto_login_local()` | 单机免登录：仅本机来源自动以管理员建立会话 |

## 构建 / Build

```
build.bat            # 同步源码 + 生成图标 + PyInstaller 打包 + 完整性清单
build_installer.bat  # 用 Inno Setup 编译安装包
```

前置依赖：

- 原系统 `backend\venv` 中已装 `pyinstaller`、`pywebview`、`pillow`（`build.bat` 默认取 `..\backend\venv\Scripts\python.exe`，找不到时回退到 PATH 中的 `python`）
- Inno Setup 6（默认查找其标准安装目录下的 `ISCC.exe`，也可把编译器放到工程的 `tools\InnoSetup\` 下）

## 运行参数 / Runtime options

环境变量（可选）：

| 变量 / Variable | 作用 / Purpose |
|---|---|
| `TOOLING_PORT` | 覆盖监听端口（默认 8765） |
| `TOOLING_HOST` | 覆盖监听地址（默认 `127.0.0.1`；单机版请勿改成 `0.0.0.0`） |
| `TOOLING_DATA_DIR` | 强制指定数据目录（调试用） |
| `TOOLING_SECRET_KEY` | 覆盖会话密钥 |
| `TOOLING_LEGACY_SECRET` | 调试时读取旧密钥文件的路径（可选） |

命令行参数：

| 参数 / Argument | 作用 / Purpose |
|---|---|
| 无 / none | 弹出原生窗口（日常使用）/ native window |
| `--service` | 只起服务不开窗口（脚本 / 调试用）/ service only |

## 完整性校验 / Integrity check

启动器对程序文件做 SHA-256 全量校验，清单由 `make_integrity.py` 在每次构建后生成，并用 HMAC 签名。

**这是一道「防误改」而非「防逆向」的防线**：有本机管理员权限的人仍可替换或复制程序文件，校验只能在其后报告「已被改过」并拒绝启动。恢复方式是重新运行安装包。打包产物中的 Python 字节码也可被现有工具提取还原，因此不要把任何需要保密的凭据写进业务代码。

## 启动耗时 / Startup timing

实测端到端约 2.9 秒（进程启动 → 服务就绪），加上窗口渲染约 3–4 秒。主要阶段：完整性校验 ~0.19s、端口探测 ~0.21s、导入 Flask 应用 ~1.17s、WebView2 初始化 + 页面加载 1–2s。

两处曾造成约 2 秒无谓等待的问题已修：本机探测走系统代理（改用 `ProxyHandler({})` 绕过）、socket 超时过长（0.6s → 0.2s，先做端口探测再发 HTTP 请求）。各阶段耗时写入 `%LOCALAPPDATA%\ToolingManagement\app.log`（搜 `[启动计时]`）。

安装到 `Program Files` 后启动会比免安装目录慢约 0.8 秒（Windows Defender 实时扫描），可选地把安装目录加入 Defender 排除项——安装包不会自动改动安全软件配置。

### 安装时被安全软件拦截

静默安装时，带 HIPS 主动防御的安全软件可能拦截安装器，表现为长时间无响应、连安装日志都不生成。处理办法是把安装包与安装目录加入信任区，或临时关闭主动防御。判断方法：同一份产物用免安装方式若能正常运行，说明程序本体没问题，只是安装环节被拦。

## 排查 / Troubleshooting

- 运行日志：`%LOCALAPPDATA%\ToolingManagement\app.log`
- 端口占用：改 `%LOCALAPPDATA%\ToolingManagement\config.json` 中的 `port`
- 数据目录不可写时会自动回退到 `%ProgramData%` 与用户主目录

## 已知限制 / Limitations

- 目标 Windows x64，依赖系统已安装 **WebView2 Runtime**（Win10 / Win11 通常随 Edge 自带）。
- 服务用 Flask 自带开发服务器，单机自用足够，不面向多人并发。
- 本版本**不组网**。多人共用应改用服务端部署模式（保留登录 + 防火墙放行），不要把本版本的免登录形态改成对外监听。
