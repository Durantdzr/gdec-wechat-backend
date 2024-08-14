from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import insert_user, search_friends_byopenid, insert_realtion_friend, get_friend_list, \
    save_realtion_friendbyid,is_invited_user
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule, User, ConferenceHall, RelationFriend
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, valid_image
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
    result = ConferenceHall.query.all()
    return make_succ_response([item.name for item in result])


@app.route('/api/conference/get_hall_schedule', methods=['GET'])
def get_hall_schedule():
    """
        :return:大会会场日程
    """
    # 获取请求体参数
    hall = request.args.get('hall')
    wxOpenid = request.headers['X-WX-OPENID']
    result = ConferenceSchedule.query.filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSchedule.hall == hall).all()
    data = []
    for item in result:
        schedule = item.get_schedule()
        schedule['guest_img'] = []
        if len(schedule.get('guest_id', [])) > 0:
            for guest in schedule.get('guest_id', []):
                user = User.query.filter_by(id=guest).first()
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
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        user = User()
        user.openid = request.headers['X-WX-OPENID']
    user.name = params.get("name")
    user.phone = params.get("phone")
    user.code = params.get("code")
    user.company = params.get("company")
    user.title = params.get("title")
    user.type = params.get("type")
    user.socail = params.get("socail", 0)
    insert_user(user)
    return make_succ_response(user.id)


@app.route('/api/user/upload_user_img', methods=['POST'])
def upload_user_img():
    """
    :return:上传用户头像
    """
    # 获取请求体参数
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        user = User()
        user.openid = request.headers['X-WX-OPENID']
    file = request.files['file']
    if file:  # 这里可以加入文件类型判断等逻辑
        format = valid_image(file.stream)
        file.save('guest/' + request.headers['X-WX-OPENID'] + format)
        uploadfile(request.headers['X-WX-OPENID'], 'guest/' + request.headers['X-WX-OPENID'] + format)
        user.img_url = 'guest/' + request.headers['X-WX-OPENID'] + format
        insert_user(user)
        return make_succ_response(user.id)
    else:
        return make_err_response('请上传文件')


@app.route('/api/user/privilege', methods=['GET'])
def get_user_privilege():
    """
    :return:获取用户权限
    """
    # 获取请求体参数
    data = {'account_status': '未审核', 'find_friend': False, 'invited': False, 'schdule': False, 'document': False,
            'invited_num': 0, 'schdule_num': 0}
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid, User.is_deleted == 0).first()
    if user is None:
        return make_succ_response(data)
    data['account_status'] = user.get_status()
    if user.status:
        data['find_friend'] = True
        data['invited'] = True
        data['schdule'] = True
        data['document'] = True
    return make_succ_response(data)


@app.route('/api/user/search_friend', methods=['GET'])
def search_friend():
    """
    :return:寻找朋友
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    name = request.args.get('name')
    if name is None or name == '':
        return make_err_response('请输入姓名')
    socail_users = search_friends_byopenid(wxopenid, name)
    return make_succ_response([user.get() for user in socail_users])


@app.route('/api/user/add_friend', methods=['POST'])
def add_friend():
    """
    :return:发出好友邀请
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    params = request.get_json()
    user = User.query.filter(User.openid == wxopenid).first()
    r_friend = RelationFriend()
    r_friend.operater_id = user.id
    r_friend.inviter_id = params.get('inviter_id')
    r_friend.meeting_date = params.get('meeting_date')
    r_friend.visit_info = params.get('visit_info')
    insert_realtion_friend(r_friend)
    return make_succ_response(r_friend.id)


@app.route('/api/user/get_invite_list', methods=['GET'])
def get_invite_list():
    """
    :return:发出好友邀请
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    name = request.args.get('name', "")
    return make_succ_response(get_friend_list(wxopenid, name))


@app.route('/api/user/save_invite', methods=['POST'])
def save_invite():
    """
    :return:接受好友邀请
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    params = request.get_json()
    relation_id = params.get('relation_id')
    if is_invited_user(relation_id,wxopenid):
        return make_succ_response(save_realtion_friendbyid(int(relation_id)))
    else:
        return make_err_response('操作者不是接受邀请用户。')
