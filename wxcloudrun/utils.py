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
    return result
