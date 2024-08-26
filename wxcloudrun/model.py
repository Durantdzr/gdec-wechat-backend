import json
from datetime import datetime

from wxcloudrun import db
import config


# 计数表
class ConferenceInfo(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_information'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(100), nullable=True)
    org = db.Column('org', db.String(50), nullable=True)
    create_time = db.Column('create_time', db.TIMESTAMP, nullable=False, default=datetime.now)
    file_url = db.Column('file_url', db.TEXT)
    link_url = db.Column('link_url', db.TEXT)
    is_deleted = db.Column('is_deleted', db.INT, default=0)

    def get(self):
        return {'id': self.id, 'title': self.title, 'org': self.org,
                'file_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.file_url),
                "cdn_param": self.file_url, 'create_time': self.create_time.strftime('%Y-%m-%d'),
                'link_url': self.link_url}


WEEKDAY = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}


class ConferenceSchedule(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_schedule'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(100), nullable=True)
    hall = db.Column('hall', db.String(50), nullable=True)
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
    org = db.Column('org', db.String(100), nullable=True)
    agenda = db.Column('agenda', db.TEXT)
    img_url = db.Column('img_url', db.String(100))
    forum = db.Column('forum', db.String(50), default='')

    def get_live(self):
        status_ENUM = {1: '即将直播', 2: '正在直播', 3: '查看回放'}
        return {'id': self.id, 'title': self.title, 'location': self.location, 'live_time': self.get_live_time(),
                'status': status_ENUM.get(self.live_status), 'live_url': self.live_url, 'record_url': self.record_url}

    def get_live_time(self):
        return self.conference_date.strftime('%Y年%m月%d日') + '(' + WEEKDAY.get(
            self.conference_date.weekday()) + ')' + self.begin_time + '~' + self.end_time

    def get_schedule(self):
        status_ENUM = {0: '我要报名', 1: '正在直播', 2: '会议结束'}
        if self.guest is None:
            guest_id = []
        else:
            guest_id = list(map(int, self.guest.split(',')))
        return {'id': self.id, 'title': self.title, 'location': self.location, "hall": self.hall,
                'conference_date': self.conference_date.strftime('%Y-%m-%d'), 'status': self.status,
                'live_status': self.live_status, "begin_time": self.begin_time, "end_time": self.end_time,
                'live_url': self.live_url, "record_url": self.record_url, 'guest_id': guest_id, 'org': self.org,
                "agenda": [] if (self.agenda is None or self.agenda == '') else json.loads(self.agenda),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url}

    def get_schedule_view(self):
        status_ENUM = {0: '我要报名', 1: '正在直播' if self.live_status == 1 else '会议进行中',
                       2: '查看回放' if self.live_status == 2 else '会议结束'}
        live_status_ENUM = {1: '未开始', 2: '直播中', 3: "回放中"}
        if self.guest is None:
            guest_id = []
        else:
            guest_id = list(map(int, self.guest.split(',')))
        if '开幕式' in self.title:
            ext = '开幕式'
        elif '主会场' in self.hall:
            ext = '主论坛'
        else:
            ext = ''
        return {'id': self.id, 'title': self.title, 'location': self.location, "hall": self.hall,
                'conference_date': self.conference_date.strftime('%Y-%m-%d'), 'status': status_ENUM.get(self.status),
                "begin_time": self.begin_time, "end_time": self.end_time, 'live_url': self.live_url,
                "record_url": self.record_url, 'guest_id': guest_id, 'ext': ext,
                'live_status': live_status_ENUM.get(self.live_status, '')}

    def get_schedule_view_simple(self):
        if '开幕式' in self.title:
            ext = '开幕式'
        elif '主会场' in self.hall:
            ext = '主论坛'
        else:
            ext = ''
        return {'id': self.id, 'title': self.title, 'location': self.location,
                'conference_date': self.conference_date.strftime('%Y-%m-%d'),
                "begin_time": self.begin_time, "end_time": self.end_time, 'live_url': self.live_url,
                "record_url": self.record_url, 'ext': ext,
                "agenda": [] if (self.agenda is None or self.agenda == '') else json.loads(self.agenda),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url)}


