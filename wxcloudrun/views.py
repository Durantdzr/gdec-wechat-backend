from flask import request
from run import app
from wxcloudrun.dao import insert_user, search_friends_byopenid, insert_realtion_friend, get_friend_list, \
    save_realtion_friendbyid, is_invited_user, get_guests_list, get_conference_schedule_by_id, get_open_guests_list, \
    get_main_hall_guests_list, get_other_hall_guests_list, get_cooperater_list, get_hall_schedule_bydate, get_live_data, \
    get_user_schedule_num_by_id, refresh_schedule_info, get_hall_schedule_byid, get_hall_exhibition_bydate, \
    get_hall_exhibition_byid, get_hall_exhibition, search_friends_random, refresh_guest, refresh_guest_info, is_friend, \
    get_hall_blockchain_schedule
from wxcloudrun.model import ConferenceInfo, User, ConferenceHall, RelationFriend, ConferenceSignUp, DigitalCityWeek,ConferenceSchedule
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, uploadwebfile, getscheduleqrcode, \
    send_check_msg, makeqrcode,send_tx_msg,masked_view
from sqlalchemy import or_
from wxcloudrun.cronjob import reload_image
import config
import requests
import json
import uuid
import base64
import os


# @app.before_first_request
# def init_data():
#     """
#     初始化数据
#     """
    

@app.route('/api/conference/get_information_list', methods=['GET'])
def get_information_list():
    """
        :return:大会资讯列表
        """
    # 获取请求体参数
    result = ConferenceInfo.query.filter(ConferenceInfo.is_deleted == 0).order_by(ConferenceInfo.order.desc()).all()
    return make_succ_response([item.get() for item in result])


@app.route('/api/conference/get_live_list', methods=['GET'])
def get_live_list():
    """
        :return:大会直播列表
        """
    # 获取请求体参数
    data = get_live_data()
    uploadwebfile(data, file='get_live_list.json')
    return make_succ_response(data)


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
    blockChain = request.args.get('blockChain')
    if blockChain:
        data = get_hall_blockchain_schedule()
    else:
        data = get_hall_schedule_bydate()
    return make_succ_response(data)


@app.route('/api/conference/get_hall_exhibition', methods=['GET'])
def view_get_hall_exhibition():
    """
        :return:大会展会
    """
    # 获取请求体参数
    wxOpenid = request.headers['X-WX-OPENID']
    data = get_hall_exhibition()
    uploadwebfile(data, file='get_hall_exhibition.json')
    return make_succ_response(data)


