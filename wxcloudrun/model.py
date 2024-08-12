from datetime import datetime

from wxcloudrun import db


# 计数表
class ConferenceInfo(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_information'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(100), nullable=True)
    org = db.Column('org', db.String(50), nullable=True)
    create_time = db.Column('create_time', db.TIMESTAMP, nullable=False, default=datetime.now)

    def get(self):
        return {'id': self.id, 'title': self.title, 'org': self.org, 'create_time': self.create_time.strftime('%Y-%m-%d')}
