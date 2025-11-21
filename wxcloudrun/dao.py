import datetime
import logging

from sqlalchemy.exc import OperationalError
from sqlalchemy import func
from sqlalchemy.orm import aliased
from wxcloudrun import db
from wxcloudrun.model import ConferenceInfo, RelationFriend, User, ConferenceSignUp, ConferenceSchedule, \
    ConferenCoopearter, ConferenceCooperatorShow, OperaterLog, OperaterRule, Exhibiton, BusinessInfo, \
    EnterpriseCertified, MeetingReservation, MeetingRoom
from sqlalchemy import or_, and_
from wxcloudrun.utils import uploadwebfile, send_check_msg, masked_view
import config
import time

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
    schedules = ConferenceSchedule.query.filter(ConferenceSchedule.title.like('%' + name + '%'),
                                                ConferenceSchedule.is_deleted == 0).all()
    guest = []
    schedule_id = []
    for item in schedules:
        schedule = item.get_schedule()
        guest.extend(schedule.get('guest_id', []))
        schedule_id.append(schedule.get('id'))
    user_id = []
    sign_up = ConferenceSignUp.query.filter(ConferenceSignUp.schedule_id.in_(schedule_id),
                                            ConferenceSignUp.status == 2).all()
    for item in sign_up:
        user_id.append(item.user_id)
    socail_user = User.query.filter(
        or_(User.name.like('%' + name + '%'), User.company.like('%' + name + '%'), User.origin_userid.in_(guest),
            User.id.in_(user_id)),
        User.status == 2, User.is_deleted == 0, ~User.type.in_(['嘉宾', '管理员']),
        User.socail == 1, ~User.id.in_(friend_list)).all()
    return socail_user


def search_friends_random(openid):
    user = User.query.filter(User.openid == openid).first()
    user_id = user.id
    friends = RelationFriend.query.filter(
        or_(RelationFriend.operater_id == user_id, RelationFriend.inviter_id == user_id),
        RelationFriend.is_deleted == 0).all()
    friend_list = [user_id]
    for friend in friends:
        friend_list.append(friend.operater_id)
        friend_list.append(friend.inviter_id)
    socail_user = User.query.filter(User.status == 2, User.is_deleted == 0, ~User.type.in_(['嘉宾', '管理员']),
                                    User.socail == 1, ~User.id.in_(friend_list)).order_by(func.random()).limit(5)
    return socail_user


def is_friend(user_id, friend_id):
    r_friend = RelationFriend.query.filter(RelationFriend.is_deleted == 0,
                                           or_(and_(RelationFriend.operater_id == user_id,
                                                    RelationFriend.inviter_id == friend_id),
                                               and_(RelationFriend.operater_id == friend_id,
                                                    RelationFriend.inviter_id == user_id))).first()
    if r_friend:
        return True
    else:
        return False


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
            # if status == 2:
            #     record.identity_verification = 1001
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


def update_schedule_seatbyid(signuplist, seat, seat_region,seat_row):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        records = ConferenceSignUp.query.filter(ConferenceSignUp.id.in_(signuplist)).all()
        for record in records:
            record.seat_info = seat
            record.seat_region = seat_region
            record.seat_row = seat_row
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


def get_review_conference_list(name, page, page_size, forum, status, schedule_name):
    query = db.session.query(ConferenceSignUp, User, ConferenceSchedule).join(
        User, User.id == ConferenceSignUp.user_id
    ).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id
    ).filter(
        User.name.like('%' + name + '%'),
        User.status == 2,
        User.is_deleted == 0,
        ConferenceSchedule.is_deleted == 0,
        ConferenceSchedule.forum.like('%' + forum + '%'),
        ConferenceSignUp.is_deleted == 0
    )

    if status is not None:
        query = query.filter(ConferenceSignUp.status == status)
    if schedule_name is not None:
        query = query.filter(ConferenceSchedule.title.like('%' + schedule_name + '%'))

    result = query.paginate(page, per_page=page_size, error_out=False)
    return [{"id": signup.id, "user_name": user.name, "schedule_name": schedule.title,
             "schedule_date": schedule.conference_date.strftime('%Y-%m-%d'), "begin_time": schedule.begin_time,
             "label": schedule.label, "type": user.type,
             "end_time": schedule.end_time, "phone": user.phone, "status": signup.status, "company": user.company,
             "seat_img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, schedule.seat_img),
             "title": user.title, "seat_info": signup.seat_info, "seat_region": signup.seat_region,
             "seat_type": signup.type} for signup, user, schedule in
            result.items], result.total


