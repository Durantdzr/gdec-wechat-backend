# encoding: utf-8
"""
@version: python3.9
@software: PyCharm
@file: logger.py
@describe: 
@time: 2024/9/9 2:01 PM
"""
import logging
from logging import Handler, LogRecord
from wxcloudrun.model import OperaterLog
from wxcloudrun import db
import json


class DatabaseLogHandler(Handler):
    def emit(self, record: LogRecord) -> None:
        log_entry = OperaterLog(operator=record.msg.get("operator", ''), event=record.msg.get("event", ''),
                                ip=record.msg.get("ip", ''), data=record.msg.get("data", ''))
        db.session.add(log_entry)
        db.session.commit()


logger = logging.getLogger('manage')
logger.addHandler(DatabaseLogHandler())
logger.setLevel(logging.INFO)


def operatr_log(operator, event, data, ip):
    if type(data) == dict:
        data = json.dumps(data)
    logger.info(msg={"operator": operator, "event": event, "data": data, "ip": ip})
