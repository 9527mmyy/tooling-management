from flask import Flask, send_from_directory, make_response
from flask_cors import CORS
from flask_compress import Compress
import os
from datetime import timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True, origins='*')
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
# 优先读取环境变量，未设置时回退到默认值（保持向后兼容）
app.config['SECRET_KEY'] = os.environ.get('TOOLING_SECRET_KEY', 'tooling-management-secret-key-2026')
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
    """前端首页（禁用缓存，避免前端代码更新后浏览器仍用旧版）"""
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

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)

@app.route('/test')
def test_page():
    response = make_response(send_from_directory('templates', 'test.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
