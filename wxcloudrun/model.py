import json
from datetime import datetime
from wxcloudrun.utils import encrypt, decrypt, masked_view
from wxcloudrun import db
import config


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
    order = db.Column('order', db.Integer, default=0)

    def get(self):
        return {'id': self.id, 'title': self.title, 'org': self.org,
                'file_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.file_url),
                "cdn_param": self.file_url, 'create_time': self.create_time.strftime('%Y-%m-%d'),
                'link_url': self.link_url, "order": self.order}


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
    guest = db.Column('guest', db.TEXT, nullable=True)
    live_status = db.Column('live_status', db.INT, default=0)
    is_deleted = db.Column('is_deleted', db.INT, default=0)
    org = db.Column('org', db.String(100), nullable=True)
    agenda = db.Column('agenda', db.TEXT)
    img_url = db.Column('img_url', db.String(100))
    forum = db.Column('forum', db.String(50), default='')
    sponsor = db.Column('sponsor', db.String(100), default='')
    supported = db.Column('supported', db.String(100), default='')
    organizer = db.Column('organizer', db.String(100), default='')
    coorganizer = db.Column('co-organizer', db.String(100), default='')
    background = db.Column('background', db.TEXT)
    label = db.Column('label', db.String(30), nullable=True)
    order = db.Column('order', db.Integer, default=0)

    def get_live(self):
        status_ENUM = {1: '即将直播', 2: '正在直播', 3: '查看回放'}
        return {'id': self.id, 'title': self.title, 'location': self.location, 'live_time': self.get_live_time(),
                'status': status_ENUM.get(self.live_status), 'live_url': self.live_url, 'record_url': self.record_url,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET,
                                                                self.img_url) if self.img_url is not None else ''}

    def get_live_time(self):
        return self.conference_date.strftime('%Y年%m月%d日') + '(' + WEEKDAY.get(
            self.conference_date.weekday()) + ')' + self.begin_time + '~' + self.end_time

    def get_schedule(self):
        status_ENUM = {0: '我要报名', 1: '正在直播', 2: '会议结束'}
        if self.guest is None or self.guest == '':
            guest_id = []
        else:
            guest_id = list(map(int, self.guest.split(',')))
        if self.sponsor is None or self.sponsor == '':
            sponsor = []
        else:
            sponsor = list(map(int, self.sponsor.split(',')))
        if self.supported is None or self.supported == '':
            supported = []
        else:
            supported = list(map(int, self.supported.split(',')))
        if self.organizer is None or self.organizer == '':
            organizer = []
        else:
            organizer = list(map(int, self.organizer.split(',')))
        if self.coorganizer is None or self.coorganizer == '':
            coorganizer = []
        else:
            coorganizer = list(map(int, self.coorganizer.split(',')))
        return {'id': self.id, 'title': self.title, 'location': self.location, "hall": self.hall,
                'conference_date': self.conference_date.strftime('%Y-%m-%d'), 'status': self.status,
                'live_status': self.live_status, "begin_time": self.begin_time, "end_time": self.end_time,
                'live_url': self.live_url, "record_url": self.record_url, 'guest_id': guest_id, 'org': self.org,
                "agenda": [] if (self.agenda is None or self.agenda == '') else json.loads(self.agenda),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url, "sponsor": sponsor, "supported": supported, "organizer": organizer,
                "coorganizer": coorganizer, "background": self.background, "label": self.label,
                "qrcode_cdn": 'https://{}.tcb.qcloud.la/{}qrcode_schedule_{}.jpg'.format(config.COS_BUCKET,
                                                                                         config.VERSION, self.id)}

    def get_schedule_view(self):
        status_ENUM = {0: '我要报名', 1: '正在直播' if self.live_status == 1 else '会议进行中',
                       2: '查看回放' if self.live_status == 2 else '会议结束', 3: "不可报名"}
        live_status_ENUM = {1: '未开始', 2: '直播中', 3: "回放中"}
        if self.guest is None or self.guest == '':
            guest_id = []
        else:
            guest_id = list(map(int, self.guest.split(',')))
        if self.sponsor is None or self.sponsor == '':
            sponsor = []
        else:
            sponsor = list(map(int, self.sponsor.split(',')))
        return {'id': self.id, 'title': self.title, 'hall': self.location, "location": self.hall, "label": self.label,
                "forum": self.forum, 'conference_date': self.conference_date.strftime('%Y-%m-%d'),
                'status': status_ENUM.get(self.status),
                "begin_time": self.begin_time, "end_time": self.end_time, 'live_url': self.live_url,
                "record_url": self.record_url, 'guest_id': guest_id, 'ext': self.label, "sponsor": sponsor,
                'live_status': live_status_ENUM.get(self.live_status, ''),
                "blockchain_ext": "会议论坛" if self.label in ["开幕式", "分论坛", "分论坛（外场）"] else self.label}

    def get_schedule_view_simple(self):
        status_ENUM = {0: '我要报名', 1: '正在直播' if self.live_status == 1 else '会议进行中',
                       2: '查看回放' if self.live_status == 2 else '会议结束', 3: "不可报名"}
        live_status_ENUM = {1: '未开始', 2: '直播中', 3: "回放中"}
        if self.guest is None or self.guest == '':
            guest_id = []
        else:
            guest_id = list(map(int, self.guest.split(',')))
        if self.sponsor is None or self.sponsor == '':
            sponsor = []
        else:
            sponsor = list(map(int, self.sponsor.split(',')))
        if self.supported is None or self.supported == '':
            supported = []
        else:
            supported = list(map(int, self.supported.split(',')))
        if self.organizer is None or self.organizer == '':
            organizer = []
        else:
            organizer = list(map(int, self.organizer.split(',')))
        if self.coorganizer is None or self.coorganizer == '':
            coorganizer = []
        else:
            coorganizer = list(map(int, self.coorganizer.split(',')))
        return {'id': self.id, 'title': self.title, 'hall': self.location, "location": self.hall,
                'conference_date': self.conference_date.strftime('%Y-%m-%d'),
                "begin_time": self.begin_time, "end_time": self.end_time, 'live_url': self.live_url,
                "record_url": self.record_url, 'ext': self.label,
                "agenda": [] if (self.agenda is None or self.agenda == '') else json.loads(self.agenda),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url), "guest_id": guest_id,
                'status': status_ENUM.get(self.status), 'live_status': live_status_ENUM.get(self.live_status, ''),
                "sponsor": sponsor, "supported": supported, "organizer": organizer, "coorganizer": coorganizer,
                "background": self.background}


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
    reason = db.Column('reason', db.String(100))
    codeEncrypted = db.Column('code_encrypted', db.BINARY)
    phoneEncrypted = db.Column('phone_encrypted', db.BINARY)
    origin_userid = db.Column('origin_user_id', db.INT)
    branch = db.Column('branch', db.INT)
    auto_flag = db.Column('auto_flag', db.INT)

    def get_status(self):
        status_ENUM = {1: '审核未通过', 2: '审核已通过', 0: '未审核', 3: '待审核'}
        return status_ENUM.get(self.status, '审核未通过')

    def savecodeEncrypted(self, data):
        self.codeEncrypted = encrypt(data)

    def savephoneEncrypted(self, data):
        self.phoneEncrypted = encrypt(data)

    def get(self):
        return {"id": self.id, "name": self.name, "company": self.company, "title": self.title,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url), "socail": self.socail}

    def get_full(self):
        return {"id": self.id, "name": self.name, "company": self.company, "title": self.title,
                "phone": decrypt(self.phoneEncrypted) if self.phoneEncrypted else None,
                "code": decrypt(self.codeEncrypted) if self.codeEncrypted else None,
                "type": self.type,
                "socail": self.socail,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET,
                                                                self.img_url) if self.img_url is not None else None,
                'cdn_param': self.img_url, "status": self.status, "reason": self.reason, "guest_id": self.origin_userid}

    def get_guest(self):
        return {"id": self.id, "name": self.name, "company": self.company, "title": self.title, "info": self.guest_info,
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url, 'forum': self.forum, 'order': self.order, "socail": self.socail}


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
    info = db.Column('info', db.String(255), nullable=True)
    is_deleted = db.Column('is_deleted', db.INT, default=0)
    forum = db.Column('forum', db.String)

    def get(self):
        return {"id": self.id, "name": self.name, "cdn_param": self.img_url, "type": self.type, "info": self.info,
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
                    "web_url": 'https://{}.tcb.qcloud.la/{}web/{}'.format(config.COS_BUCKET, config.VERSION, self.id)}
        else:
            return {"id": self.id, "name": self.name, "info": self.info, "type": self.type, "doc": self.media_param,
                    "web_url": 'https://{}.tcb.qcloud.la/{}web/{}'.format(config.COS_BUCKET, config.VERSION, self.id)}


