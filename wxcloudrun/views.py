from datetime import datetime
from flask import render_template, request
from run import app
# from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule,User
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile
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