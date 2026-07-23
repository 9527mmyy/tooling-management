from flask import Blueprint, request, session
from models import db, Tool, InStorageRecord, OperationLog
from datetime import datetime

in_storage_bp = Blueprint('in_storage', __name__)


@in_storage_bp.route('/', methods=['GET'])
def list_in_storage():
    """获取入库记录列表"""
    tool_id = request.args.get('tool_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = InStorageRecord.query
    if tool_id:
        query = query.filter_by(tool_id=tool_id)

    pagination = query.order_by(InStorageRecord.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return {
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'page': page
    }


@in_storage_bp.route('/', methods=['POST'])
def create_in_storage():
    """创建入库记录"""
    data = request.get_json() or {}
    tool_id = data.get('tool_id')
    if not tool_id:
        return {'error': '缺少 tool_id'}, 400

    tool = Tool.query.get_or_404(tool_id)

    storage_date_str = data.get('storage_date', '')
    try:
        storage_date = datetime.strptime(storage_date_str, '%Y-%m-%d').date() if storage_date_str else datetime.now().date()
    except ValueError:
        storage_date = datetime.now().date()

    operator = data.get('operator', session.get('username', ''))

    record = InStorageRecord(
        tool_id=tool_id,
        storage_date=storage_date,
        supplier=data.get('supplier', ''),
        batch_no=data.get('batch_no', ''),
        quantity=data.get('quantity', 1),
        storage_location=data.get('storage_location', ''),
        operator=operator,
        remark=data.get('remark', '')
    )

    # 更新工具状态为在库
    tool.status = '在库'
    if storage_date_str:
        tool.purchase_date = storage_date_str

    db.session.add(record)
    db.session.commit()
    add_log('添加入库记录', f'编号 {tool.code}，入库日期 {storage_date}')
    return {'message': 'success', 'record': record.to_dict()}


@in_storage_bp.route('/<int:record_id>', methods=['DELETE'])
def delete_in_storage(record_id):
    """删除入库记录"""
    record = InStorageRecord.query.get_or_404(record_id)
    tool = record.tool
    db.session.delete(record)
    db.session.commit()
    add_log('删除入库记录', f'编号 {tool.code if tool else ""}')
    return {'message': 'deleted'}


def add_log(action, detail):
    """操作日志"""
    username = session.get('username', '')
    log = OperationLog(
        user=username,
        action=action,
        detail=detail,
        ip=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
