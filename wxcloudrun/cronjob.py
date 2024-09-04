# encoding: utf-8
"""
@version: python3.9
@software: PyCharm
@file: cronjob.py
@describe: 
@time: 2024/9/4 11:17 AM
"""

from wxcloudrun.dao import find_user_schedule_tobegin
from wxcloudrun.utils import send_to_begin_msg
def send_begin_msg():
    result = find_user_schedule_tobegin()
    for item in result:
        send_to_begin_msg(item.get("openid",""), item.get("title",""), item.get("location",""), item.get("begin_time",""))