def get_review_conference_listBYlabel(userid, label, schedule_id):
    query = db.session.query(ConferenceSignUp, User, ConferenceSchedule).join(
        User, User.id == ConferenceSignUp.user_id
    ).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id
    ).filter(
        User.id == userid,
        User.is_deleted == 0,
        ConferenceSchedule.is_deleted == 0,
    )

    if label is not None:
        query = query.filter(ConferenceSchedule.label.in_(label))
    if schedule_id is not None:
        query = query.filter(ConferenceSchedule.id == schedule_id)
    result = query.all()
    data = []
    for signup, user, schedule in result:
        # 拼接座位信息
        seat_parts = []
        if signup.seat_region and signup.seat_region.strip():
            seat_parts.append(f"{signup.seat_region}区")
        if signup.seat_row and signup.seat_row.strip():
            seat_parts.append(f"{signup.seat_row}排")
        if signup.seat_info and signup.seat_info.strip():
            seat_parts.append(f"{signup.seat_info}号")
        seat_display = "-".join(seat_parts) if seat_parts else ""

        data.append({
            "id": signup.id,
            "user_name": user.name,
            "schedule_name": schedule.title,
            "schedule_date": schedule.conference_date.strftime('%Y-%m-%d'),
            "begin_time": schedule.begin_time,
            "label": schedule.label,
            "end_time": schedule.end_time,
            "phone": user.phone,
            "status": signup.status,
            "company": user.company,
            "seat_img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, schedule.seat_img),
            "title": user.title,
            "seat_info": seat_display,
            "seat_region": signup.seat_region,
            "seat_row": signup.seat_row,
            "seat_type": signup.type
        })
    return data


def get_all_review_conference_list(name, forum, status):
    if status is None:
        result = db.session.query(ConferenceSignUp, User, ConferenceSchedule).join(User,
                                                                                   User.id == ConferenceSignUp.user_id).join(
            ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
            User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                                              ConferenceSchedule.is_deleted == 0,
            ConferenceSchedule.forum.like('%' + forum + '%')).all()
    else:
        result = db.session.query(ConferenceSignUp, User, ConferenceSchedule).join(User,
                                                                                   User.id == ConferenceSignUp.user_id).join(
            ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
            User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                                              ConferenceSchedule.is_deleted == 0,
                                              ConferenceSignUp.status == status,
            ConferenceSchedule.forum.like('%' + forum + '%')).all()
    signup_status_ENUM = {0: '等待审核', 1: '审核未通过', 2: '审核通过'}
    return [{"id": signup.id, "姓名": user.name, "预约会议名": schedule.title,
             "日期": schedule.conference_date.strftime('%Y-%m-%d'), "开始时间": schedule.begin_time,
             "结束时间": schedule.end_time, "联系方式": user.phone, "状态": signup_status_ENUM.get(signup.status),
             "公司名称": user.company,
             "职务": user.title} for signup, user, schedule in result]


def get_all_signup_conference_statics():
    ConferenceScheduleAlias = aliased(ConferenceSchedule)
    result = db.session.query(
        ConferenceScheduleAlias.title.label('会议名'),
        func.count(ConferenceSignUp.id).label('预约数量')
    ).join(
        User, User.id == ConferenceSignUp.user_id
    ).join(
        ConferenceScheduleAlias, ConferenceSignUp.schedule_id == ConferenceScheduleAlias.id
    ).filter(
        User.is_deleted == 0,
        ConferenceScheduleAlias.is_deleted == 0
    ).group_by(
        ConferenceScheduleAlias.title
    ).all()

    # 将结果转换为字典列表
    return [{"会议名": row.会议名, "预约数量": row.预约数量, "统计日期": datetime.datetime.now().strftime('%Y-%m-%d')}
            for row in result]


