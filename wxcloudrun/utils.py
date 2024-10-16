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
import zipfile
import os
import random
import time
import io
from PIL import Image
from cryptography.fernet import Fernet
import types
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.sms.v20210111 import sms_client, models
import re

cipher_suite = Fernet(config.FERNET_KEY)
def batchdownloadfile(filelist,openid='omf5s7V9tfLS25ZxIXE0TtJCaZ3w'):
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


def getqrcodeimg(path="page/index/index", openid='omf5s7V9tfLS25ZxIXE0TtJCaZ3w'):
    data = {
        "path": path,
        "width": 430,
        "env_version":"develop" if config.VERSION=='test/' else "release"
    }

    result = requests.post('http://api.weixin.qq.com/wxa/getwxacode', params={"openid": openid},
                           json=data)
    return io.BytesIO(result.content)

def getscheduleqrcode(id):
    imgBuffer=getqrcodeimg(path="myHome/agenda/index?id={}".format(id))
    img=Image.open(imgBuffer)
    img.save(config.VERSION + 'qrcode_schedule_' + str(id) + '.jpg', 'JPEG')
    uploadfile(config.VERSION + 'qrcode_schedule_' + str(id) + '.jpg')

def makeqrcode(url,filename):
    imgBuffer = getqrcodeimg(path=url)
    img = Image.open(imgBuffer)
    img.save(config.VERSION + filename, 'JPEG')
    uploadfile(config.VERSION + filename)



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
    with open(config.VERSION + file, 'w') as f:
        json.dump(data, f)
    uploadfile(openid=openid, file=config.VERSION + file)


def send_to_begin_msg(openid, title, location, begin_time):
    data = {
        "touser": openid,
        "template_id": "ercDXlwuxY8WfhCWzLnElsvpJmKDSjN7N1HyRliaElM",
        "data": {
            "thing2": {
                "value": title
            },
            "thing4": {
                "value": location
            },
            "time3": {
                "value": begin_time
            },
            "thing5": {
                "value": "活动即将开始，请前往参加"
            }
        },
        "miniprogram_state": "trial",
        "lang": "zh_CN"
    }

    result = requests.post('http://api.weixin.qq.com/cgi-bin/message/subscribe/send', params={"openid": openid},
                           json=data)
    return result.json()


def send_check_msg(openid, meetingname, content, reason, phrase3, date):
    data = {
        "touser": openid,
        "template_id": "VP9vKMAYt7SYhdgI6H73hUBqyQo3KctyvNb4pdVRAw0",
        "data": {
            "thing1": {
                "value": meetingname
            },
            "thing2": {
                "value": content
            },
            "thing21": {
                "value": reason
            },
            "phrase3": {
                "value": phrase3
            },
            "date4": {
                "value": date
            }
        },
        "miniprogram_state": "trial",
        "lang": "zh_CN"
    }

    result = requests.post('http://api.weixin.qq.com/cgi-bin/message/subscribe/send', params={"openid": openid},
                           json=data)
    return result.json()


def get_urllink(openid='omf5s7V9tfLS25ZxIXE0TtJCaZ3w'):
    data = {"expire_type": 1, "expire_interval": 15, "env_version": "trial"}
    result = requests.post('http://api.weixin.qq.com/wxa/generate_urllink', params={"openid": openid}, json=data)
    return result.json()


def get_ticket(url, openid='omf5s7V9tfLS25ZxIXE0TtJCaZ3w'):
    result = requests.get('http://api.weixin.qq.com/cgi-bin/ticket/getticket', params={"openid": openid})
    ticket_response = result.json()
    jsapi_ticket = ticket_response.get("ticket", "111")
    nonce_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
    timestamp = int(time.time())
    string1 = f'jsapi_ticket={jsapi_ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}'
    signature = hashlib.sha1(string1.encode('utf-8')).hexdigest()

    return result.json(), {
        'appId': "wx06cb5c6c75d69dc2",
        'timestamp': timestamp,
        'nonceStr': nonce_str,
        'signature': signature
    }


def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_in_zip_path = os.path.relpath(file_path, os.path.dirname(folder_path))
                zipf.write(file_path, file_in_zip_path)


def download_cdn_file(cdn_param, output_file):
    response = requests.get('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, cdn_param))
    with open(output_file, "wb") as file:
        file.write(response.content)


def encrypt(message):
    encrypted = cipher_suite.encrypt(message.encode('utf-8'))
    return encrypted

def decrypt(encrypted):
    decrypted = cipher_suite.decrypt(encrypted)
    return decrypted.decode('utf-8')

def masked_view(s):
    if len(s) <= 7:
        return s
    masked = re.sub(r'(?<=.{3}).(?=.{4})', '*', s)
    return masked

def send_tx_msg(phone, template_id):
    try:
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(config.SecretId, config.SecretKey)
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "sms.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = sms_client.SmsClient(cred, "ap-nanjing", clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.SendSmsRequest()
        params = {
            "PhoneNumberSet": phone,
            "SmsSdkAppId": config.SdkAppId,
            "TemplateId": template_id,
            "SignName": "全球数商大会GDEC"
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个SendSmsResponse的实例，与请求对象对应
        resp = client.SendSms(req)
        # 输出json格式的字符串回包
        return(resp.to_json_string())

    except TencentCloudSDKException as err:
        print(err)