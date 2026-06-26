from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # admin / employee / viewer

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_employee(self):
        return self.role == 'employee'

    @property
    def is_viewer(self):
        return self.role == 'viewer'

    def can_edit(self):
        """是否可以编辑工装（新增/修改，不含删除）"""
        return self.role in ('admin', 'employee')

    def can_delete(self):
        """是否可以删除工装"""
        return self.role == 'admin'

    def can_approve_scrap(self):
        """是否可以审批报废"""
        return self.role == 'admin'

    def can_manage_users(self):
        """是否可以管理用户"""
        return self.role == 'admin'

    def can_manage_config(self):
        """是否可以管理配置"""
        return self.role == 'admin'

    def can_return_borrow(self):
        """是否可以归还借用"""
        return self.role in ('admin', 'employee')

    def can_export(self):
        """是否可以导出数据"""
        return True  # 三个角色都可以导出
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Tool(db.Model):
    """工装表"""
    __tablename__ = 'tools'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    drawing_no = db.Column(db.String(100))  # 图号
    name = db.Column(db.String(100), nullable=False)
    spec = db.Column(db.String(200))
    category = db.Column(db.String(50))  # 类别(量具/刀具/夹具等)
    level = db.Column(db.String(10), default='A')  # 等级(A/B/C)
    factory = db.Column(db.String(100))   # 使用分厂
    team = db.Column(db.String(100))       # 使用班组
    receiver = db.Column(db.String(80))    # 领用人
    status = db.Column(db.String(20), default='在库')  # 在库/借出/维修/报废
    purchase_date = db.Column(db.Date)
    next_inspection_date = db.Column(db.Date)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'drawing_no': self.drawing_no or '',
            'name': self.name,
            'spec': self.spec or '',
            'category': self.category or '',
            'level': self.level or 'A类',
            'factory': self.factory or '',
            'team': self.team or '',
            'receiver': self.receiver or '',
            'status': self.status,
            'purchase_date': self.purchase_date.strftime('%Y-%m-%d') if self.purchase_date else '',
            'next_inspection_date': self.next_inspection_date.strftime('%Y-%m-%d') if self.next_inspection_date else '',
            'remark': self.remark or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }


class BorrowRecord(db.Model):
    """借用记录表"""
    __tablename__ = 'borrow_records'

    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    borrower = db.Column(db.String(80), nullable=False)
    factory = db.Column(db.String(100))   # 使用分厂
    team = db.Column(db.String(100))      # 使用班组
    receiver = db.Column(db.String(80))    # 领用人
    borrow_time = db.Column(db.DateTime, default=datetime.now)
    return_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='借用中')  # 借用中/已归还

    tool = db.relationship('Tool', backref='borrow_records')

    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'tool_code': self.tool.code if self.tool else '',
            'tool_name': self.tool.name if self.tool else '',
            'factory': self.factory or '',
            'team': self.team or '',
            'receiver': self.receiver or '',
            'borrower': self.borrower,
            'borrow_time': self.borrow_time.strftime('%Y-%m-%d %H:%M:%S'),
            'return_time': self.return_time.strftime('%Y-%m-%d %H:%M:%S') if self.return_time else '',
            'status': self.status
        }


class Inspection(db.Model):
    """检定记录表"""
    __tablename__ = 'inspections'

    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    inspect_date = db.Column(db.Date, nullable=False)
    result = db.Column(db.String(20), nullable=False)  # 合格/不合格/待修
    next_date = db.Column(db.Date)
    inspector = db.Column(db.String(80))
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    tool = db.relationship('Tool', backref='inspections')

    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'tool_code': self.tool.code if self.tool else '',
            'tool_name': self.tool.name if self.tool else '',
            'inspect_date': self.inspect_date.strftime('%Y-%m-%d'),
            'result': self.result,
            'next_date': self.next_date.strftime('%Y-%m-%d') if self.next_date else '',
            'inspector': self.inspector or '',
            'remark': self.remark or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Attachment(db.Model):
    """附件表"""
    __tablename__ = 'attachments'

    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=True)  # 允许为空（临时上传）
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspections.id'), nullable=True)  # 检定记录ID
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))  # 入库资料/检定报告/其他
    file_size = db.Column(db.Integer)
    upload_time = db.Column(db.DateTime, default=datetime.now)
    uploader = db.Column(db.String(80))

    tool = db.relationship('Tool', backref='attachments')

    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'inspection_id': self.inspection_id or None,
            'file_name': self.file_name,
            'file_type': self.file_type or '',
            'file_size': self.file_size or 0,
            'upload_time': self.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
            'uploader': self.uploader or ''
        }


class OperationLog(db.Model):
    """操作日志表"""
    __tablename__ = 'operation_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref='operation_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'action': self.action,
            'detail': self.detail or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class SystemConfig(db.Model):
    """系统配置表（可配置的选项）"""
    __tablename__ = 'system_configs'

    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), nullable=False)  # category/factory/team
    config_value = db.Column(db.String(100), nullable=False)  # 配置值
    sort_order = db.Column(db.Integer, default=0)  # 排序顺序
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'sort_order': self.sort_order,
        }


class ScrapRequest(db.Model):
    """报废申请表"""
    __tablename__ = 'scrap_requests'

    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, default='')
    request_type = db.Column(db.String(20), default='scrap')  # scrap/delete
    status = db.Column(db.String(20), default='待审核')  # 待审核/已批准/已拒绝
    created_at = db.Column(db.DateTime, default=datetime.now)
    reviewed_at = db.Column(db.DateTime)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reject_reason = db.Column(db.Text, default='')

    tool = db.relationship('Tool', backref='scrap_requests')
    requester = db.relationship('User', foreign_keys=[requester_id], backref='scrap_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviewed_scraps')

    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'tool_code': self.tool.code if self.tool else '',
            'tool_name': self.tool.name if self.tool else '',
            'requester_id': self.requester_id,
            'requester_name': self.requester.username if self.requester else '',
            'reason': self.reason or '',
            'request_type': self.request_type or 'scrap',
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_at': self.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if self.reviewed_at else '',
            'reviewer_name': self.reviewer.username if self.reviewer else '',
            'reject_reason': self.reject_reason or '',
        }
