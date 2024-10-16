# encoding: utf-8
"""
@version: python3.9
@software: PyCharm
@file: cronjob.py
@describe: 
@time: 2024/9/4 11:17 AM
"""

from wxcloudrun.dao import find_user_schedule_tobegin,get_user_picture
from wxcloudrun.utils import send_to_begin_msg,download_cdn_file
import logging
logger = logging.getLogger('log')
def send_begin_msg():
    result = find_user_schedule_tobegin()
    for item in result:
        send_to_begin_msg(item.get("openid",""), item.get("title",""), item.get("location",""), item.get("begin_time",""))

def reload_image():
    img_url=get_user_picture()
    img_url=list(set(img_url))
    for user in img_url:
        if user is not None and user!="":
            print(user)
            download_cdn_file(user, user)

    