from flask import Blueprint, request, jsonify, session
from models import db, Tool, Inspection
from routes.auth import login_required, admin_required, add_log
from datetime import datetime

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

