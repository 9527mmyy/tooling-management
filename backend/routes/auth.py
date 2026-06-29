from flask import Blueprint, request, jsonify, session
from models import db, User, OperationLog
from functools import wraps
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# 会话超时时间（30分钟无操作自动登出）
SESSION_TIMEOUT = timedelta(minutes=30)


def login_required(f):
    """登录验证装饰器（含30分钟无操作自动登出）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        # 检查30分钟无操作超时
        last_activity = session.get('last_activity')
        if last_activity:
            try:
                last_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_time > SESSION_TIMEOUT:
                    session.clear()
                    return jsonify({'code': 401, 'msg': '登录已超时，请重新登录'}), 401
            except (ValueError, TypeError):
                pass
        # 更新最后活动时间
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        if session.get('role') != 'admin':
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated


def edit_required(f):
    """编辑权限装饰器（admin或employee）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        if session.get('role') not in ('admin', 'employee'):
            return jsonify({'code': 403, 'msg': '无编辑权限'}), 403
        return f(*args, **kwargs)
    return decorated


def delete_required(f):
    """删除权限装饰器（仅admin）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        if session.get('role') != 'admin':
            return jsonify({'code': 403, 'msg': '无删除权限'}), 403
        return f(*args, **kwargs)
    return decorated


def scrap_approve_required(f):
    """报废审批权限装饰器（仅admin）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        if session.get('role') != 'admin':
            return jsonify({'code': 403, 'msg': '无审批权限'}), 403
        return f(*args, **kwargs)
    return decorated


def return_required(f):
    """借用归还权限装饰器（admin或employee）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        if session.get('role') not in ('admin', 'employee'):
            return jsonify({'code': 403, 'msg': '无归还权限'}), 403
        return f(*args, **kwargs)
    return decorated


def add_log(action, detail=''):
    """记录操作日志"""
    if 'user_id' in session:
        log = OperationLog(
            user_id=session['user_id'],
            action=action,
            detail=detail
        )
        db.session.add(log)
        db.session.commit()


@auth_bp.route('/login', methods=['POST'])
def login():
    """登录（仅支持工号）"""
    data = request.get_json()
    user_no = data.get('user_no', '').strip()
    password = data.get('password', '').strip()

    if not user_no or not password:
        return jsonify({'code': 400, 'msg': '工号和密码不能为空'})

    user = User.query.filter_by(user_no=user_no).first()
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'msg': '工号或密码错误'})

    session.permanent = True
    session['user_id'] = user.id
    session['username'] = user.username
    session['user_no'] = user.user_no
    session['role'] = user.role
    session['last_activity'] = datetime.now().isoformat()

    add_log('登录', f'用户 {user.username}({user_no}) 登录')

    return jsonify({
        'code': 200,
        'msg': '登录成功',
        'data': {
            **user.to_dict(),
            'permissions': {
                'can_edit': user.can_edit(),
                'can_delete': user.can_delete(),
                'can_approve_scrap': user.can_approve_scrap(),
                'can_manage_users': user.can_manage_users(),
                'can_manage_config': user.can_manage_config(),
                'can_return_borrow': user.can_return_borrow(),
                'can_export': user.can_export(),
            }
        }
    })


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改当前用户密码"""
    data = request.get_json()
    old_password = data.get('old_password', '').strip()
    new_password = data.get('new_password', '').strip()
    confirm_password = data.get('confirm_password', '').strip()

    if not old_password or not new_password:
        return jsonify({'code': 400, 'msg': '旧密码和新密码不能为空'})

    if len(new_password) < 6:
        return jsonify({'code': 400, 'msg': '新密码至少6位'})

    if new_password != confirm_password:
        return jsonify({'code': 400, 'msg': '两次输入的新密码不一致'})

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'code': 401, 'msg': '用户不存在'})

    if not user.check_password(old_password):
        return jsonify({'code': 400, 'msg': '旧密码错误'})

    user.set_password(new_password)
    db.session.commit()
    add_log('修改密码', f'用户 {user.username} 修改了密码')

    return jsonify({'code': 200, 'msg': '密码修改成功'})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """登出"""
    add_log('登出', f'用户 {session.get("username", "")} 登出')
    session.clear()
    return jsonify({'code': 200, 'msg': '已登出'})


@auth_bp.route('/info', methods=['GET'])
def info():
    """获取当前用户信息"""
    if 'user_id' not in session:
        return jsonify({'code': 401, 'msg': '未登录'})
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'code': 401, 'msg': '用户不存在'})
    return jsonify({
        'code': 200,
        'data': {
            **user.to_dict(),
            'permissions': {
                'can_edit': user.can_edit(),
                'can_delete': user.can_delete(),
                'can_approve_scrap': user.can_approve_scrap(),
                'can_manage_users': user.can_manage_users(),
                'can_manage_config': user.can_manage_config(),
                'can_return_borrow': user.can_return_borrow(),
                'can_export': user.can_export(),
            }
        }
    })


@auth_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """获取用户列表（管理员）"""
    users = User.query.all()
    return jsonify({
        'code': 200,
        'data': [u.to_dict() for u in users]
    })


@auth_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """创建用户（管理员）"""
    data = request.get_json()
    user_no = data.get('user_no', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'employee')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'})

    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'msg': '用户名已存在'})

    if user_no and User.query.filter_by(user_no=user_no).first():
        return jsonify({'code': 400, 'msg': '用户编号已存在'})

    user = User(user_no=user_no, username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    add_log('创建用户', f'创建用户 {username}({user_no})，角色 {role}')

    return jsonify({'code': 200, 'msg': '创建成功', 'data': user.to_dict()})


@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户（管理员）"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'user_no' in data:
        new_no = data['user_no'].strip()
        if new_no != user.user_no and User.query.filter_by(user_no=new_no).first():
            return jsonify({'code': 400, 'msg': '用户编号已存在'})
        user.user_no = new_no
    if 'password' in data and data['password'].strip():
        user.set_password(data['password'])
    if 'role' in data:
        user.role = data['role']

    db.session.commit()
    add_log('更新用户', f'更新用户 {user.username}')

    return jsonify({'code': 200, 'msg': '更新成功', 'data': user.to_dict()})


@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户（管理员）"""
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        return jsonify({'code': 400, 'msg': '不能删除默认管理员'})

    add_log('删除用户', f'删除用户 {user.username}')
    db.session.delete(user)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '删除成功'})