class ConferenceHall(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_hall'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(50), nullable=True)


class User(db.Model):
    # 设置结构体表格名称
    __tablename__ = 't_user'
    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(100), nullable=True)
    openid = db.Column('openid', db.String(50), nullable=True)
    phone = db.Column('phone', db.String(20), nullable=True)
    code = db.Column('code', db.String(50), nullable=True)
    company = db.Column('company', db.String(100), nullable=True)
    title = db.Column('title', db.String(255), nullable=True)
    type = db.Column('type', db.String(10), default='普通观众')
    socail = db.Column('socail', db.INT, default=0)
    is_deleted = db.Column('is_deleted', db.INT, default=0)
    img_url = db.Column('img_url', db.TEXT)
    status = db.Column('status', db.INT, default=0)
    password = db.Column('pwd', db.String(50), nullable=True)
    guest_info = db.Column('guest_info', db.TEXT)
    order = db.Column('order', db.Integer, default=0)
    forum = db.Column('forum', db.String)

    def get_status(self):
        status_ENUM = {1: '审核未通过', 2: '审核已通过', 0: '未审核', 3: '待审核'}
        return status_ENUM.get(self.status, '审核未通过')

    def get(self):
        return {"id": self.id, "name": self.name, "company": self.company, "title": self.title,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url)}

    def get_full(self):
        return {"id": self.id, "name": self.name, "company": self.company, "title": self.title, "phone": self.phone,
                "code": self.code, "type": self.type, "socail": self.socail,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET,
                                                                self.img_url) if self.img_url is not None else None,
                'cdn_param': self.img_url}

    def get_guest(self):
        return {"id": self.id, "name": self.name, "company": self.company, "title": self.title, "info": self.guest_info,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url, 'forum': self.forum, 'order': self.order}


class RelationFriend(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'r_user_friend'
    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    operater_id = db.Column('operater_id', db.Integer)
    inviter_id = db.Column('inviter_id', db.Integer)
    meeting_date = db.Column('meeting_date', db.TIMESTAMP, nullable=True)
    create_time = db.Column('create_time', db.TIMESTAMP, nullable=True, default=datetime.now)
    visit_info = db.Column('visit_info', db.String(100), nullable=True)
    is_deleted = db.Column('is_deleted', db.INT, default=0)
    status = db.Column('status', db.INT, default=0)


class ConferenCoopearter(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_coopearter'
    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(30), nullable=True)
    img_url = db.Column('img_url', db.String(100), nullable=True)
    url = db.Column('url', db.String(50), nullable=True)
    type = db.Column('type', db.String(10), nullable=True)
    is_deleted = db.Column('is_deleted', db.INT, default=0)

    def get(self):
        return {"id": self.id, "name": self.name, "cdn_param": self.img_url, "type": self.type,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url), "url": self.url}


class ConferenceSignUp(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_sign_up'
    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column('user_id', db.Integer)
    schedule_id = db.Column('schedule_id', db.Integer)
    status = db.Column('status', db.Integer, default=0)


class Media(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'manage_media'
    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(50), nullable=True)
    info = db.Column('info', db.String(100), nullable=True)
    type = db.Column('type', db.String(10), nullable=True)
    media_param = db.Column('media_param', db.TEXT, nullable=True)
    is_deleted = db.Column('is_deleted', db.INT, default=0)

    def get(self):
        if self.type == '图片':
            return {"id": self.id, "name": self.name, "info": self.info, "type": self.type,
                    "cdn_param": self.media_param,
                    "web_url": 'https://{}.tcb.qcloud.la/web/{}'.format(config.COS_BUCKET, self.id)}
        else:
            return {"id": self.id, "name": self.name, "info": self.info, "type": self.type, "doc": self.media_param,
                    "web_url": 'https://{}.tcb.qcloud.la/web/{}'.format(config.COS_BUCKET, self.id)}
