import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import ConferenceInfo, RelationFriend, User
from sqlalchemy import or_, and_
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


def search_friends_byopenid(openid, name):
    user = User.query.filter(User.openid == openid).first()
    user_id = user.id
    friends = RelationFriend.query.filter(
        or_(RelationFriend.operater_id == user_id, RelationFriend.inviter_id == user_id),
        RelationFriend.is_deleted == 0).all()
    friend_list = []
    for friend in friends:
        friend_list.append(friend.operater_id)
        friend_list.append(friend.inviter_id)
    socail_user = User.query.filter(User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                                    User.socail == 1, ~User.id.in_(friend_list)).all()
    return socail_user


def get_friend_list(openid, name):
    user = User.query.filter(User.openid == openid).first()
    user_id = user.id
    data = []
    operator_friends = db.session.query(RelationFriend, User).join(User, User.id == RelationFriend.inviter_id).filter(
        User.name.like('%' + name + '%'), RelationFriend.operater_id == user_id, RelationFriend.is_deleted == 0).all()
    status_ENUM = {0: '已邀请', 1: '已添加'}
    for relation, user in operator_friends:
        data.append({"name": user.name, "id": user.id, "company": user.company, "title": user.title,
                     "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url),
                     "status": status_ENUM.get(relation.status), "relation_id": relation.id})
    invited_friends = db.session.query(RelationFriend, User).join(User, User.id == RelationFriend.operater_id).filter(
        User.name.like('%' + name + '%'), RelationFriend.inviter_id == user_id, RelationFriend.is_deleted == 0).all()
    status_ENUM = {0: '接受邀请', 1: '已添加'}
    for relation, user in invited_friends:
        data.append({"name": user.name, "id": user.id, "company": user.company, "title": user.title,
                     "img_url": 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url),
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


def update_user_statusbyid(userlist, status):
    """
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        records = User.query.filter(User.id.in_(userlist)).all()
        for record in records:
            record.status = status
        db.session.commit()
        return True
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def get_guests_list():
    guests = User.query.filter(User.type == '嘉宾', User.is_deleted == 0).all()
    data = [guest.get_guest() for guest in guests]
    return data