def get_conference_schedule_by_id(userid, date):
    signup_status_ENUM = {0: '等待审核', 1: '审核未通过', 2: '审核通过'}
    result = db.session.query(ConferenceSignUp, ConferenceSchedule).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSignUp.user_id == userid,
        ConferenceSchedule.conference_date == date).all()
    data = []
    for signup, schedule in result:
        delta = (datetime.datetime.strptime(
            schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
            "%Y-%m-%d %H:%M") - datetime.datetime.now()).total_seconds()
        data.append({"id": schedule.id, "schedule_name": schedule.title,
                     "schedule_time": schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
                     "status": signup_status_ENUM.get(signup.status), "seat_info": signup.seat_info,
                     "seat_img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, schedule.seat_img),
                     'info': '距开始还有1小时' if delta / 60 > 0 and delta / 60 < 120 else ''})
    return data


def get_user_schedule_num_by_id(userid):
    result = db.session.query(ConferenceSignUp, ConferenceSchedule).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSignUp.user_id == userid).all()
    num = 0
    main_label = False
    has_opening = False
    has_main = False
    color = config.BLACK_COLOR
    for signup, schedule in result:
        delta = (datetime.datetime.strptime(
            schedule.conference_date.strftime('%Y-%m-%d') + ' ' + schedule.begin_time,
            "%Y-%m-%d %H:%M") - datetime.datetime.now()).total_seconds()
        if delta / 60 > 0 and delta / 60 < 120:
            num += 1
        if schedule.label in ['主论坛', '开幕式']:
            main_label = True
            if schedule.label == '主论坛':
                has_main = True
            if schedule.label == '开幕式':
                has_opening = True
        # 根据新规则确定颜色
    if has_opening and has_main:
        # 如果两个都有，则11点之前显示开幕式颜色，11点之后显示主论坛颜色
        now = int(time.time())
        if now < config.ERCODE_EXCHANGE_TIME:
            color = config.OPEN_SCHEDULE_COLOR
        else:
            color = config.MAIN_SCHEDULE_COLOR
    elif has_opening:
        # 只有开幕式显示开幕式颜色
        color = config.OPEN_SCHEDULE_COLOR
    elif has_main:
        # 只有主论坛显示主论坛颜色
        color = config.MAIN_SCHEDULE_COLOR
    return num, main_label, color


def check_login_times(username, ip):
    log = OperaterLog.query.filter(OperaterLog.event == '/api/manage/login',
                                   OperaterLog.data.in_(['不存在该用户', '密码错误']),
                                   OperaterLog.create_time >= datetime.datetime.now() - datetime.timedelta(
                                       minutes=config.LOGIN_ERROR_LOCK_TIME),
                                   or_(OperaterLog.operator == username, OperaterLog.ip == ip)).all()
    return len(log)


def get_user_picture():
    users = User.query.filter(User.is_deleted == 0).all()
    return [user.img_url for user in users]


