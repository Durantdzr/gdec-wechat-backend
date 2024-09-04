import datetime
import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import ConferenceInfo, RelationFriend, User, ConferenceSignUp, ConferenceSchedule, \
    ConferenCoopearter, ConferenceCooperatorShow
from sqlalchemy import or_
from wxcloudrun.utils import uploadwebfile, send_check_msg
import config

# 初始化日志
logger = logging.getLogger('log')


def insert_user(user):
    """
    插入一个User实体
    :param counter: User实体
    """
    try:
        db.session.add(user)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def delete_reocrd(user):
    """
    插入一个User实体
    :param counter: User实体
    """
    try:
        db.session.delete(user)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def search_friends_byopenid(openid, name):
    user = User.query.filter(User.openid == openid).first()
    user_id = user.id
    friends = RelationFriend.query.filter(
        or_(RelationFriend.operater_id == user_id, RelationFriend.inviter_id == user_id),
        RelationFriend.is_deleted == 0).all()
    friend_list = [user_id]
    for friend in friends:
        friend_list.append(friend.operater_id)
        friend_list.append(friend.inviter_id)
    socail_user = User.query.filter(or_(User.name.like('%' + name + '%'), User.company.like('%' + name + '%')),
                                    User.status == 2, User.is_deleted == 0,
                                    User.socail == 1, ~User.id.in_(friend_list)).all()
    return socail_user


def get_friend_list(openid, name):
    user = User.query.filter(User.openid == openid).first()
    user_id = user.id
    data = []
    operator_friends = db.session.query(RelationFriend, User).join(User, User.id == RelationFriend.inviter_id).filter(
        or_(User.name.like('%' + name + '%'), User.company.like('%' + name + '%')),
        RelationFriend.operater_id == user_id, RelationFriend.is_deleted == 0).all()
    status_ENUM = {0: '已邀请', 1: '已添加'}
    for relation, user in operator_friends:
        data.append(
            {"name": user.name, "id": user.id, "company": user.company, "title": user.title, "phone": user.phone,
             "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url),
             "visit_info": relation.visit_info,
             "status": status_ENUM.get(relation.status), "relation_id": relation.id})
    invited_friends = db.session.query(RelationFriend, User).join(User, User.id == RelationFriend.operater_id).filter(
        or_(User.name.like('%' + name + '%'), User.company.like('%' + name + '%')),
        RelationFriend.inviter_id == user_id, RelationFriend.is_deleted == 0).all()
    status_ENUM = {0: '接受邀请', 1: '已添加'}
    for relation, user in invited_friends:
        data.append(
            {"name": user.name, "id": user.id, "company": user.company, "title": user.title, "phone": user.phone,
             "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url),
             "visit_info": relation.visit_info,
             "status": status_ENUM.get(relation.status), "relation_id": relation.id})
    return data


def insert_realtion_friend(relation):
    """
    插入一个User实体
    :param counter: User实体
    """
    try:
        db.session.add(relation)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def save_realtion_friendbyid(id):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        record = RelationFriend.query.filter(RelationFriend.id == id).first()
        record.status = 1
        db.session.commit()
        return record.id
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def is_invited_user(relation_id, wxopenid):
    result = db.session.query(RelationFriend, User).join(User, User.id == RelationFriend.inviter_id).filter(
        User.openid == wxopenid, RelationFriend.id == relation_id).all()
    if len(result) > 0:
        return True
    else:
        return False


def update_user_statusbyid(userlist, status, reason):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        records = User.query.filter(User.id.in_(userlist)).all()
        status_ENUM = {1: "审核未通过", 2: "审核通过"}
        for record in records:
            send_check_msg(openid=record.openid, meetingname='全球数商大会', content=record.name + '用户报名审核',
                           reason=reason,
                           phrase3=status_ENUM.get(status), date=datetime.datetime.now().strftime('%Y-%m-%d'))
            record.status = status
            record.reason = reason
        db.session.commit()
        return True
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def update_schedule_statusbyid(signuplist, status):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        records = ConferenceSignUp.query.filter(ConferenceSignUp.id.in_(signuplist)).all()
        for record in records:
            record.status = status
        db.session.commit()
        return True
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def get_guests_list():
    guests = User.query.filter(User.type == '嘉宾', User.is_deleted == 0).order_by(
        User.order.desc()).all()
    data = [guest.get_guest() for guest in guests]
    return data


def get_open_guests_list():
    schedule = ConferenceSchedule.query.filter(ConferenceSchedule.title.like('%开幕式%')).first()
    guest_id = schedule.guest.split(',')
    guests = User.query.filter(User.id.in_(guest_id)).order_by(
        User.order.desc()).all()
    data = [guest.get_guest() for guest in guests]
    return data


