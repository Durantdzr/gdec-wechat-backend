import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import ConferenceInfo

# 初始化日志
logger = logging.getLogger('log')

