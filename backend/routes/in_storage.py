from flask import Blueprint, request, session
from models import db, Tool, InStorageRecord, OperationLog, BorrowRecord, Inspection
from datetime import datetime
from routes.auth import login_required, edit_required, admin_required, add_log

in_storage_bp = Blueprint('in_storage', __name__)


@in_storage_bp.route('/', methods=['GET'])
@login_required
def list_in_storage():
    """获取入库记录列表（需登录；2026-11-01 修复：原接口无鉴权，未登录可直接拉取全部数据）"""
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
@edit_required
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

    # 更新工具状态为在库；但仍有未归还借用的工装保持「借出」不动。
    # 2026-11-05 修复：原实现无条件置在库，批量补录建档记录会把已借出工装状态覆盖。
    has_open_borrow = BorrowRecord.query.filter_by(
        tool_id=tool.id, status='借用中').first() is not None
    if not has_open_borrow:
        tool.status = '在库'
    if storage_date_str:
        tool.storage_date = storage_date  # 写入独立的入库时间，不再覆盖完工日期
        # 入库日期落库后，未被检定记录覆盖的 A/B 级工装按周期重算下次检定
        if not tool.next_inspection_date and tool.level in ('A', 'B'):
            if Inspection.query.filter_by(tool_id=tool.id).count() == 0:
                from routes.tools import calc_next_inspection
                tool.next_inspection_date = calc_next_inspection(
                    tool.level, tool.storage_date)

    db.session.add(record)
    db.session.commit()
    add_log('添加入库记录', f'编号 {tool.code}，入库日期 {storage_date}')
    return {'message': 'success', 'record': record.to_dict()}


@in_storage_bp.route('/<int:record_id>', methods=['DELETE'])
@admin_required
def delete_in_storage(record_id):
    """删除入库记录"""
    record = InStorageRecord.query.get_or_404(record_id)
    tool = record.tool
    db.session.delete(record)
    db.session.commit()
    add_log('删除入库记录', f'编号 {tool.code if tool else ""}')
    return {'message': 'deleted'}