class ConferenceCooperatorShow(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'conference_cooperater_show'
    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(20))
    type = db.Column('type', db.String(20))
    is_show = db.Column('is_show', db.BOOLEAN, default=True)


class OperaterLog(db.Model):
    # 设置结构体表格名称
    __tablename__ = 't_operate_log'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    operator = db.Column('operator', db.String(50), nullable=True)
    event = db.Column('event', db.String(100), nullable=True)
    ip = db.Column('ip', db.String(100), nullable=True)
    data = db.Column('data', db.TEXT)
    create_time = db.Column('create_time', db.TIMESTAMP, nullable=False, default=datetime.now)


class OperaterRule(db.Model):
    # 设置结构体表格名称
    __tablename__ = 't_operate_rule'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    rule = db.Column('rule', db.String(100), nullable=True)
    name = db.Column('name', db.String(100), nullable=True)


class Exhibiton(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'exhibition'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(100), nullable=True)
    hall = db.Column('hall', db.String(50), nullable=True)
    location = db.Column('location', db.String(50), nullable=True)
    status = db.Column('status', db.INT, default=0)
    begin_time = db.Column('begin_time', db.TIMESTAMP, nullable=True)
    end_time = db.Column('end_time', db.TIMESTAMP, nullable=True)
    is_deleted = db.Column('is_deleted', db.INT, default=0)
    participating_unit = db.Column('participating_unit', db.TEXT)
    img_url = db.Column('img_url', db.String(100))
    forum = db.Column('forum', db.String(50), default='')
    sponsor = db.Column('sponsor', db.String(100), default='')
    supported = db.Column('supported', db.String(100), default='')
    organizer = db.Column('organizer', db.String(100), default='')
    coorganizer = db.Column('co-organizer', db.String(100), default='')
    info = db.Column('info', db.TEXT)
    label = db.Column('label', db.String(30), nullable=True)
    district = db.Column('district', db.String(255), nullable=True)

    def get(self):
        if self.sponsor is None or self.sponsor == '':
            sponsor = []
        else:
            sponsor = list(map(int, self.sponsor.split(',')))
        if self.supported is None or self.supported == '':
            supported = []
        else:
            supported = list(map(int, self.supported.split(',')))
        if self.organizer is None or self.organizer == '':
            organizer = []
        else:
            organizer = list(map(int, self.organizer.split(',')))
        if self.coorganizer is None or self.coorganizer == '':
            coorganizer = []
        else:
            coorganizer = list(map(int, self.coorganizer.split(',')))
        return {'id': self.id, 'title': self.title, 'location': self.location, "hall": self.hall,
                'status': self.status,
                "begin_time": self.begin_time.strftime('%Y-%m-%d %H:%M'),
                "end_time": self.end_time.strftime('%Y-%m-%d %H:%M'), "district": self.district,
                "participating_unit": [] if (
                        self.participating_unit is None or self.participating_unit == '') else json.loads(
                    self.participating_unit),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url, "sponsor": sponsor, "supported": supported, "organizer": organizer,
                "coorganizer": coorganizer, "info": self.info, "label": self.label}

    def get_view_simple(self):
        status_ENUM = {0: '我要报名', 1: '会议进行中', 2: '会议结束', 3: "不可报名"}
        if self.sponsor is None or self.sponsor == '':
            sponsor = []
        else:
            sponsor = list(map(int, self.sponsor.split(',')))
        if self.supported is None or self.supported == '':
            supported = []
        else:
            supported = list(map(int, self.supported.split(',')))
        if self.organizer is None or self.organizer == '':
            organizer = []
        else:
            organizer = list(map(int, self.organizer.split(',')))
        if self.coorganizer is None or self.coorganizer == '':
            coorganizer = []
        else:
            coorganizer = list(map(int, self.coorganizer.split(',')))
        return {'id': self.id, 'title': self.title, 'hall': self.location, "location": self.hall,
                'status': status_ENUM.get(self.status), "district": self.district,
                "begin_time": self.begin_time.strftime('%Y-%m-%d %H:%M'),
                "end_time": self.end_time.strftime('%Y-%m-%d %H:%M'),
                "participating_unit": [] if (
                        self.participating_unit is None or self.participating_unit == '') else json.loads(
                    self.participating_unit),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url, "sponsor": sponsor, "supported": supported, "organizer": organizer,
                "coorganizer": coorganizer, "info": self.info, "label": self.label}

    def get_blockview_simple(self):
        status_ENUM = {0: '我要报名', 1: '会议进行中', 2: '会议结束', 3: "不可报名"}
        if self.sponsor is None or self.sponsor == '':
            sponsor = []
        else:
            sponsor = list(map(int, self.sponsor.split(',')))
        if self.supported is None or self.supported == '':
            supported = []
        else:
            supported = list(map(int, self.supported.split(',')))
        if self.organizer is None or self.organizer == '':
            organizer = []
        else:
            organizer = list(map(int, self.organizer.split(',')))
        if self.coorganizer is None or self.coorganizer == '':
            coorganizer = []
        else:
            coorganizer = list(map(int, self.coorganizer.split(',')))
        return {'id': self.id, 'title': self.title, 'hall': self.location, "location": self.hall,
                'status': status_ENUM.get(self.status), "district": self.district,
                'conference_date': self.begin_time.strftime('%Y-%m-%d'),
                "begin_time": self.begin_time.strftime('%H:%M'),
                "end_time": self.end_time.strftime('%H:%M'),
                "participating_unit": [] if (
                        self.participating_unit is None or self.participating_unit == '') else json.loads(
                    self.participating_unit),
                "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, self.img_url),
                'cdn_param': self.img_url, "sponsor": sponsor, "supported": supported, "organizer": organizer,
                "coorganizer": coorganizer, "info": self.info, "label": self.label, "blockchain_ext": self.district}