def find_user_schedule_tobegin():
    result = db.session.query(ConferenceSignUp, ConferenceSchedule, User).join(
        ConferenceSchedule, ConferenceSignUp.schedule_id == ConferenceSchedule.id).join(User,
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


def get_hall_schedule_bydate(date, label=None, forum=None):
    query = ConferenceSchedule.query.filter(
        ConferenceSchedule.is_deleted == 0,
        ConferenceSchedule.conference_date == date
    )
    if label is not None:
        query = query.filter(ConferenceSchedule.label == label)
    if forum is not None:
        query = query.filter(ConferenceSchedule.forum == forum)

    result = query.order_by(
        ConferenceSchedule.order.desc(),
        ConferenceSchedule.begin_time.asc()
    ).all()

    data = []
    for item in result:
        schedule = item.get_schedule_view()
        schedule['guest_img'] = []
        schedule['sponsor_info'] = []
        if len(schedule.get('guest_id', [])) > 0:
            for guest in schedule.get('guest_id', []):
                user = User.query.filter_by(id=guest, is_deleted=0).first()
                if user is None:
                    continue
                schedule['guest_img'].append('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url))
        if len(schedule.get('sponsor', [])) > 0:
            schedule['sponsor_info'].extend(get_coopearter_by_list(schedule.get('sponsor', [])))
        data.append(schedule)
    return data


def get_hall_blockchain_schedule():
    result = ConferenceSchedule.query.filter(
        ConferenceSchedule.is_deleted == 0,
        or_(ConferenceSchedule.title.like("%链%"), ConferenceSchedule.label == '展示展览')).order_by(
        ConferenceSchedule.begin_time.asc()).all()
    Exhibitonresult = Exhibiton.query.filter(
        Exhibiton.is_deleted == 0, Exhibiton.district == '展示展览').order_by(
        Exhibiton.begin_time.asc()).all()
    data = []
    for item in result:
        schedule = item.get_schedule_view()
        schedule['guest_img'] = []
        schedule['sponsor_info'] = []
        schedule['type'] = 'schedule'
        if len(schedule.get('guest_id', [])) > 0:
            for guest in schedule.get('guest_id', []):
                user = User.query.filter_by(id=guest, is_deleted=0).first()
                if user is None:
                    continue
                schedule['guest_img'].append('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url))
        if len(schedule.get('sponsor', [])) > 0:
            schedule['sponsor_info'].extend(get_coopearter_by_list(schedule.get('sponsor', [])))
        data.append(schedule)
    for item in Exhibitonresult:
        exhibiton = item.get_blockview_simple()
        exhibiton['type'] = 'exhibition'
        exhibiton['guest_img'] = []
        exhibiton['sponsor_info'] = []
        if len(exhibiton.get('sponsor', [])) > 0:
            exhibiton['sponsor_info'].extend(get_coopearter_by_list(exhibiton.get('sponsor', [])))
        data.append(exhibiton)
    data.sort(key=lambda x: x['begin_time'])
    return data


def get_hall_exhibition_bydate(date):
    result = Exhibiton.query.filter(
        Exhibiton.is_deleted == 0, Exhibiton.exhibition_date == date).order_by(
        Exhibiton.begin_time.asc()).all()
    data = [item.get() for item in result]
    return data


def get_hall_exhibition_bydistrict(district):
    result = Exhibiton.query.filter(
        Exhibiton.is_deleted == 0, Exhibiton.district == district).order_by(
        Exhibiton.begin_time.asc()).all()
    data = [item.get() for item in result]
    return data


def get_hall_exhibition():
    result = Exhibiton.query.filter(
        Exhibiton.is_deleted == 0).order_by(
        Exhibiton.begin_time.asc()).all()
    data = []
    for item in result:
        exhibition = item.get_view_simple()
        exhibition['guest_info'] = []
        exhibition['sponsor_info'] = []
        exhibition['supported_info'] = []
        exhibition['organizer_info'] = []
        exhibition['coorganizer_info'] = []
        if len(exhibition.get('supported', [])) > 0:
            exhibition['supported_info'].extend(get_coopearter_by_list(exhibition.get('supported', [])))
        if len(exhibition.get('organizer', [])) > 0:
            exhibition['organizer_info'].extend(get_coopearter_by_list(exhibition.get('organizer', [])))
        if len(exhibition.get('coorganizer', [])) > 0:
            exhibition['coorganizer_info'].extend(get_coopearter_by_list(exhibition.get('coorganizer', [])))
        if len(exhibition.get('sponsor', [])) > 0:
            exhibition['sponsor_info'].extend(get_coopearter_by_list(exhibition.get('sponsor', [])))
        for num in range(len(exhibition.get('participating_unit', []))):
            unit = ConferenCoopearter.query.filter(
                ConferenCoopearter.id == exhibition['participating_unit'][num]['unit'],
                ConferenCoopearter.is_deleted == 0).first()
            if unit is None:
                exhibition['participating_unit'][num]['status'] = False
            else:
                exhibition['participating_unit'][num]['status'] = True
                exhibition['participating_unit'][num].update(unit.get())
        data.append(exhibition)
    return data


def get_hall_exhibition_byid(id):
    result = Exhibiton.query.filter(Exhibiton.id == id).first()
    exhibition = result.get_view_simple()
    exhibition['guest_info'] = []
    exhibition['sponsor_info'] = []
    exhibition['supported_info'] = []
    exhibition['organizer_info'] = []
    exhibition['coorganizer_info'] = []
    for num in range(len(exhibition.get('participating_unit', []))):
        unit = ConferenCoopearter.query.filter(ConferenCoopearter.id == exhibition['participating_unit'][num]['unit'],
                                               ConferenCoopearter.is_deleted == 0).first()
        if unit is None:
            exhibition['participating_unit'][num]['status'] = False
        else:
            exhibition['participating_unit'][num]['status'] = True
            exhibition['participating_unit'][num].update(unit.get())
    if len(exhibition.get('supported', [])) > 0:
        exhibition['supported_info'].extend(get_coopearter_by_list(exhibition.get('supported', [])))
    if len(exhibition.get('organizer', [])) > 0:
        exhibition['organizer_info'].extend(get_coopearter_by_list(exhibition.get('organizer', [])))
    if len(exhibition.get('coorganizer', [])) > 0:
        exhibition['coorganizer_info'].extend(get_coopearter_by_list(exhibition.get('coorganizer', [])))
    if len(exhibition.get('sponsor', [])) > 0:
        exhibition['sponsor_info'].extend(get_coopearter_by_list(exhibition.get('sponsor', [])))
    return exhibition


def get_hall_schedule_byid(id):
    result = ConferenceSchedule.query.filter(ConferenceSchedule.id == id).first()
    schedule = result.get_schedule_view_simple()
    schedule['guest_info'] = []
    schedule['sponsor_info'] = []
    schedule['supported_info'] = []
    schedule['organizer_info'] = []
    schedule['coorganizer_info'] = []
    for num in range(len(schedule.get('agenda', []))):
        schedule['agenda'][num]['guest_info'] = []
        if len(schedule['agenda'][num].get('guest_id', [])) > 0:
            for guest in schedule['agenda'][num].get('guest_id', []):
                user = User.query.filter_by(id=guest, is_deleted=0).first()
                if user is None:
                    continue
                schedule['agenda'][num]['guest_info'].append(user.get())

    if len(schedule.get('guest_id', [])) > 0:
        for guest in schedule.get('guest_id', []):
            user = User.query.filter_by(id=guest, is_deleted=0).first()
            if user is None:
                continue
            schedule['guest_info'].append(user.get())
    if len(schedule.get('supported', [])) > 0:
        schedule['supported_info'].extend(get_coopearter_by_list(schedule.get('supported', [])))
    if len(schedule.get('organizer', [])) > 0:
        schedule['organizer_info'].extend(get_coopearter_by_list(schedule.get('organizer', [])))
    if len(schedule.get('coorganizer', [])) > 0:
        schedule['coorganizer_info'].extend(get_coopearter_by_list(schedule.get('coorganizer', [])))
    if len(schedule.get('sponsor', [])) > 0:
        schedule['sponsor_info'].extend(get_coopearter_by_list(schedule.get('sponsor', [])))
    return schedule


def get_coopearter_by_list(coopearter_ids):
    operaters = ConferenCoopearter.query.filter(ConferenCoopearter.id.in_(coopearter_ids),
                                                ConferenCoopearter.is_deleted == 0).all()
    data = []
    if operaters is not None:
        operaters.sort(key=lambda x: coopearter_ids.index(x.id))
        for operater in operaters:
            data.append(operater.get())
    return data


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
    showType = ConferenceCooperatorShow.query.filter(ConferenceCooperatorShow.is_show == True).all()
    type = [show.type for show in showType]
    schedules = ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted == 0).all()
    cooperater_id = []
    for schedule in schedules:
        result = schedule.get_schedule()
        for item in type:
            if item == 'participating_unit':
                continue
            cooperater_id.extend(result.get(item))
    exhibitions = Exhibiton.query.filter(Exhibiton.is_deleted == 0).all()
    for exhibition in exhibitions:
        result = exhibition.get()
        for item in type:
            if item == 'participating_unit':
                cooperater_id.extend([unit.get("unit") for unit in result.get(item, [])])
            else:
                cooperater_id.extend(result.get(item))
    result = ConferenCoopearter.query.filter(ConferenCoopearter.is_deleted == 0,
                                             ConferenCoopearter.id.in_(cooperater_id)).all()
    return [item.get() for item in result]


def get_pay_cooperater():
    result = ConferenCoopearter.query.filter(ConferenCoopearter.is_deleted == 0,
                                             ConferenCoopearter.type == '支付企业').all()
    return [item.get() for item in result]


def refresh_cooperater():
    data = get_cooperater()
    uploadwebfile(data, file='get_cooperater.json')
    data = get_pay_cooperater()
    uploadwebfile(data, file='get_pay_cooperater.json')
    data = get_cooperater_list('合作媒体')
    uploadwebfile(data, file='get_comedia.json')


def refresh_guest():
    data = get_guests_list()
    uploadwebfile(data, file='get_guest_list.json')


def refresh_guest_info(userid):
    guest = User.query.filter(User.id == userid).first()
    uploadwebfile(guest.get_guest(), file='web/guest/' + str(guest.id) + '.json')


def refresh_conference_info():
    result = ConferenceInfo.query.filter(ConferenceInfo.is_deleted == 0).order_by(ConferenceInfo.order.desc()).all()
    data = [item.get() for item in result]
    uploadwebfile(data, file='get_information_list.json')


def refresh_schedule_info():
    schedules = ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted == 0).all()
    for schedule in schedules:
        uploadwebfile(schedule.get_schedule_view_simple(),
                      file='get_schedule_by_id' + str(schedule.id) + '.json')


def get_operat_list(page, page_size, operator, event, begin_time, end_time):
    if begin_time and end_time:
        result = (db.session.query(OperaterLog, OperaterRule).join(OperaterRule,
                                                                   OperaterLog.event == OperaterRule.rule)
                  .filter(OperaterLog.operator.like('%' + operator + '%'),
                          OperaterRule.name.like('%' + event + '%'), OperaterLog.create_time >= begin_time,
                          OperaterLog.create_time <= end_time).order_by(
            OperaterLog.create_time.desc()).paginate(page, per_page=page_size, error_out=False))
    else:
        result = (db.session.query(OperaterLog, OperaterRule).join(OperaterRule,
                                                                   OperaterLog.event == OperaterRule.rule)
                  .filter(OperaterLog.operator.like('%' + operator + '%'),
                          OperaterRule.name.like('%' + event + '%')).order_by(
            OperaterLog.create_time.desc()).paginate(page, per_page=page_size, error_out=False))
    return result


def get_business_list(title=None, type=None):
    query = BusinessInfo.query.filter(BusinessInfo.is_deleted == 0, BusinessInfo.status == 2)
    if title is not None:
        query = query.filter(
            or_(BusinessInfo.title.like('%' + title + '%'), BusinessInfo.company.like('%' + title + '%')))
    if type is not None:
        query = query.filter(BusinessInfo.type.like('%' + type + '%'))
    result = query.order_by(BusinessInfo.create_time.desc()).all()
    return [item.get() for item in result]


def get_enterprise_list(title=None, type=None):
    query = EnterpriseCertified.query.filter(EnterpriseCertified.is_deleted == 0, EnterpriseCertified.status == 2)
    if title is not None:
        query = query.filter(
            or_(EnterpriseCertified.name.like('%' + title + '%')))
    if type is not None:
        query = query.filter(EnterpriseCertified.industry.like('%' + type + '%'))
    result = query.order_by(EnterpriseCertified.create_time.desc()).all()
    return [item.get() for item in result]


def get_business_certified_list(page, page_size, title, status):
    # if status is None:
    #     result = (db.session.query(EnterpriseCertified, User).join(User,
    #                                                                EnterpriseCertified.user_id == User.id)
    #               .filter(EnterpriseCertified.name.like('%' + title + '%'),
    #                       EnterpriseCertified.is_deleted == 0).order_by(
    #         EnterpriseCertified.create_time.desc()).paginate(page, per_page=page_size, error_out=False))
    # else:
    #     result = (db.session.query(EnterpriseCertified, User).join(User,
    #                                                                EnterpriseCertified.user_id == User.id)
    #               .filter(EnterpriseCertified.name.like('%' + title + '%'),
    #                       EnterpriseCertified.is_deleted == 0,
    #                       EnterpriseCertified.status == status).order_by(
    #         EnterpriseCertified.create_time.desc()).paginate(page, per_page=page_size, error_out=False))
    data = []
    # for enterprise, user in result.items:
    #     u = user.get()
    #     data.append({"id": enterprise.id, "name": enterprise.name, "code": enterprise.code,
    #                  "file_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, enterprise.file_url),
    #                  "scale": enterprise.scale, "invite_code": enterprise.invite_code,
    #                  "industry": enterprise.industry, "area": enterprise.area,
    #                  "financing_stage": enterprise.financing_stage,
    #                  "result": enterprise.result, "user_id": enterprise.user_id, "user_name": u.get("name"),
    #                  "status": enterprise.status, "is_deleted": enterprise.is_deleted,
    #                  "create_time": enterprise.create_time.strftime('%Y-%m-%d'), "chat_object_type": "公司"
    #                  })
    if status is None:
        result = EnterpriseCertified.query.filter(EnterpriseCertified.name.like('%' + title + '%'),
                                                  EnterpriseCertified.is_deleted == 0,
                                                  EnterpriseCertified.user_id == None).order_by(
            EnterpriseCertified.create_time.desc()).paginate(page, per_page=page_size, error_out=False)
    else:
        result = EnterpriseCertified.query.filter(EnterpriseCertified.name.like('%' + title + '%'),
                                                  EnterpriseCertified.is_deleted == 0,
                                                  EnterpriseCertified.status == status,
                                                  EnterpriseCertified.user_id == None).order_by(
            EnterpriseCertified.create_time.desc()).paginate(page, per_page=page_size, error_out=False)
    for item in result.items:
        u = None
        data.append({"id": item.id, "name": item.name, "code": item.code,
                     "file_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, item.file_url),
                     "scale": item.scale, "invite_code": item.invite_code,
                     "industry": item.industry, "area": item.area,
                     "financing_stage": item.financing_stage,
                     "result": item.result, "user_id": item.user_id, "user_name": None,
                     "status": item.status, "is_deleted": item.is_deleted,
                     "create_time": item.create_time.strftime('%Y-%m-%d'), "chat_object_type": "公司",
                     "contacts_name": item.contacts_name, "contacts_phone": item.contacts_phone
                     })
    return data, result.total


def update_EnterpriseCertified_statusbyid(userlist, status, reason):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        records = EnterpriseCertified.query.filter(EnterpriseCertified.id.in_(userlist)).all()
        for record in records:
            record.status = status
            record.reason = reason
        db.session.commit()
        return True
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def update_BusinessInfo_statusbyid(userlist, status, reason):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        records = BusinessInfo.query.filter(BusinessInfo.id.in_(userlist)).all()
        for record in records:
            record.status = status
            record.reason = reason
        db.session.commit()
        return True
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def get_meeting_record_list_byuserid(userid, page=1, page_size=1000):
    result = (db.session.query(MeetingReservation, MeetingRoom).join(MeetingRoom,
                                                                     MeetingReservation.meeting_room_id == MeetingRoom.id)
              .filter(MeetingReservation.creater_id == userid, MeetingReservation.is_deleted == 0).order_by(
        MeetingReservation.start_time.desc()).paginate(page, per_page=page_size, error_out=False))
    data = []
    for reservation, meeting_room in result.items:
        r = reservation.get()
        r["meeting_room_name"] = meeting_room.name
        r["meeting_room_id"] = meeting_room.id
        r["meeting_room_location"] = meeting_room.location
        data.append(r)
    return data, result.total


def check_in_label_byUserid(userid):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    result = ConferenceSignUp.query.filter(ConferenceSignUp.user_id == userid, ConferenceSignUp.status == 2,
                                           ConferenceSignUp.schedule_id.in_(
                                               [config.OPEN_SCHEDULE_ID, config.MAIN_SCHEDULE_ID])).first()
    if result:
        return True
    else:
        return False
# import json
# def check_64():
#     logs=OperaterLog.query.filter(OperaterLog.operator=='gdec_admin64',OperaterLog.event=='/api/manage/review_register').all()
#     users=[]
#     for log in logs:
#         data=json.loads(log.data)
#         if data['opt']=='agree':
#             users.extend(data['userlist'])
#     users=User.query.filter(User.id.in_(users),User.identity_verification!=1001)
#     for user in users:
#         user.status=0
#         insert_user( user)
#         print(user.id)
