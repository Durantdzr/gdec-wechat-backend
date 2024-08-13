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


def batchdownloadfile(openid, file):
    data = {
        "env": config.ENV,
        "file_list": [
            {
                "fileid": 'cloud://{}.{}/{}'.format(config.ENV, config.COS_BUCKET, file),
                "max_age": 7200
            }
        ]
    }

    result = requests.post('http://api.weixin.qq.com/tcb/batchdownloadfile', params={"openid": openid},
                           json=data)
    result=result.json()
    return result.get('file_list')[0].get('download_url')

def uploadfile(openid, file):
    data = {
        "env": config.ENV,
        "path": file
    }

    result = requests.post('http://api.weixin.qq.com/tcb/uploadfile', params={"openid": openid},
                           json=data)
    result=result.json()


def valid_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')
