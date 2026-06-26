from flask import Blueprint, request, jsonify, session
from models import db, Tool, BorrowRecord, Attachment, Inspection, OperationLog
from routes.auth import login_required, admin_required, add_log
from datetime import datetime

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/', methods=['GET'])
@login_required
def list_tools():
    """获取工装列表，支持搜索筛选"""
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '').strip()
    factory = request.args.get('factory', '').strip()
    team = request.args.get('team', '').strip()
    exclude_status = request.args.get('exclude_status', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    query = Tool.query

    if keyword:
        query = query.filter(
            db.or_(
                Tool.code.contains(keyword),
                Tool.name.contains(keyword),
                Tool.spec.contains(keyword)
            )
        )
    if status:
        query = query.filter_by(status=status)
    if factory:
        query = query.filter(Tool.factory.contains(factory))
    if team:
        query = query.filter(Tool.team.contains(team))
    if exclude_status:
        # 排除指定状态（如'报废'）
        query = query.filter(Tool.status != exclude_status)

    pagination = query.order_by(Tool.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'data': {
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page
        }
    })


@tools_bp.route('/<int:tool_id>', methods=['GET'])
@login_required
def get_tool(tool_id):
    """获取工装详情"""
    tool = Tool.query.get_or_404(tool_id)
    data = tool.to_dict()
    # 附带借用记录
    data['borrow_records'] = [r.to_dict() for r in tool.borrow_records]
    # 附带检定记录
    data['inspections'] = [i.to_dict() for i in tool.inspections]
    # 附带附件列表
    data['attachments'] = [a.to_dict() for a in tool.attachments]
    return jsonify({'code': 200, 'data': data})


@tools_bp.route('/', methods=['POST'])
@admin_required
def create_tool():
    """新增工装（管理员）"""
    data = request.get_json()
    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'code': 400, 'msg': '编号和名称不能为空'})

    if Tool.query.filter_by(code=code).first():
        return jsonify({'code': 400, 'msg': '编号已存在'})

    tool = Tool(
        code=code,
        drawing_no=data.get('drawing_no', ''),
        name=name,
        spec=data.get('spec', ''),
        category=data.get('category', ''),
        level=data.get('level', 'A类'),
        factory=data.get('factory', ''),
        team=data.get('team', ''),
        receiver=data.get('receiver', ''),
        status=data.get('status', '在库'),
        remark=data.get('remark', '')
    )

    if data.get('purchase_date'):
        tool.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    if data.get('next_inspection_date'):
        tool.next_inspection_date = datetime.strptime(data['next_inspection_date'], '%Y-%m-%d').date()

    db.session.add(tool)
    db.session.commit()

    add_log('新增工装', f'编号 {code}，名称 {name}')

    return jsonify({'code': 200, 'msg': '新增成功', 'data': tool.to_dict()})


