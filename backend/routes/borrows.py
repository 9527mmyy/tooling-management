from flask import Blueprint, request, jsonify, session
from models import db, Tool, BorrowRecord
from routes.auth import login_required, edit_required, return_required, add_log
from datetime import datetime

borrows_bp = Blueprint('borrows', __name__)


@borrows_bp.route('/', methods=['GET'])
@login_required
def list_borrows():
    """获取借用记录列表"""
    status = request.args.get('status', '').strip()
    borrower = request.args.get('borrower', '').strip()
    factory = request.args.get('factory', '').strip()
    team = request.args.get('team', '').strip()
    # 2026-11-04 修复：type=int 容错非数字（原裸 int() 传 page=abc 直接 500）；
    # per_page 钳制到 [1,100]，防一次拉全库。
    page = request.args.get('page', 1, type=int) or 1
    per_page = min(max(request.args.get('per_page', 20, type=int) or 20, 1), 100)

    query = BorrowRecord.query

    if status:
        query = query.filter_by(status=status)
    if borrower:
        query = query.filter(BorrowRecord.borrower.contains(borrower))
    if factory:
        query = query.filter(BorrowRecord.factory.contains(factory))
    if team:
        query = query.filter(BorrowRecord.team.contains(team))

    pagination = query.order_by(BorrowRecord.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'data': {
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@borrows_bp.route('/', methods=['POST'])
@edit_required
def create_borrow():
    """借用工装（admin/employee；viewer 无权借用）"""
    data = request.get_json() or {}
    tool_id = data.get('tool_id')
    borrower = data.get('borrower', session.get('username', '')).strip()

    if not tool_id:
        return jsonify({'code': 400, 'msg': '请选择工装'})

    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'code': 404, 'msg': '工装不存在'})
    if tool.status != '在库':
        return jsonify({'code': 400, 'msg': f'工装状态为{tool.status}，不可借用'})

    # 创建借用记录
    record = BorrowRecord(
        tool_id=tool_id,
        borrower=borrower,
        factory=data.get('factory', ''),
        team=data.get('team', ''),
        receiver=data.get('receiver', ''),
        status='借用中'
    )
    # 更新工装状态。使用分厂/班组/领用人属于台账固有归属：
    # 已有值不覆盖（避免一次借用把原归属改写掉），但台账里为空的
    # （批量导入的新工装）用本次借用信息回填，让台账直接看到在用归属。
    tool.status = '借出'
    if not tool.factory and data.get('factory'):
        tool.factory = data['factory']
    if not tool.team and data.get('team'):
        tool.team = data['team']
    if not tool.receiver and data.get('receiver'):
        tool.receiver = data['receiver']

    db.session.add(record)
    db.session.commit()

    add_log('借用工装', f'编号 {tool.code}，借用人 {borrower}')

    return jsonify({'code': 200, 'msg': '借用成功', 'data': record.to_dict()})


@borrows_bp.route('/<int:record_id>/return', methods=['POST'])
@return_required
def return_borrow(record_id):
    """归还工装"""
    record = BorrowRecord.query.get_or_404(record_id)

    if record.status != '借用中':
        return jsonify({'code': 400, 'msg': '该记录已归还'})

    # 更新借用记录
    record.status = '已归还'
    record.return_time = datetime.now()
    # 记录退库人与备注（退库动作独立成事件）
    data = request.get_json(silent=True) or {}
    record.return_operator = session.get('username') or session.get('user_no') or ''
    record.return_remark = (data.get('remark') or '').strip()
    record.return_check = (data.get('check') or '').strip()

    # 更新工装状态。台账归属（factory/team/receiver）是工装固有信息，
    # 2026-11-04 修复：归还不清除，否则归还一次台账就永久丢三个字段。
    tool = Tool.query.get(record.tool_id)
    if tool:
        tool.status = '在库'

    db.session.commit()

    add_log('归还工装', f'编号 {tool.code if tool else ""}，借用人 {record.borrower}')

    return jsonify({'code': 200, 'msg': '归还成功', 'data': record.to_dict()})