class DigitalCityWeek(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'digital_city_week'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(100), nullable=True)
    dept = db.Column('dept', db.String(30), nullable=True)
    location = db.Column('location', db.String(255), nullable=True)
    activity_time = db.Column('activity_time', db.TEXT, nullable=True)
    contact = db.Column('contact', db.String(255), nullable=True)
    info = db.Column('info', db.TEXT, nullable=True)
    url = db.Column('url', db.String(255), nullable=True)
    slogan = db.Column('slogan', db.String(255), nullable=True)
    order = db.Column('order', db.Integer, nullable=True)

    def get(self):
        return {"title": self.title, "dept": self.dept, "location": self.location, "activity_time": self.activity_time,
                "contact": self.contact, "info": self.info, "url": self.url, "slogan": self.slogan}


class BusinessInfo(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'business_info'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column('title', db.String(50), nullable=True)
    company = db.Column('company', db.String(50), nullable=True)
    type = db.Column('type', db.String(20), nullable=True)
    project_info = db.Column('project_info', db.TEXT, nullable=True)
    demand = db.Column('demand', db.String(20), nullable=True)
    status = db.Column('status', db.INT, nullable=True,default=0)
    team_info = db.Column('team_info', db.TEXT, nullable=True)
    creater_userid = db.Column('creater_userid', db.Integer, nullable=True)
    is_deleted = db.Column('is_deleted', db.Integer, nullable=True, default=0)
    create_time = db.Column('create_time', db.DateTime, nullable=True, default=datetime.now)

    def get(self):
        return {"id": self.id, "title": self.title, "company": self.company, "type": self.type,
                "project_info": self.project_info, "demand": self.demand, "status": self.status,
                "team_info": self.team_info, "creater_userid": self.creater_userid, "is_deleted": self.is_deleted,
                "create_time": self.create_time.strftime('%Y-%m-%d'), "chat_object_type": "项目"}


class EnterpriseCertified(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'enterprise_certified'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String(50), nullable=True)
    code = db.Column('code', db.String(50), nullable=True)
    file_url = db.Column('file', db.String(100), nullable=True)
    scale = db.Column('scale', db.String(50), nullable=True)
    industry = db.Column('industry', db.String(50), nullable=True)
    area = db.Column('area', db.String(100), nullable=True)
    financing_stage = db.Column('financing_stage', db.String(50), nullable=True)
    result = db.Column('result', db.TEXT, nullable=True)
    user_id = db.Column('user_id', db.Integer, nullable=True)
    status = db.Column('status', db.Integer, nullable=True, default=0)
    is_deleted = db.Column('is_deleted', db.Integer, nullable=True, default=0)
    create_time = db.Column('create_time', db.DateTime, nullable=True, default=datetime.now)

    def get(self):
        return {"id": self.id, "name": self.name, "code": self.code, "file_url": self.file_url, "scale": self.scale,
                "industry": self.industry, "area": self.area, "financing_stage": self.financing_stage,
                "result": self.result, "user_id": self.user_id, "status": self.status, "is_deleted": self.is_deleted,
                "create_time": self.create_time.strftime('%Y-%m-%d'), "chat_object_type": "企业"
                }


class BusinessNegotiation(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'business_negotiation'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    chat_object_id = db.Column('chat_object_id', db.Integer, nullable=True)
    chat_object_type = db.Column('chat_object_type', db.String(50), nullable=True)
    chat_object_name = db.Column('chat_object_name', db.String(100), nullable=True)
    creater_userid = db.Column('creater_userid', db.Integer, nullable=True)
    negotation_userid = db.Column('negotiation_userid', db.Integer, nullable=True)
    negotation_intention = db.Column('negotiation_intention', db.String(300), nullable=True)
    status = db.Column('status', db.INT, nullable=True, default=0)
    is_deleted = db.Column('is_deleted', db.Integer, nullable=True, default=0)
    create_time = db.Column('create_time', db.DateTime, nullable=True, default=datetime.now)

    def get(self,visit=True):
        if visit:
            status_ENUM = {0: "待审核", 1: "审核不通过", 2: "审核通过"}
        else:
            status_ENUM = {0: "待通过", 1: "已拒绝", 2: "已同意"}
        return {"id": self.id, "chat_object_id": self.chat_object_id, "chat_object_type": self.chat_object_type,
                "chat_object_name": self.chat_object_name, "creater_userid": self.creater_userid,
                "negotation_userid": self.negotation_userid, "negotation_intention": self.negotation_intention,
                "status": self.status, "status_info": status_ENUM.get(self.status),
                "create_time": self.create_time.strftime('%Y-%m-%d')
                }


class MeetingRoom(db.Model):
    # 设置结构体表格名称
    __tablename__ = 't_meeting_room'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column('location', db.String(100), nullable=True)
    name = db.Column('name', db.String(100), nullable=True)

    def get(self):
        return {"id": self.id, "location": self.location, "name": self.name}


class MeetingReservation(db.Model):
    # 设置结构体表格名称
    __tablename__ = 't_meeting_reservation'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    meeting_room_id = db.Column('meeting_room_id', db.INT, nullable=True)
    is_deleted = db.Column('is_deleted', db.Integer, nullable=True, default=0)
    start_time = db.Column('start_time', db.DateTime, nullable=True)
    end_time = db.Column('end_time', db.DateTime, nullable=True)