@app.route('/api/conference/get_exhibition_by_id', methods=['GET'])
def get_exhibition_by_id():
    """
    :return:获取某id的展会
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_hall_exhibition_byid(request.args.get('id'))
    uploadwebfile(data, openid=wxopenid, file='get_exhibitio_by_id' + str(request.args.get('id')) + '.json')
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
    success=len(ConferenceSignUp.query.filter(ConferenceSignUp.schedule_id == params['schedule_id'],
                                  ConferenceSignUp.status == 2).all())
    signup_max=ConferenceSchedule.query.filter(ConferenceSchedule.id==params['schedule_id']).first()
    if success>=signup_max.signup_max:
        return make_err_response('报名人数已满')
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
    data = result.json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None and data.get('errmsg') == 'ok':
        user = User()
        user.openid = request.headers['X-WX-OPENID']
        data_list = data.get('data_list', [{}])[0]
        json_data = json.loads(data_list.get('json', ''))
        json_data = json_data.get('data', {})
        phoneNumber = json_data.get('phoneNumber', '')
        user.phone = phoneNumber
        user.savephoneEncrypted(phoneNumber)
        insert_user(user)
    if user is not None and data.get('errmsg') == 'ok':
        data_list = data.get('data_list', [{}])[0]
        json_data = json.loads(data_list.get('json', ''))
        json_data = json_data.get('data', {})
        phoneNumber = json_data.get('phoneNumber', '')
        if user.status!=2 and user.status!=3:
            user.savephoneEncrypted(phoneNumber)
        s=str(uuid.uuid4())
        user.openid = s
        insert_user(user)
        user = User.query.filter(or_(User.phone == phoneNumber,User.phone==masked_view(phoneNumber))).first()
        if user is None:
            user = User()
            user.phone = phoneNumber
        elif user.is_deleted == 1:
            user.is_deleted = 0
            user.name = None
            user.phone = phoneNumber
            user.code = None
            user.title = None
            user.type = '普通观众'
            user.socail = 0
            user.status = 0
            user.img_url = None
            user.phoneEncrypted = None
            user.codeEncrypted = None
        elif user.phone==masked_view(phoneNumber) and user.openid==s:
            user.phone = phoneNumber
            user.savephoneEncrypted(phoneNumber)
            user.auto_flag = 1
        user.openid = request.headers['X-WX-OPENID']
        insert_user(user)
    return make_succ_response(data)


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
    if user.status == 2 and user.socail == params.get("socail", 0):
        return make_err_response('用户已完成审核，无法再次提交审核。')
    elif user.status == 2:
        user.socail = params.get("socail", 0)
        insert_user(user)
        if user.origin_userid is not None:
            guest = User.query.filter(User.id == user.origin_userid).first()
            guest.socail = params.get("socail", 0)
            insert_user(guest)
            refresh_guest()
            refresh_guest_info(guest.id)
        return make_succ_response(user.id)
    elif user.status == 3:
        return make_err_response('无法提交用户数据')
    user.name = params.get("name")
    user.phone = params.get("phone")
    user.savephoneEncrypted(params.get("phone"))
    user.code = params.get("code")
    user.savecodeEncrypted(params.get("code"))
    user.company = params.get("company")
    user.title = params.get("title")
    user.type = params.get("type")
    user.socail = params.get("socail", 0)
    user.img_url = params.get("cdn_param")
    user.status = 2
    insert_user(user)
    return make_succ_response(user.id)


@app.route('/api/user/upload_user_img', methods=['POST'])
def upload_user_img():
    """
    :return:上传用户头像
    """
    # 获取请求体参数

    params = request.get_json()
    src = params.get('img_encode')
    data = src.split(',')[1]
    image_data = base64.b64decode(data)
    u = uuid.uuid4()
    filename = 'guest/' + str(u) + '.jpeg'
    with open(filename, 'wb') as file_to_save:
        file_to_save.write(image_data)
    uploadfile(filename, openid=request.headers['X-WX-OPENID'])
    return make_succ_response(
        {'img_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, filename), "cdn_param": filename})


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
    if user.status == 2:
        data['find_friend'] = True
        data['invited'] = True
        data['schdule'] = True
        data['document'] = True
        data['invited_num'] = len(
            RelationFriend.query.filter(RelationFriend.inviter_id == user.id, RelationFriend.status == 0).all())
        data['schdule_num'] = get_user_schedule_num_by_id(user.id)
    return make_succ_response(data)


@app.route('/api/user/get_user_by_id', methods=['GET'])
def get_user_by_id():
    """
    :return:获取某id的用户信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.id == request.args.get('user_id')).first()
    if user is None:
        return make_err_response('没有该用户')
    return make_succ_response(user.get())


