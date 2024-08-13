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
        return {'id': self.id, 'title': self.title, 'org': self.org,
                'create_time': self.create_time.strftime('%Y-%m-%d')}


WEEKDAY = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}


class ConferenceSchedule(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_schedule'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(100), nullable=True)
    location = db.Column('location', db.String(50), nullable=True)
    conference_date = db.Column('conference_date', db.TIMESTAMP, nullable=True)
    status = db.Column('status', db.INT, default=0)
    live_url = db.Column('live_url', db.String(128), nullable=True)
    record_url = db.Column('record_url', db.String(128), nullable=True)
    begin_time = db.Column('begin_time', db.String(10), nullable=True)
    end_time = db.Column('end_time', db.String(10), nullable=True)
    guest = db.Column('guest', db.String(100), nullable=True)
    live_status = db.Column('live_status', db.INT, default=0)
    is_deleted = db.Column('is_deleted', db.INT, default=0)




    def get_live(self):
        status_ENUM = {1: '即将直播', 2: '正在直播', 3: '会议结束'}
        return {'id': self.id, 'title': self.title, 'location': self.location, 'live_time': self.get_live_time(),
                'status': status_ENUM.get(self.live_status), 'live_url': self.live_url, 'record_url': self.record_url}

    def get_live_time(self):
        return self.conference_date.strftime('%Y年%m月%d日') + '(' + WEEKDAY.get(
            self.conference_date.weekday()) + ')' + self.begin_time + '~' + self.end_time
