from flask import request
from run import app
from wxcloudrun.dao import insert_user, search_friends_byopenid, insert_realtion_friend, get_friend_list, \
    save_realtion_friendbyid, is_invited_user, update_user_statusbyid, get_guests_list, get_conference_schedule_by_id, \
    get_open_guests_list, get_main_hall_guests_list, get_other_hall_guests_list,get_cooperater_list
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule, User, ConferenceHall, RelationFriend, ConferenceSignUp, \
    ConferenCoopearter
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, valid_image, uploadwebfile
import imghdr
import config
import requests
import json
import uuid


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
    date = request.args.get('date')
    wxOpenid = request.headers['X-WX-OPENID']
    result = ConferenceSchedule.query.filter(
        ConferenceSchedule.is_deleted == 0, ConferenceSchedule.conference_date == date).order_by(
        ConferenceSchedule.id).all()
    data = []
    for item in result:
        schedule = item.get_schedule_view()
        schedule['guest_img'] = []
        if len(schedule.get('guest_id', [])) > 0:
            for guest in schedule.get('guest_id', []):
                user = User.query.filter_by(id=guest).first()
                schedule['guest_img'].append('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, user.img_url))
        data.append(schedule)
    return make_succ_response(data)


@app.route('/api/conference/sign_up_conference', methods=['POST'])
def sign_up_conference():
    """
    :return:用户报名会议接口
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if ConferenceSignUp.query.filter(ConferenceSignUp.schedule_id == params['schedule_id'],
                                     ConferenceSignUp.user_id == user.id).first():
        return make_err_response('已报名过该会议')
    sign_up = ConferenceSignUp()
    sign_up.user_id = user.id
    sign_up.schedule_id = params.get('schedule_id')
    insert_user(sign_up)
    return make_succ_response(sign_up.id)


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
    user.img_url = params.get("cdn_param")
    insert_user(user)
    return make_succ_response(user.id)


@app.route('/api/user/upload_user_img', methods=['POST'])
def upload_user_img():
    """
    :return:上传用户头像
    """
    # 获取请求体参数

    file = request.files['file']
    if file:  # 这里可以加入文件类型判断等逻辑
        format = valid_image(file.stream)
        u = uuid.uuid4()
        filename = 'guest/' + str(u) + format
        file.save(filename)
        uploadfile(filename, openid=request.headers['X-WX-OPENID'])
        return make_succ_response(
            {'img_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, filename), "cdn_param": filename})
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


@app.route('/api/user/get_user_by_id', methods=['GET'])
def get_user_by_id():
    """
    :return:获取某id的用户信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.id == request.args.get('user_id')).first()
    return make_succ_response(user.get())


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
    if is_invited_user(relation_id, wxopenid):
        return make_succ_response(save_realtion_friendbyid(int(relation_id)))
    else:
        return make_err_response('操作者不是接受邀请用户。')


@app.route('/api/conference/get_guest_list', methods=['GET'])
def get_guest_list():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_guests_list()
    # uploadwebfile(data, openid=wxopenid, file='get_guest_list.json')
    return make_succ_response(data)


@app.route('/api/uploadfile/json', methods=['POST'])
def uploadfile_json():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = request.get_json()
    with open('data.json', 'w') as f:
        json.dump(data, f)
    return make_succ_response(uploadfile(wxopenid, 'data.json'))


@app.route('/api/downloadfile/json', methods=['GET'])
def downloadfile_json():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    cloudid = request.args.get('cloudid', "")
    return make_succ_response(batchdownloadfile(wxopenid, [cloudid]))


@app.route('/api/conference/get_schedule_list', methods=['GET'])
def get_schedule_list():
    """
    :return:获取当前用户的日程
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid, User.is_deleted == 0).first()
    data = get_conference_schedule_by_id(userid=user.id)
    return make_succ_response(data)


@app.route('/api/conference/get_open_guest_list', methods=['GET'])
def get_open_guest_list():
    """
    :return:获取开幕式嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_open_guests_list()
    uploadwebfile(data, openid=wxopenid, file='get_open_guest_list.json')
    return make_succ_response(data)


@app.route('/api/conference/get_main_hall_guest_list', methods=['GET'])
def get_main_hall_guest_list():
    """
    :return:获取主论坛嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_main_hall_guests_list()
    uploadwebfile(data, openid=wxopenid, file='get_main_hall_guest_list.json')
    return make_succ_response(data)


@app.route('/api/conference/get_other_hall_guest_list', methods=['GET'])
def get_other_hall_guest_list():
    """
    :return:获取分论坛嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_other_hall_guests_list()
    uploadwebfile(data, openid=wxopenid, file='get_other_hall_guest_list.json')
    return make_succ_response(data)


@app.route('/api/conference/refresh_all_guest_list', methods=['GET'])
def refresh_all_guest_list():
    """
    :return:刷新嘉宾用户信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    guests = User.query.filter(User.type == '嘉宾', User.is_deleted == 0).order_by(
        User.order.desc()).all()
    for guest in guests:
        uploadwebfile(guest.get_guest(), openid=wxopenid, file='web/guest/' + str(guest.id) + '.json')
    return make_succ_response('ok')


@app.route('/api/conference/get_cooperater', methods=['GET'])
def get_cooperaters():
    """
    :return:获取合作伙伴信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data=get_cooperater_list('合作伙伴')
    uploadwebfile(data, openid=wxopenid, file='get_cooperater.json')
    return make_succ_response(data)

@app.route('/api/conference/get_comedia', methods=['GET'])
def get_comedia():
    """
    :return:获取合作媒体信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data=get_cooperater_list('合作媒体')
    uploadwebfile(data, openid=wxopenid, file='get_comedia.json')
    return make_succ_response(data)
