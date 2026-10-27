from flask import Blueprint, request, jsonify, session
from models import db, Tool, Inspection, Attachment
from routes.auth import login_required, admin_required, edit_required, add_log
from datetime import datetime
import os

inspections_bp = Blueprint('inspections', __name__)


@inspections_bp.route('/', methods=['GET'])
@login_required
def list_inspections():
    """获取检定记录列表"""
    tool_id = request.args.get('tool_id', type=int)
    result = request.args.get('result', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    query = Inspection.query

    if tool_id:
        query = query.filter_by(tool_id=tool_id)
    if result:
        query = query.filter_by(result=result)

    pagination = query.order_by(Inspection.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'data': {
            'items': [i.to_dict() for i in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@inspections_bp.route('/', methods=['POST'])
@login_required
def create_inspection():
    """新增检定记录"""
    data = request.get_json()
    tool_id = data.get('tool_id')
    inspect_date = data.get('inspect_date')
    result = data.get('result', '').strip()
    next_date = data.get('next_date')
    inspector = data.get('inspector', '').strip()
    remark = data.get('remark', '')

    if not tool_id or not inspect_date or not result:
        return jsonify({'code': 400, 'msg': '工装、检定日期和结果不能为空'})

    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'code': 404, 'msg': '工装不存在'})

    inspection = Inspection(
        tool_id=tool_id,
        inspect_date=datetime.strptime(inspect_date, '%Y-%m-%d').date(),
        result=result,
        inspector=inspector,
        remark=remark
    )

    if next_date:
        next_date_obj = datetime.strptime(next_date, '%Y-%m-%d').date()
        inspection.next_date = next_date_obj
        # 同步更新工装表的下次检定日期
        tool.next_inspection_date = next_date_obj

    # 如果检定不合格，更新工装状态
    if result == '不合格':
        tool.status = '维修'
    elif result == '待修':
        tool.status = '维修'

    db.session.add(inspection)
    db.session.commit()

    add_log('新增检定', f'编号 {tool.code}，结果 {result}')

    return jsonify({'code': 200, 'msg': '检定记录添加成功', 'data': inspection.to_dict()})


def _sync_next_inspection_date(tool):
    """重算工装下次检定日期（2026-10-27 修复6）：
    取该工装最新一条检定记录的 next_date；若无记录或记录无 next_date，
    则按等级与入库时间推算（A=半年/B=一年），C 级不推算。"""
    from routes.tools import calc_next_inspection
    if not tool:
        return
    latest = Inspection.query.filter_by(tool_id=tool.id).order_by(
        Inspection.inspect_date.desc(), Inspection.id.desc()).first()
    if latest and latest.next_date:
        tool.next_inspection_date = latest.next_date
    else:
        tool.next_inspection_date = calc_next_inspection(tool.level, tool.storage_date)
    db.session.commit()


@inspections_bp.route('/<int:inspection_id>', methods=['PUT'])
@edit_required
def update_inspection(inspection_id):
    """更新检定记录（admin/employee），同步工装状态与下次检定日期"""
    inspection = Inspection.query.get_or_404(inspection_id)
    data = request.get_json() or {}

    if 'inspect_date' in data and data['inspect_date']:
        inspection.inspect_date = datetime.strptime(data['inspect_date'], '%Y-%m-%d').date()
    if 'result' in data and data['result']:
        inspection.result = data['result'].strip()
    if 'next_date' in data:
        inspection.next_date = datetime.strptime(data['next_date'], '%Y-%m-%d').date() if data['next_date'] else None
    if 'inspector' in data:
        inspection.inspector = data['inspector'].strip() or None
    if 'remark' in data:
        inspection.remark = data['remark'] or ''

    tool = Tool.query.get(inspection.tool_id)
    # 结果改为不合格/待修时，工装进入维修状态（与新增逻辑一致）
    if tool and inspection.result in ('不合格', '待修'):
        tool.status = '维修'
    db.session.commit()

    _sync_next_inspection_date(tool)
    add_log('更新检定', f'编号 {tool.code if tool else ""}，结果 {inspection.result}')

    return jsonify({'code': 200, 'msg': '检定记录更新成功', 'data': inspection.to_dict()})


@inspections_bp.route('/<int:inspection_id>', methods=['DELETE'])
@admin_required
def delete_inspection(inspection_id):
    """删除检定记录（管理员），同步工装下次检定日期"""
    inspection = Inspection.query.get_or_404(inspection_id)
    tool = Tool.query.get(inspection.tool_id)

    # 删除该检定关联的附件（检定报告）记录与磁盘文件
    for att in Attachment.query.filter_by(inspection_id=inspection_id).all():
        if os.path.exists(att.file_path):
            try:
                os.remove(att.file_path)
            except OSError:
                pass
        db.session.delete(att)

    add_log('删除检定', f'工装 {tool.code if tool else ""}，检定日期 {inspection.inspect_date}')
    db.session.delete(inspection)
    db.session.commit()

    _sync_next_inspection_date(tool)
    return jsonify({'code': 200, 'msg': '检定记录已删除'})