@app.route('/api/user/get_user_by_openid', methods=['GET'])
def get_user_by_openid():
    """
    :return:获取小程序用户信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid, User.is_deleted == 0).first()
    if user is None:
        return make_err_response('没有该用户')
    return make_succ_response(user.get_full())


@app.route('/api/user/search_friend', methods=['GET'])
def search_friend():
    """
    :return:寻找朋友
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    name = request.args.get('name')
    if name is None or name == '':
        socail_users = search_friends_random(wxopenid)
    else:
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
    inviter = User.query.filter(User.origin_userid == params.get('inviter_id')).first()
    if inviter is None:
        if is_friend(user.id, params.get('inviter_id')):
            return make_err_response('已有好友关系')
        r_friend = RelationFriend()
        r_friend.operater_id = user.id
        r_friend.inviter_id = params.get('inviter_id')
        r_friend.meeting_date = params.get('meeting_date')
        r_friend.visit_info = params.get('visit_info')
    else:
        if is_friend(user.id, inviter.id):
            return make_err_response('已有好友关系')
        r_friend = RelationFriend()
        r_friend.operater_id = user.id
        r_friend.inviter_id = inviter.id
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
    return make_succ_response(uploadfile('data.json', wxopenid))


@app.route('/api/getqrcodeimg', methods=['POST'])
def getqrcodeimg1():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    params = request.get_json()
    return make_succ_response(getscheduleqrcode(params.get('id')))


@app.route('/api/makeqrcodeimg', methods=['POST'])
def makeqrcodeimg():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    params = request.get_json()
    makeqrcode(params.get('url'), params.get('filename'))
    return make_succ_response()


@app.route('/api/downloadfile/json', methods=['GET'])
def downloadfile_json():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    cloudid = request.args.get('cloudid', "")
    return make_succ_response(batchdownloadfile([cloudid],wxopenid))


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
    data = get_cooperater_list('合作伙伴')
    uploadwebfile(data, openid=wxopenid, file='get_cooperater.json')
    return make_succ_response(data)


@app.route('/api/conference/get_comedia', methods=['GET'])
def get_comedia():
    """
    :return:获取合作媒体信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_cooperater_list('合作媒体')
    uploadwebfile(data, openid=wxopenid, file='get_comedia.json')
    return make_succ_response(data)


@app.route('/api/conference/get_schedule_by_id', methods=['GET'])
def get_schedule_by_id():
    """
    :return:获取某id的会议议程
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = get_hall_schedule_byid(request.args.get('id'))
    uploadwebfile(data, openid=wxopenid, file='get_schedule_by_id' + str(request.args.get('id')) + '.json')
    return make_succ_response(data)


@app.route('/api/conference/refresh_schedule_list', methods=['GET'])
def refresh_schedule_list():
    """
    :return:刷新嘉宾用户信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    refresh_schedule_info()
    return make_succ_response('ok')


@app.route('/api/send_msg', methods=['POST'])
def send_msg():
    """
        :return:发送消息
    """
    params = request.get_json()
    wxOpenid = request.headers['X-WX-OPENID']
    result = send_tx_msg(phone=params.get('phone'),template_id=params.get('template_id'))
    return make_succ_response(result)


@app.route('/api/conference/digital_city_week', methods=['GET'])
def digital_city_week():
    """
    :return:数字体验周数据接口
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    result = DigitalCityWeek.query.order_by(DigitalCityWeek.order.desc()).all()
    data = [item.get() for item in result]

    uploadwebfile(data, openid=wxopenid, file='digital_city_week.json')
    return make_succ_response(data)

@app.route('/api/conference/reload_image', methods=['GET'])
def reload_images():
    """
    :return:刷新图片
    """
    # 获取请求体参数
    reload_image()
    return make_succ_response(0)

@app.route('/api/conference/get_reload_schedule', methods=['GET'])
def get_reload_schedule():
    user_count = User.query.filter(User.is_deleted == 0).count()
    file=os.listdir('guest')
    return make_succ_response({"user_count":user_count,"file":len(file)})


@app.route('/api/send_open_msg', methods=['POST'])
def send_open_msg():
    """
        :return:发送消息
    """
    params = request.get_json()
    users=User.query.filter(User.type=='开幕式观众',User.is_deleted==0).all()
    print(len(users))
    for user in users:
        result=send_tx_msg(phone=[user.phone],template_id='2285544')
        print(result)
    return make_succ_response(0)