# encoding: utf-8
"""
@version: python3.9
@software: PyCharm
@file: utils.py
@describe: 
@time: 2024/8/13 1:37
"""

import requests
import config
import imghdr
import hashlib
import json


def batchdownloadfile(openid, filelist):
    data = {
        "env": config.ENV,
        "file_list": [
            {
                "fileid": file,
                "max_age": 7200
            } for file in filelist
        ]
    }

    result = requests.post('http://api.weixin.qq.com/tcb/batchdownloadfile', params={"openid": openid},
                           json=data)
    result = result.json()
    return result


def uploadfile(file, openid='omf5s7V9tfLS25ZxIXE0TtJCaZ3w'):
    data = {
        "env": config.ENV,
        "path": file
    }

    result = requests.post('http://api.weixin.qq.com/tcb/uploadfile', params={"openid": openid},
                           json=data)
    result = result.json()
    result2 = requests.post(result.get('url'),
                            data={"Signature": result.get('authorization'), "x-cos-security-token": result.get('token'),
                                  "x-cos-meta-fileid": result.get('cos_file_id'), "key": file}, files=[
            ('file', (file, open(file, 'rb'), 'application/json'))])
    return result


def valid_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


def vaild_password(password):
    return hashlib.md5(password.encode(encoding='UTF-8')).hexdigest()


def uploadwebfile(data, file, openid='omf5s7V9tfLS25ZxIXE0TtJCaZ3w'):
    data = {'code': 0, 'data': data}
    with open(file, 'w') as f:
        json.dump(data, f)
    uploadfile(openid=openid, file=file)