def get_main_hall_guests_list():
    schedules = ConferenceSchedule.query.filter(ConferenceSchedule.hall == '主会场·城市规划与公共艺术中心',
                                                ConferenceSchedule.is_deleted == 0).all()
    guest_id = []
    for schedule in schedules:
        if schedule.guest is None:
            continue
        guest_id.extend(schedule.guest.split(','))
    guests = User.query.filter(User.id.in_(guest_id)).order_by(
        User.order.desc()).all()
    data = [guest.get_guest() for guest in guests]
    return data


def get_other_hall_guests_list():
    schedules = ConferenceSchedule.query.filter(ConferenceSchedule.hall != '主会场·城市规划与公共艺术中心',
                                                ConferenceSchedule.is_deleted == 0).all()
    guest_id = []
    for schedule in schedules:
        if schedule.guest is None:
            continue
        guest_id.extend(schedule.guest.split(','))
    guests = User.query.filter(User.id.in_(guest_id)).order_by(
        User.order.desc()).all()
    data = [guest.get_guest() for guest in guests]
    return data


def get_review_conference_list(name, page, page_size, forum, status):
    if status is None:
        result = db.session.query(ConferenceSignUp, User, ConferenceSchedule).join(User,
                                                                                   User.id == ConferenceSignUp.user_id).join(
            ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
            User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                                              ConferenceSchedule.is_deleted == 0,
            ConferenceSchedule.forum.like('%' + forum + '%')).paginate(page, per_page=page_size,
                                                                       error_out=False)
    else:
        result = db.session.query(ConferenceSignUp, User, ConferenceSchedule).join(User,
                                                                                   User.id == ConferenceSignUp.user_id).join(
            ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
            User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                                              ConferenceSchedule.is_deleted == 0,
                                              ConferenceSignUp.status == status,
            ConferenceSchedule.forum.like('%' + forum + '%')).paginate(page, per_page=page_size,
                                                                       error_out=False)
    return [{"id": signup.id, "user_name": user.name, "schedule_name": schedule.title,
             "schedule_date": schedule.conference_date.strftime('%Y-%m-%d'), "begin_time": schedule.begin_time,
             "end_time": schedule.end_time, "phone": user.phone, "status": signup.status} for signup, user, schedule in
            result.items], result.total


def get_conference_schedule_by_id(userid):
    signup_status_ENUM = {0: '等待审核', 1: '审核未通过', 2: '审核通过'}
    result = db.session.query(ConferenceSignUp, ConferenceSchedule).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSignUp.user_id == userid).all()
    data = []
    for signup, schedule in result:
        delta = (datetime.datetime.strptime(
            schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
            "%Y-%m-%d %H:%M") - datetime.datetime.now()).total_seconds()
        data.append({"id": schedule.id, "schedule_name": schedule.title,
                     "schedule_time": schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
                     "status": signup_status_ENUM.get(signup.status),
                     'info': '距开始还有1小时' if delta / 60 > 0 and delta / 60 < 120 else ''})
    return data


def get_user_schedule_num_by_id(userid):
    result = db.session.query(ConferenceSignUp, ConferenceSchedule).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSignUp.user_id == userid).all()
    num = 0
    for signup, schedule in result:
        delta = (datetime.datetime.strptime(
            schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
            "%Y-%m-%d %H:%M") - datetime.datetime.now()).total_seconds()
        if delta / 60 > 0 and delta / 60 < 120:
            num += 1
    return num


def find_user_schedule_tobegin():
    result = db.session.query(ConferenceSignUp, ConferenceSchedule, User).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id,
                            ConferenceSignUp.user_id == User.id).filter(
        ConferenceSchedule.is_deleted == 0).all()
    data = []
    for signup, schedule, user in result:
        delta = (datetime.datetime.strptime(
            schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
            "%Y-%m-%d %H:%M") - datetime.datetime.now()).total_seconds()
        if delta / 60 > 0 and delta / 60 < 120:
            data.append({"openid": user.openid, "title": schedule.title, "location": schedule.location,
                         "begin_time": schedule.begin_time})
    return data


