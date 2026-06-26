from flask import Blueprint, request, jsonify, current_app, send_file, session
from models import db, Attachment, Tool
from routes.auth import login_required, admin_required, edit_required, add_log
import os
import uuid
from datetime import datetime

attachments_bp = Blueprint('attachments', __name__)


@attachments_bp.route('/', methods=['GET'])
@login_required
def list_attachments():
    """获取附件列表"""
    tool_id = request.args.get('tool_id', type=int)
    file_type = request.args.get('file_type', '').strip()

    if not tool_id:
        return jsonify({'code': 400, 'msg': '请指定工装ID'})

    query = Attachment.query.filter_by(tool_id=tool_id)

    if file_type:
        query = query.filter_by(file_type=file_type)

    attachments = query.order_by(Attachment.id.desc()).all()

    return jsonify({
        'code': 200,
        'data': [a.to_dict() for a in attachments]
    })


@attachments_bp.route('/upload', methods=['POST'])
@edit_required
def upload():
    """上传附件"""
    tool_id = request.form.get('tool_id', type=int)
    inspection_id = request.form.get('inspection_id', type=int)  # 新增：检定记录ID
    file_type = request.form.get('file_type', '其他')  # 入库资料/检定报告/其他

    if 'file' not in request.files:
        return jsonify({'code': 400, 'msg': '请选择文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'msg': '请选择文件'})

    # 生成唯一文件名，保留原始扩展名
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"

    # 目录策略：优先用 tool_id，其次用 inspection_id，最后用 temp
    if tool_id:
        tool = Tool.query.get(tool_id)
        if not tool:
            return jsonify({'code': 404, 'msg': '工装不存在'})
        base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], tool.code)
    elif inspection_id:
        # 检定附件，存到 inspections 子目录
        base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'inspections', str(inspection_id))
    else:
        # 临时目录
        base_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp')
    
    os.makedirs(base_dir, exist_ok=True)

    file_path = os.path.join(base_dir, unique_name)
    file.save(file_path)

    # 获取文件大小
    file_size = os.path.getsize(file_path)

    # 保存附件记录（tool_id 或 inspection_id 可以为空）
    attachment = Attachment(
        tool_id=tool_id,
        inspection_id=inspection_id,  # 新增
        file_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        uploader=session.get('username', '')
    )

    db.session.add(attachment)
    db.session.commit()

    if tool_id:
        add_log('上传附件', f'工装 {tool.code}，文件 {file.filename}，类型 {file_type}')
    else:
        add_log('上传附件', f'临时上传，文件 {file.filename}，类型 {file_type}')

    return jsonify({'code': 200, 'msg': '上传成功', 'data': attachment.to_dict()})


@attachments_bp.route('/<int:att_id>/download', methods=['GET'])
@login_required
def download(att_id):
    """下载附件"""
    attachment = Attachment.query.get_or_404(att_id)

    if not os.path.exists(attachment.file_path):
        return jsonify({'code': 404, 'msg': '文件不存在'})

    add_log('下载附件', f'文件 {attachment.file_name}')

    return send_file(
        attachment.file_path,
        download_name=attachment.file_name,
        as_attachment=True
    )


@attachments_bp.route('/<int:att_id>', methods=['DELETE'])
@admin_required
def delete_attachment(att_id):
    """删除附件（管理员）"""
    attachment = Attachment.query.get_or_404(att_id)

    add_log('删除附件', f'文件 {attachment.file_name}')

    # 删除物理文件
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.session.delete(attachment)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '删除成功'})

