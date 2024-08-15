import json

from flask import Response
from wxcloudrun.utils import uploadfile
def make_succ_empty_response():
    data = json.dumps({'code': 0, 'data': {}})
    return Response(data, mimetype='application/json')


def make_succ_response(data,code=0):
    data = json.dumps({'code': code, 'data': data})
    return Response(data, mimetype='application/json')
def make_web_succ_response(data,openid,web_file,code=0):
    data = json.dumps({'code': code, 'data': data})
    with open(web_file, 'w') as f:
        json.dump(data, f)
    uploadfile(openid,web_file)
    return Response(data, mimetype='application/json')

def make_succ_page_response(data,code=0,total=0):
    data = json.dumps({'code': code, 'data': data, 'total': total})
    return Response(data, mimetype='application/json')


def make_err_response(err_msg):
    data = json.dumps({'code': -1, 'errorMsg': err_msg})
    return Response(data, mimetype='application/json')
