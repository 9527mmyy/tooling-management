from flask import Blueprint, request, jsonify, session, current_app
from models import db, Tool, ScrapRequest, BorrowRecord, Inspection, Attachment
from routes.auth import login_required, admin_required, scrap_approve_required, add_log
from routes.tools import cleanup_tool_resources
from datetime import datetime
import os

scraps_bp = Blueprint('scraps', __name__)


def _delete_tool_resources(tool):
    """删除工装及其关联资源。2026-11-04 起与 routes/tools.py 共用一份实现，
    避免两份清理逻辑各自漂移（原 tools.py 版本漏删 attachments 表记录）。"""
    cleanup_tool_resources(tool)


@scraps_bp.route('/', methods=['POST'])
@login_required
def submit_scrap():
    """提交报废/删除申请 或 admin直接执行"""
    data = request.get_json() or {}
    tool_id = data.get('tool_id')
    reason = data.get('reason', '').strip()
    request_type = data.get('request_type', 'scrap')  # scrap 或 delete

    if not tool_id:
        return jsonify({'code': 400, 'msg': '缺少工装信息'})

    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'code': 400, 'msg': '工装不存在'})

    role = session.get('role', '')
    user_id = session['user_id']

    if role == 'admin':
        if request_type == 'delete':
            # admin 直接删除（与 tools.py delete_tool 一致的完整清理）
            active_borrow = BorrowRecord.query.filter_by(
                tool_id=tool_id, status='借用中'
            ).first()
            if active_borrow:
                return jsonify({'code': 400, 'msg': '该工装已借出，无法删除'})
            # 检查检定记录
            active_inspection = Inspection.query.filter_by(tool_id=tool_id).first()
            if active_inspection:
                return jsonify({'code': 400, 'msg': '该工装有检定记录，请先删除检定记录后再删除工装'})
            add_log('删除工装', f'编号 {tool.code}，名称 {tool.name}')
            _delete_tool_resources(tool)
            db.session.commit()
            return jsonify({'code': 200, 'msg': '工装已删除'})
        else:
            # admin 直接报废
            old_status = tool.status
            tool.status = '报废'
            db.session.commit()
            add_log('报废工装', f'编号 {tool.code}，名称 {tool.name}（原状态：{old_status}）')
            return jsonify({'code': 200, 'msg': '工装已报废'})

    # 普通员工: 提交申请
    existing = ScrapRequest.query.filter_by(
        tool_id=tool_id, status='待审核', request_type=request_type
    ).first()
    if existing:
        type_label = '报废' if request_type == 'scrap' else '删除'
        return jsonify({'code': 400, 'msg': f'该工装已有待审核的{type_label}申请，请等待审批'})

    req = ScrapRequest(
        tool_id=tool_id,
        requester_id=user_id,
        reason=reason,
        request_type=request_type
    )
    db.session.add(req)
    db.session.commit()
    type_label = '报废' if request_type == 'scrap' else '删除'
    add_log(f'提交{type_label}申请', f'编号 {tool.code}，名称 {tool.name}，申请人 {session.get("username","")}')

    return jsonify({'code': 200, 'msg': f'{type_label}申请已提交，等待管理员审批'})


@scraps_bp.route('/', methods=['GET'])
@admin_required
def list_scraps():
    """获取申请列表（管理员）"""
    status = request.args.get('status', '').strip()
    request_type = request.args.get('request_type', '').strip()
    # 2026-11-04 修复：type=int 容错非数字（原裸 int() 传 page=abc 直接 500）；
    # per_page 钳制到 [1,100]，防一次拉全库。
    page = request.args.get('page', 1, type=int) or 1
    per_page = min(max(request.args.get('per_page', 20, type=int) or 20, 1), 100)

    query = ScrapRequest.query

    if status:
        query = query.filter_by(status=status)
    if request_type:
        query = query.filter_by(request_type=request_type)

    pagination = query.order_by(ScrapRequest.id.desc()).paginate(
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


@scraps_bp.route('/<int:req_id>/approve', methods=['PUT'])
@scrap_approve_required
def approve_request(req_id):
    """批准申请（报废或删除）"""
    req = ScrapRequest.query.get_or_404(req_id)

    if req.status != '待审核':
        return jsonify({'code': 400, 'msg': '该申请已被处理'})

    tool = Tool.query.get(req.tool_id)
    if not tool:
        return jsonify({'code': 400, 'msg': '工装已不存在'})

    req.status = '已批准'
    req.reviewed_at = datetime.now()
    req.reviewer_id = session['user_id']

    if req.request_type == 'delete':
        # 删除操作（与 tools.py delete_tool 一致的完整清理）
        active_borrow = BorrowRecord.query.filter_by(
            tool_id=tool.id, status='借用中'
        ).first()
        if active_borrow:
            return jsonify({'code': 400, 'msg': '该工装已借出，请先归还后再删除'})
        # 检查检定记录
        active_inspection = Inspection.query.filter_by(tool_id=tool.id).first()
        if active_inspection:
            return jsonify({'code': 400, 'msg': '该工装有检定记录，请先删除检定记录后再删除工装'})
        add_log('审批删除', f'批准删除工装 编号 {tool.code}，名称 {tool.name}，申请人 {req.requester.username}')
        _delete_tool_resources(tool)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除申请已批准，工装已删除'})
    else:
        # 报废操作
        tool.status = '报废'
        db.session.commit()
        add_log('审批报废', f'批准报废工装 编号 {tool.code}，名称 {tool.name}，申请人 {req.requester.username}')
        return jsonify({'code': 200, 'msg': '报废申请已批准，工装已报废'})


@scraps_bp.route('/<int:req_id>/reject', methods=['PUT'])
@scrap_approve_required
def reject_request(req_id):
    """拒绝申请（报废或删除）"""
    req = ScrapRequest.query.get_or_404(req_id)

    if req.status != '待审核':
        return jsonify({'code': 400, 'msg': '该申请已被处理'})

    data = request.get_json() or {}
    reject_reason = data.get('reject_reason', '').strip()

    req.status = '已拒绝'
    req.reviewed_at = datetime.now()
    req.reviewer_id = session['user_id']
    req.reject_reason = reject_reason
    db.session.commit()

    type_label = '报废' if req.request_type == 'scrap' else '删除'
    add_log(f'审批{type_label}', f'拒绝{type_label}工装 编号 {req.tool.code}，原因：{reject_reason or "未填写"}')

    return jsonify({'code': 200, 'msg': f'{type_label}申请已拒绝'})

