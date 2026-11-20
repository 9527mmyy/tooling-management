from flask import Flask, send_from_directory, make_response, redirect
from flask_cors import CORS
from flask_compress import Compress
import os
from datetime import timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
# CORS 收紧（2026-10-27 安全加固）：原为 origins='*' + supports_credentials=True，
# 任何网站都能带凭证跨源读取。当前为前后端同源部署，跨域仅需支持本机（含桌面版 127.0.0.1:8765）；
# 同源访问不受 CORS 影响；如后续有内网跨域需求，在此白名单追加来源即可。
CORS(app, supports_credentials=True, origins=[
    'http://localhost:5000', 'http://127.0.0.1:5000',
    'http://localhost:8765', 'http://127.0.0.1:8765',
])
Compress(app)  # 启用gzip压缩
app.url_map.strict_slashes = False  # 允许尾部斜杠

# 静态文件缓存配置（1天）
@app.after_request
def add_cache_headers(response):
    from flask import request
    if 'static' in request.path:
        response.cache_control.max_age = 86400
        response.cache_control.public = True
    return response

# 配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'tooling.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'check_same_thread': False},
    'pool_pre_ping': True
}
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 上传限制
# 会话密钥：优先环境变量（nssm AppEnvironmentExtra，2026-09-30 实测生效）；
# 环境变量缺失时回退到「仓库外的密钥文件」，避免回落到代码里那个**已公开**的兜底常量。
# 密钥不进代码库、不进 git。
def _read_secret(env_name):
    """会话密钥来源：环境变量 > 仓库外密钥文件 > 现场生成并落盘。

    2026-11-04 修复：原实现的最终兜底是代码里那个已公开的硬编码常量，
    一旦新部署漏带环境变量或密钥文件，任何人都能用它伪造 admin 会话。
    现在绝不回落到常量；密钥目录默认取 backend 上两级的 _secrets，
    与现有部署一致，迁移到别的机器也能自适应。
    """
    import secrets as _secrets

    v = (os.environ.get(env_name) or '').strip()
    if v:
        return v

    secret_dir = (os.environ.get('TOOLING_SECRET_DIR')
                  or os.path.join(os.path.dirname(os.path.dirname(basedir)), '_secrets'))
    key_path = os.path.join(secret_dir, env_name + '.key')
    try:
        with open(key_path, encoding='utf-8') as f:
            v = f.read().strip()
        if v:
            return v
    except OSError:
        pass

    v = _secrets.token_hex(32)
    try:
        os.makedirs(secret_dir, exist_ok=True)
        with open(key_path, 'w', encoding='utf-8') as f:
            f.write(v)
        print('[WARN] 未找到会话密钥，已生成新密钥并写入 ' + key_path)
    except OSError:
        print('[WARN] 会话密钥无法落盘，本次使用临时密钥；重启后所有会话将失效')
    return v


app.config['SECRET_KEY'] = _read_secret('TOOLING_SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # cookie有效期（实际超时由服务端last_activity控制）
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 允许同站请求携带cookie
app.config['SESSION_COOKIE_HTTPONLY'] = True

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 请求日志（调试用）
@app.before_request
def log_request():
    from flask import request
    from datetime import datetime
    if request.path.startswith('/api/'):
        print(f'[{datetime.now().strftime("%H:%M:%S")}] {request.method} {request.path}')

# CSRF 来源校验（2026-10-27 安全加固）：
# 会话基于 Cookie，无 CSRF Token。对写操作校验 Origin/Referer，阻止跨站请求伪造。
# · 无 Origin/Referer（桌面版、curl、内网脚本等非浏览器客户端）→ 放行
# · 与请求 Host 同源 → 放行（浏览器同源写请求会携带 Origin）
# · hostname 为 localhost/127.0.0.1 → 放行（本机桌面版 / 本地调试）
# · 其余跨站来源 → 拒绝
@app.before_request
def csrf_protect():
    from urllib.parse import urlparse
    from flask import jsonify, request
    if request.method not in ('POST', 'PUT', 'DELETE', 'PATCH'):
        return None
    src = request.headers.get('Origin') or request.headers.get('Referer')
    if not src:
        return None  # 非浏览器客户端，无法校验来源
    try:
        o = urlparse(src)
    except ValueError:
        return jsonify({'code': 403, 'msg': '非法请求来源'}), 403
    if o.netloc == request.host:
        return None  # 同源
    if o.hostname in ('localhost', '127.0.0.1'):
        return None  # 本机
    return jsonify({'code': 403, 'msg': '跨站请求被拒绝'}), 403

from models import db
db.init_app(app)

# SQLite 性能优化
with app.app_context():
    from sqlalchemy import text
    db.session.execute(text('PRAGMA journal_mode=WAL'))
    db.session.execute(text('PRAGMA synchronous=NORMAL'))
    db.session.execute(text('PRAGMA cache_size=10000'))
    db.session.commit()

# 注册路由
from routes.auth import auth_bp
from routes.tools import tools_bp
from routes.borrows import borrows_bp
from routes.inspections import inspections_bp
from routes.attachments import attachments_bp
from routes.scraps import scraps_bp
from routes.org import org_bp
from routes.configs import configs_bp
from routes.export import export_bp
from routes.import_tools import import_bp
from routes.in_storage import in_storage_bp

app.register_blueprint(org_bp, url_prefix='/api/org')
app.register_blueprint(configs_bp, url_prefix='/api/configs')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(tools_bp, url_prefix='/api/tools')
app.register_blueprint(borrows_bp, url_prefix='/api/borrows')
app.register_blueprint(inspections_bp, url_prefix='/api/inspections')
app.register_blueprint(attachments_bp, url_prefix='/api/attachments')
app.register_blueprint(scraps_bp, url_prefix='/api/scraps')
app.register_blueprint(export_bp, url_prefix='/api/export')
app.register_blueprint(import_bp, url_prefix='/api/import')
app.register_blueprint(in_storage_bp, url_prefix='/api/in_storage')

# 健康检查（公开端点，供监控探活；不返回任何敏感信息）
@app.route('/api/health')
def health_check():
    """监控系统探活端点：返回服务状态与当前时间，无需登录。"""
    from flask import jsonify
    from datetime import datetime
    try:
        # 轻量数据库连通性探测，确保服务与数据库都正常
        with app.app_context():
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'ok',
            'time': datetime.now().isoformat(timespec='seconds'),
            'service': 'tooling-management'
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 500

# 关于信息（公开端点，供登录页页脚与「关于」对话框读取）
@app.route('/api/system/about')
def system_about():
    """返回系统版本与出品信息。数据源：backend/version.py"""
    from flask import jsonify
    from version import get_about
    return jsonify({'code': 200, 'data': get_about()})

# 前端路由
@app.route('/')
def index():
    """工装管理系统首页（直接显示登录页）"""
    response = make_response(send_from_directory('templates', 'index.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/tooling')
def tooling_index():
    """工装管理系统入口（禁用缓存）"""
    response = make_response(send_from_directory('templates', 'index.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


with app.app_context():
    db.create_all()
    # 创建默认管理员
    from models import User
    if not User.query.filter_by(username='admin').first():
        # 同时设置 user_no='admin'，否则全新安装时登录接口（按工号校验）无法登录
        admin = User(username='admin', user_no='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ 默认管理员创建: admin / admin123（工号 admin）')

@app.route('/test')
def test_page():
    response = make_response(send_from_directory('templates', 'test.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
