"""报废申请模型"""

class ScrapRequest(db.Model):
    """报废申请表"""
    __tablename__ = 'scrap_requests'

    id = db.Column(db.Integer, primary_key=True)
    tool_id = db.Column(db.Integer, db.ForeignKey('tools.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, default='')
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
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'reviewed_at': self.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if self.reviewed_at else '',
            'reviewer_name': self.reviewer.username if self.reviewer else '',
            'reject_reason': self.reject_reason or '',
        }
