from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import insert_user
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule,User
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile,uploadfile,valid_image
from werkzeug.utils import secure_filename
import imghdr
import config
import requests
@app.route('/api/conference/get_information_list', methods=['GET'])
def get_information_list():
    """
        :return:大会资讯列表
        """
    # 获取请求体参数
    result = ConferenceInfo.query.all()
    return make_succ_response([item.get() for item in result])


@app.route('/api/conference/get_live_list', methods=['GET'])
def get_live_list():
    """
        :return:大会直播列表
        """
    # 获取请求体参数
    result = ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted == 0,
                                             ConferenceSchedule.live_status > 0).all()
    return make_succ_response([item.get_live() for item in result])


@app.route('/api/conference/get_hall_list', methods=['GET'])
def get_hall_list():
    """
        :return:大会会场列表
    """
    # 获取请求体参数
    result = ConferenceSchedule.query.with_entities(ConferenceSchedule.hall).filter(
        ConferenceSchedule.is_deleted == 0).group_by(ConferenceSchedule.hall).all()
    return make_succ_response([item[0] for item in result])

@app.route('/api/conference/get_hall_schedule', methods=['GET'])
def get_hall_schedule():
    """
        :return:大会会场日程
    """
    # 获取请求体参数
    hall = request.args.get('hall')
    wxOpenid = request.headers['X-WX-OPENID']
    result = ConferenceSchedule.query.filter(
        ConferenceSchedule.is_deleted == 0,ConferenceSchedule.hall==hall).all()
    data=[]
    for item in result:
        schedule=item.get_schedule()
        schedule['guest_img']=[]
        if len(schedule.get('guest_id',[]))>0:
            for guest in schedule.get('guest_id',[]):
                user=User.query.filter_by(id=guest).first()
                schedule['guest_img'].append('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url))
        data.append(schedule)
    return make_succ_response(data)

@app.route('/api/get_user_phone', methods=['POST'])
def get_user_phone():
    """
    :return:获取手机号
    """

    # 获取请求体参数
    wxOpenid = request.headers['X-WX-OPENID']
    params = request.get_json()
    result = requests.post('http://api.weixin.qq.com/wxa/getopendata', params={"openid": wxOpenid},
                           json={'cloudid_list': [params.get("cloudid")]})
    return make_succ_response(result.json())

@app.route('/api/user/upload_user_info', methods=['POST'])
def upload_user_info():
    """
    :return:提交用户审核
    """
    # 获取请求体参数
    params = request.get_json()
    user=User.query.filter(User.openid==request.headers['X-WX-OPENID'],User.is_deleted==0).first()
    if user is  None:
        user = User()
        user.openid = request.headers['X-WX-OPENID']
    user.name = params.get("name")
    user.phone= params.get("phone")
    user.code= params.get("code")
    user.company = params.get("company")
    user.title = params.get("title")
    user.type = params.get("type")
    user.socail = params.get("socail",0)
    insert_user(user)
    return make_succ_response(user.id)

@app.route('/api/user/upload_user_img', methods=['POST'])
def upload_user_img():
    """
    :return:上传用户头像
    """
    # 获取请求体参数
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID'], User.is_deleted == 0).first()
    if user is None:
        user = User()
        user.openid = request.headers['X-WX-OPENID']
    file = request.files['file']
    if file:  # 这里可以加入文件类型判断等逻辑
        format=valid_image(file.stream)
        file.save('guest/'+request.headers['X-WX-OPENID']+format)
        uploadfile(request.headers['X-WX-OPENID'],'guest/'+request.headers['X-WX-OPENID']+format)
        user.img_url='guest/'+request.headers['X-WX-OPENID']+format
        insert_user(user)
        return make_succ_response(user.id)
    else:
        return make_err_response('请上传文件')