@tools_bp.route('/inspection-reminders', methods=['GET'])
def get_inspection_reminders():
    """获取检定提醒列表"""
    filter_type = request.args.get('filter', 'overdue')  # overdue, 30, 60, all
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    today = datetime.now().date()
    from datetime import timedelta
    
    # 构建查询（排除已报废的工装）
    query = Tool.query.filter(
        Tool.next_inspection_date != None,
        Tool.status != '报废'
    )
    
    if filter_type == 'overdue':
        # 已逾期
        query = query.filter(Tool.next_inspection_date < today)
    elif filter_type == '30':
        # 30天内到期
        query = query.filter(
            Tool.next_inspection_date >= today,
            Tool.next_inspection_date <= today + timedelta(days=30)
        )
    elif filter_type == '60':
        # 60天内到期
        query = query.filter(
            Tool.next_inspection_date >= today,
            Tool.next_inspection_date <= today + timedelta(days=60)
        )
    elif filter_type == 'all':
        # 全部（有检定日期的）
        pass
    
    # 分页
    total = query.count()
    tools = query.order_by(Tool.next_inspection_date.asc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    # 计算剩余天数
    result = []
    for tool in tools.items:
        tool_dict = tool.to_dict()
        next_date = tool.next_inspection_date
        if next_date:
            days_until = (next_date - today).days
            tool_dict['days_until_inspection'] = days_until
        else:
            tool_dict['days_until_inspection'] = None
        result.append(tool_dict)
    
    return jsonify({
        'code': 200,
        'data': {
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    })


@tools_bp.route('/<int:tool_id>', methods=['PUT'])
@admin_required
def update_tool(tool_id):
    """更新工装（管理员）"""
    tool = Tool.query.get_or_404(tool_id)
    data = request.get_json()

    if 'code' in data:
        new_code = data['code'].strip()
        if new_code != tool.code and Tool.query.filter_by(code=new_code).first():
            return jsonify({'code': 400, 'msg': '编号已存在'})
        tool.code = new_code
    if 'name' in data:
        tool.name = data['name'].strip()
    if 'drawing_no' in data:
        tool.drawing_no = data['drawing_no'] or ''
    if 'spec' in data:
        tool.spec = data['spec'] or ''
    if 'category' in data:
        tool.category = data['category'] or ''
    if 'level' in data:
        tool.level = data['level'] or 'A类'
    if 'factory' in data:
        tool.factory = data['factory'] or None
    if 'team' in data:
        tool.team = data['team'] or None
    if 'receiver' in data:
        tool.receiver = data['receiver'] or None
    if 'status' in data:
        tool.status = data['status']
    if 'remark' in data:
        tool.remark = data['remark'] or ''
    if 'purchase_date' in data and data['purchase_date']:
        tool.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    elif 'purchase_date' in data and not data['purchase_date']:
        tool.purchase_date = None
    if 'next_inspection_date' in data and data['next_inspection_date']:
        tool.next_inspection_date = datetime.strptime(data['next_inspection_date'], '%Y-%m-%d').date()
    elif 'next_inspection_date' in data and not data['next_inspection_date']:
        tool.next_inspection_date = None

    db.session.commit()

    add_log('更新工装', f'编号 {tool.code}，名称 {tool.name}')

    return jsonify({'code': 200, 'msg': '更新成功', 'data': tool.to_dict()})


@tools_bp.route('/<int:tool_id>', methods=['DELETE'])
@admin_required
def delete_tool(tool_id):
    """删除工装（管理员）"""
    tool = Tool.query.get_or_404(tool_id)

    # 检查是否有未归还的借用
    active_borrow = BorrowRecord.query.filter_by(
        tool_id=tool_id, status='借用中'
    ).first()
    if active_borrow:
        return jsonify({'code': 400, 'msg': '该工装有未归还的借用记录，不能删除'})

    # 检查是否有检定记录
    inspection = Inspection.query.filter_by(tool_id=tool_id).first()
    if inspection:
        return jsonify({'code': 400, 'msg': '该工装有检定记录，请先删除检定记录后再删除工装'})

    add_log('删除工装', f'编号 {tool.code}，名称 {tool.name}')

    # 删除关联附件文件
    for att in tool.attachments:
        import os
        if os.path.exists(att.file_path):
            os.remove(att.file_path)

    db.session.delete(tool)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '删除成功'})


@tools_bp.route('/stats', methods=['GET'])
@login_required
def tool_stats():
    """工装统计"""
    total = Tool.query.count()
    in_stock = Tool.query.filter_by(status='在库').count()
    borrowed = Tool.query.filter_by(status='借出').count()
    repairing = Tool.query.filter_by(status='维修').count()
    scrapped = Tool.query.filter_by(status='报废').count()

    # 即将到期检定（30天内）
    today = datetime.now().date()
    from datetime import timedelta
    due_soon = Tool.query.filter(
        Tool.next_inspection_date != None,
        Tool.next_inspection_date <= today + timedelta(days=30),
        Tool.next_inspection_date >= today
    ).count()

    overdue = Tool.query.filter(
        Tool.next_inspection_date != None,
        Tool.next_inspection_date < today
    ).count()

    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'in_stock': in_stock,
            'borrowed': borrowed,
            'repairing': repairing,
            'scrapped': scrapped,
            'due_soon': due_soon,
            'overdue': overdue
        }
    })