def get_hall_schedule_bydate(date):
    result = ConferenceSchedule.query.filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSchedule.conference_date == date).order_by(
        ConferenceSchedule.begin_time.asc()).all()
    data = []
    for item in result:
        schedule = item.get_schedule_view()
        schedule['guest_img'] = []
        if len(schedule.get('guest_id', [])) > 0:
            for guest in schedule.get('guest_id', []):
                user = User.query.filter_by(id=guest, is_deleted=0).first()
                if user is None:
                    continue
                schedule['guest_img'].append('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url))
        data.append(schedule)
    return data


def get_hall_schedule_byid(id):
    result = ConferenceSchedule.query.filter(ConferenceSchedule.id == id).first()
    schedule = result.get_schedule_view_simple()
    schedule['guest_info'] = []
    schedule['sponsor_info'] = []
    schedule['supported_info'] = []
    schedule['organizer_info'] = []
    schedule['coorganizer_info'] = []
    if len(schedule.get('guest_id', [])) > 0:
        for guest in schedule.get('guest_id', []):
            user = User.query.filter_by(id=guest, is_deleted=0).first()
            if user is None:
                continue
            schedule['guest_info'].append(user.get())
    if len(schedule.get('supported', [])) > 0:
        supporteds = ConferenCoopearter.query.filter(ConferenCoopearter.id.in_(schedule.get('supported', [])),
                                                     ConferenCoopearter.is_deleted == 0).all()
        if supporteds is not None:
            for supported in supporteds:
                schedule['supported_info'].append(supported.get())
    if len(schedule.get('organizer', [])) > 0:
        organizers = ConferenCoopearter.query.filter(ConferenCoopearter.id.in_(schedule.get('organizer', [])),
                                                     ConferenCoopearter.is_deleted == 0).all()
        if organizers is not None:
            for organizer in organizers:
                schedule['organizer_info'].append(organizer.get())
    if len(schedule.get('coorganizer', [])) > 0:
        coorganizers = ConferenCoopearter.query.filter(ConferenCoopearter.id.in_(schedule.get('coorganizer', [])),
                                                       ConferenCoopearter.is_deleted == 0).all()
        if coorganizers is not None:
            for coorganizer in coorganizers:
                schedule['coorganizer_info'].append(coorganizer.get())
    if len(schedule.get('sponsor', [])) > 0:
        sponsors = ConferenCoopearter.query.filter(ConferenCoopearter.id.in_(schedule.get('sponsor', [])),
                                                   ConferenCoopearter.is_deleted == 0).all()
        if sponsors is not None:
            for sponsor in sponsors:
                schedule['sponsor_info'].append(sponsor.get())
    return schedule


def get_cooperater_list(type):
    result = ConferenCoopearter.query.filter(ConferenCoopearter.type == type,
                                             ConferenCoopearter.is_deleted == 0).all()
    return [item.get() for item in result]


def get_live_data():
    result = ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted == 0,
                                             ConferenceSchedule.live_status > 0).order_by(
        ConferenceSchedule.conference_date.asc(), ConferenceSchedule.begin_time.asc()).all()
    return [item.get_live() for item in result]


def get_cooperater():
    showType = ConferenceCooperatorShow.query.filter(ConferenceCooperatorShow.is_deleted == True).all()
    type = [show.type for show in showType]
    schedules = ConferenceSchedule.query.filter(ConferenCoopearter.is_deleted == 0).all()
    cooperater_id = []
    for schedule in schedules:
        result = schedule.get_schedule()
        for item in type:
            cooperater_id.extend(result.get(item))
    result = ConferenceSchedule.query.filter(ConferenCoopearter.is_deleted == 0,
                                             ConferenCoopearter.id.in_(cooperater_id)).all()
    return [item.get() for item in result]


def refresh_cooperater():
    data = get_cooperater()
    uploadwebfile(data, file='get_cooperater.json')
    data = get_cooperater_list('合作媒体')
    uploadwebfile(data, file='get_comedia.json')


def refresh_guest():
    data = get_guests_list()
    uploadwebfile(data, file='get_guest_list.json')
    data = get_open_guests_list()
    uploadwebfile(data, file='get_open_guest_list.json')
    data = get_main_hall_guests_list()
    uploadwebfile(data, file='get_main_hall_guest_list.json')
    data = get_other_hall_guests_list()
    uploadwebfile(data, file='get_other_hall_guest_list.json')


def refresh_guest_info(userid):
    guest = User.query.filter(User.id == userid).first()
    uploadwebfile(guest.get_guest(), file='web/guest/' + str(guest.id) + '.json')


def refresh_conference_info():
    result = ConferenceInfo.query.filter(ConferenceInfo.is_deleted == 0).all()
    data = [item.get() for item in result]
    uploadwebfile(data, file='get_information_list.json')


def refresh_schedule_info():
    schedules = ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted == 0).all()
    for schedule in schedules:
        uploadwebfile(schedule.get_schedule_view_simple(),
                      file='get_schedule_by_id' + str(schedule.id) + '.json')
