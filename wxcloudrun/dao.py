import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import ConferenceInfo

# 初始化日志
logger = logging.getLogger('log')

from wxcloudrun.model import User

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
