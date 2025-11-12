from flask import request
from run import app
from wxcloudrun.dao import insert_user, search_friends_byopenid, insert_realtion_friend, get_friend_list, \
    save_realtion_friendbyid, is_invited_user, get_guests_list, get_conference_schedule_by_id, get_open_guests_list, \
    get_main_hall_guests_list, get_other_hall_guests_list, get_cooperater_list, get_hall_schedule_bydate, get_live_data, \
    get_user_schedule_num_by_id, refresh_schedule_info, get_hall_schedule_byid, get_hall_exhibition_bydate, \
    get_hall_exhibition_byid, get_hall_exhibition, search_friends_random, refresh_guest, refresh_guest_info, is_friend, \
    get_hall_blockchain_schedule, get_business_list, get_enterprise_list, get_meeting_record_list_byuserid, \
    get_review_conference_listBYlabel
from wxcloudrun.model import ConferenceInfo, User, ConferenceHall, RelationFriend, ConferenceSignUp, DigitalCityWeek, \
    BusinessInfo, EnterpriseCertified, BusinessNegotiation, MeetingRoom, MeetingReservation, RelationUserCertified,ConferenceSchedule
from wxcloudrun.response import make_succ_response, make_err_response, make_succ_page_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, uploadwebfile, getscheduleqrcode, \
    send_check_msg, makeqrcode, send_tx_msg, masked_view, generate_verification_code, CA_identification
from flask_jwt_extended import create_access_token
from datetime import timedelta
from sqlalchemy import or_, and_, func
from wxcloudrun.cronjob import reload_image
import config
import requests
import json
import uuid
import base64
import os
import datetime


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
    label = request.args.get('label')
    forum = request.args.get('forum')
    if blockChain:
        data = get_hall_blockchain_schedule()
    else:
        data = get_hall_schedule_bydate(date, label, forum)
    return make_succ_response(data)


@app.route('/api/conference/get_hall_forum', methods=['GET'])
def get_hall_forum():
    """
        :return:大会会场日程
    """
    # 获取请求体参数
    date = request.args.get('date')
    wxOpenid = request.headers['X-WX-OPENID']
    result = get_hall_schedule_bydate(date)
    data = []
    for item in result:
        if item.get('forum') not in data:
            data.append(item.get('forum'))
    return make_succ_response(data)


@app.route('/api/conference/get_hall_exhibition', methods=['GET'])
def view_get_hall_exhibition():
    """
        :return:大会展会
    """
    # 获取请求体参数
    wxOpenid = request.headers['X-WX-OPENID']
    data = get_hall_exhibition()
    # uploadwebfile(data, file='get_hall_exhibition.json')
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
        if user.status != 2 and user.status != 3:
            user.savephoneEncrypted(phoneNumber)
        s = str(uuid.uuid4())
        user.openid = s
        insert_user(user)
        user = User.query.filter(or_(User.phone == phoneNumber, User.phone == masked_view(phoneNumber))).first()
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
        elif user.phone == masked_view(phoneNumber) and user.openid == s:
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
    if user.status == 2 and user.socail == params.get("socail", 0) and user.identity_verification==1001:
        return make_err_response('用户已完成审核，无法再次提交审核。')
    elif user.status == 2 and user.identity_verification==1001:
        user.socail = params.get("socail", 0)
        insert_user(user)
        if user.origin_userid is not None:
            guest = User.query.filter(User.id == user.origin_userid).first()
            guest.socail = params.get("socail", 0)
            insert_user(guest)
            refresh_guest()
            refresh_guest_info(guest.id)
        return make_succ_response(user.id)
    elif user.status == 3 and user.identity_verification==1001:
        return make_err_response('用户信息待审核无法提交')
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
    user.status = 3
    insert_user(user)
    subcode = CA_identification(user.name, user.phone, user.code, user.openid)
    user.identity_verification = subcode
    insert_user(user)
    if subcode != '1001':
        return make_err_response('实名认证不通过')
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
            'invited_num': 0, 'schdule_num': 0, 'main_label': False}
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
        data['schdule_num'], data['main_label'] = get_user_schedule_num_by_id(user.id)
    r = RelationUserCertified.query.filter(RelationUserCertified.user_id == user.id,
                                           RelationUserCertified.status == 2).first()
    if r is None:
        data['enterprise_certified_status'] = None
    else:
        enterprise_certified = EnterpriseCertified.query.filter(EnterpriseCertified.id == r.enterprise_id,
                                                                EnterpriseCertified.is_deleted == 0).first()
        if enterprise_certified is not None:
            data['enterprise_certified_status'] = "审核通过"
            data['enterprise_certified_info'] = enterprise_certified.get()
        else:
            data['enterprise_certified_status'] = None
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
    data = user.get_full()
    enterprise_certified = EnterpriseCertified.query.filter(EnterpriseCertified.user_id == user.id,
                                                            EnterpriseCertified.is_deleted == 0).first()
    if enterprise_certified is not None:
        status_Enum = {0: "待审核", 1: "审核通过", 2: "审核未通过"}
        data['enterprise_certified_status'] = status_Enum.get(enterprise_certified.status)
    else:
        data['enterprise_certified_status'] = None
    ercode = create_access_token(identity=user.id, expires_delta=timedelta(minutes=30),
                                       additional_claims={'used':'闸机对接'})
    data['er_code'] = ercode
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
    return make_succ_response(batchdownloadfile([cloudid], wxopenid))


@app.route('/api/conference/get_schedule_list', methods=['GET'])
def get_schedule_list():
    """
    :return:获取当前用户的日程
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid, User.is_deleted == 0).first()
    date = request.args.get('date', "2025-11-13")
    data = get_conference_schedule_by_id(userid=user.id, date=date)
    return make_succ_response(data)


@app.route('/api/conference/get_sign_up_seat', methods=['POST'])
def get_sign_up_seat():
    """
    :return:获取某个用户的座位
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    params = request.get_json()
    phone = params.get('phone', "")
    name = params.get('name', "")
    label = params.get('label')
    schedule_id = params.get('schedule_id')
    user = User.query.filter(User.name == name, User.phone == phone, User.is_deleted == 0).first()
    if user is None:
        return make_err_response('用户不存在')
    data = get_review_conference_listBYlabel(userid=user.id, label=label, schedule_id=schedule_id)
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
    # uploadwebfile(data, openid=wxopenid, file='get_schedule_by_id' + str(request.args.get('id')) + '.json')
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
    result = send_tx_msg(phone=params.get('phone'), template_id=params.get('template_id'))
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

@app.route('/api/conference/reload_schedule', methods=['GET'])
def reload_schedule():
    """
    :return:刷新图片
    """
    # 获取请求体参数
    schedules=ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted==0).all()
    for schedule in schedules:
        getscheduleqrcode(schedule.id)

    return make_succ_response(0)



@app.route('/api/conference/get_reload_schedule', methods=['GET'])
def get_reload_schedule():
    user_count = User.query.filter(User.is_deleted == 0).count()
    file = os.listdir('guest')
    return make_succ_response({"user_count": user_count, "file": len(file)})


@app.route('/api/send_open_msg', methods=['POST'])
def send_open_msg():
    """
        :return:发送消息
    """
    params = request.get_json()
    send_tx_msg(phone=['13022157641'], template_id='2527363', template_param_set=["283475", "5"])
    # users = User.query.filter(User.type == '开幕式观众', User.is_deleted == 0).all()
    # print(len(users))
    # for user in users:
    #     result = send_tx_msg(phone=[user.phone], template_id='2527363')
    #     print(result)
    return make_succ_response(0)


@app.route('/api/business/upload_img', methods=['POST'])
def business_upload_img():
    """
    :return:上传文件
    """
    # 获取请求体参数

    params = request.get_json()
    src = params.get('img_encode')
    data = src.split(',')[1]
    image_data = base64.b64decode(data)
    u = uuid.uuid4()
    filename = 'business/' + str(u) + '.jpeg'
    with open(filename, 'wb') as file_to_save:
        file_to_save.write(image_data)
    uploadfile(filename, openid=request.headers['X-WX-OPENID'])
    return make_succ_response(
        {'img_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, filename), "cdn_param": filename})


@app.route('/api/business/get_certified_info', methods=['GET'])
def business_get_info():
    """
    :return:获取认证信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid).first()
    if user is None:
        return make_err_response('用户不存在')
    code = request.args.get('code')
    enterprise = EnterpriseCertified.query.filter(EnterpriseCertified.code == code,
                                                  EnterpriseCertified.is_deleted == 0).first()
    if enterprise is None:
        return make_err_response('信用代码不存在')
    data = enterprise.get()
    if enterprise.contacts_phone == user.phone:
        r = RelationUserCertified()
        r.user_id = user.id
        r.enterprise_id = enterprise.id
        r.status = 2
        insert_user(r)
    data['certified'] = enterprise.contacts_phone == user.phone
    return make_succ_response(data)


@app.route('/api/business/send_certified_msg', methods=['GET'])
def send_certified_msg():
    """
    :return:发送认证信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid).first()
    if user is None:
        return make_err_response('用户不存在')
    r = RelationUserCertified.query.filter(RelationUserCertified.user_id == user.id,
                                           RelationUserCertified.status == 1).first()
    if r is not None:
        return make_err_response('用户已认证')
    r = RelationUserCertified.query.filter(RelationUserCertified.user_id == user.id,
                                           RelationUserCertified.status == 0,
                                           RelationUserCertified.create_time >= datetime.datetime.now() - datetime.timedelta(
                                               minutes=5)).first()
    if r is not None:
        return make_err_response('请勿重复发送')
    code = request.args.get('code')
    enterprise = EnterpriseCertified.query.filter(EnterpriseCertified.code == code,
                                                  EnterpriseCertified.is_deleted == 0).first()
    import random
    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    r = RelationUserCertified()
    r.user_id = user.id
    r.enterprise_id = enterprise.id
    r.verification_code = verification_code
    insert_user(r)
    result = send_tx_msg(phone=[enterprise.contacts_phone], template_id='2527363',
                         template_param_set=[verification_code, "5"])
    return make_succ_response(result)


@app.route('/api/business/certified', methods=['GET'])
def business_business_certified():
    """
    :return:发送认证信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid).first()
    if user is None:
        return make_err_response('用户不存在')
    verification_code = request.args.get('verification_code')
    code = request.args.get('code')
    enterprise = EnterpriseCertified.query.filter(EnterpriseCertified.code == code,
                                                  EnterpriseCertified.is_deleted == 0).first()
    r = RelationUserCertified.query.filter(RelationUserCertified.user_id == user.id,
                                           RelationUserCertified.enterprise_id == enterprise.id,
                                           RelationUserCertified.verification_code == verification_code).first()
    if r is None:
        return make_err_response('验证码错误')
    delta = (datetime.datetime.now() - r.create_time).total_seconds()
    if delta > 60 * 5:
        return make_err_response('验证码已过期')
    r.status = 2
    insert_user(r)
    return make_succ_response(r.id)


# @app.route('/api/business/certified', methods=['POST'])
# def business_business_certified():
#     """
#     :return:提交用户企业认证
#     """
#     # 获取请求体参数
#     params = request.get_json()
#     user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
#
#     if params.get('invite_code') is None:
#         return make_err_response('请填写邀请码')
#     if user is None:
#         return make_err_response('用户不存在')
#     if user.status != 2:
#         return make_err_response('用户未完成审核，请稍后。')
#     else:
#         certified = EnterpriseCertified.query.filter(
#             or_(EnterpriseCertified.user_id == user.id, and_(EnterpriseCertified.status == 2,
#                                                              EnterpriseCertified.code == params.get('code'))),
#             EnterpriseCertified.is_deleted == 0).first()
#         if certified is not None:
#             if certified.status != 1:
#                 return make_err_response('该用户或者企业已有认证，请勿重新提交')
#             else:
#                 certified.name = params.get('name')
#                 certified.code = params.get('code')
#                 certified.file_url = params.get('cdn_param')
#                 certified.scale = params.get('scale')
#                 certified.industry = params.get('industry')
#                 certified.area = params.get('area')
#                 certified.financing_stage = params.get('financing_stage')
#                 certified.result = params.get('result')
#                 certified.status = 0
#                 insert_user(certified)
#             return make_succ_response(certified.id)
#         certified = EnterpriseCertified.query.filter(
#             EnterpriseCertified.invite_code == params.get('invite_code')).first()
#         if certified is None:
#             return make_err_response('该邀请码错误')
#         elif certified.user_id is not None and certified.user_id != user.id:
#             return make_err_response('该邀请码已使用，非当前用户绑定')
#         else:
#             certified.user_id = user.id
#             certified.name = params.get('name')
#             certified.code = params.get('code')
#             certified.file_url = params.get('cdn_param')
#             certified.scale = params.get('scale')
#             certified.industry = params.get('industry')
#             certified.area = params.get('area')
#             certified.financing_stage = params.get('financing_stage')
#             certified.result = params.get('result')
#             insert_user(certified)
#         return make_succ_response(certified.id)


@app.route('/api/business/deploy_info', methods=['POST'])
def business_deploy_info():
    """
    :return:商务信息发布
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    certified = RelationUserCertified.query.filter(RelationUserCertified.user_id == user.id,
                                                 RelationUserCertified.status == 2).first()
    if certified is None:
        return make_err_response('该用户未完成企业认证')
    else:
        certified=EnterpriseCertified.query.filter(EnterpriseCertified.id == certified.enterprise_id).first()
    business = BusinessInfo()
    business.title = params.get('title')
    business.company = certified.name
    business.type = params.get('type')
    business.project_info = params.get('project_info')
    business.demand = params.get('demand')
    business.team_info = params.get('team_info')
    business.creater_userid = user.id
    insert_user(business)
    return make_succ_response(business.id)


@app.route('/api/business/delete_info', methods=['POST'])
def business_delete_info():
    """
    :return:商务信息删除
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    certified = RelationUserCertified.query.filter(RelationUserCertified.user_id == user.id,
                                                 RelationUserCertified.status == 2).first()
    if certified is None:
        return make_err_response('该用户未完成企业认证')
    business = BusinessInfo.query.filter(BusinessInfo.id == params.get('id'), BusinessInfo.is_deleted == 0).first()
    if business.creater_userid != user.id:
        return make_err_response('您没有权限修改该信息')
    business.is_deleted = 1
    insert_user(business)
    return make_succ_response(business.id)


@app.route('/api/business/list_info', methods=['GET'])
def business_list_info():
    """
    :return:获取我发布的商务信息
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    user = User.query.filter(User.openid == wxopenid).first()
    if user is None:
        return make_err_response('用户不存在')
    result = BusinessInfo.query.filter(BusinessInfo.creater_userid == user.id, BusinessInfo.is_deleted == 0).order_by(
        BusinessInfo.create_time.desc()).all()
    data = [item.get() for item in result]
    return make_succ_response(data)


@app.route('/api/business/list_all_info', methods=['GET'])
def business_list_all_info():
    """
    :return:获取商务信息列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    title = request.args.get('title')
    type = request.args.get('type')
    chat_object_type = request.args.get('chat_object_type', "所有")
    data = []
    if chat_object_type == "所有":
        business_list_info = get_business_list(title, type)
        data.extend(business_list_info)
        enterprise_list_info = get_enterprise_list(title, type)
        data.extend(enterprise_list_info)
    if chat_object_type == "项目":
        business_list_info = get_business_list(title, type)
        data.extend(business_list_info)
    if chat_object_type == "公司":
        enterprise_list_info = get_enterprise_list(title, type)
        data.extend(enterprise_list_info)
    return make_succ_response(data)


@app.route('/api/business/negotiation', methods=['POST'])
def business_negotiation():
    """
    :return:商务洽谈
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    negotiation = BusinessNegotiation.query.filter(
        BusinessNegotiation.chat_object_type == params.get('chat_object_type'),
        BusinessNegotiation.chat_object_id == params.get('chat_object_id'),
        BusinessNegotiation.creater_userid == user.id).first()
    if negotiation is not None:
        return make_err_response('该用户已经提交过该洽谈信息')
    negotiation = BusinessNegotiation()
    negotiation.chat_object_type = params.get('chat_object_type')
    negotiation.chat_object_id = params.get('chat_object_id')
    negotiation.creater_userid = user.id
    negotiation.negotation_intention = params.get('negotation_intention')
    if params.get('chat_object_type') == '项目':
        business = BusinessInfo.query.filter(BusinessInfo.id == params.get('chat_object_id'),
                                             BusinessInfo.is_deleted == 0).first()
        if business is None:
            return make_err_response('该商务信息不存在')
        else:
            negotiation.negotation_userid = business.creater_userid
            negotiation.chat_object_name = business.title
    elif params.get('chat_object_type') == '企业':
        enterprise = EnterpriseCertified.query.filter(EnterpriseCertified.id == params.get('chat_object_id'),
                                                      EnterpriseCertified.is_deleted == 0).first()
        if enterprise is None:
            return make_err_response('该企业不存在')
        else:
            negotiation.negotation_userid = enterprise.user_id
            negotiation.chat_object_name = enterprise.name
    insert_user(negotiation)
    return make_succ_response(negotiation.id)


@app.route('/api/business/list_send_negotiation', methods=['GET'])
def business_list_send_negotiation():
    """
    :return:获取发起洽谈列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    status = request.args.get('status')
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    query = BusinessNegotiation.query.filter(BusinessNegotiation.creater_userid == user.id)
    if status is not None:
        query = query.filter(
            or_(BusinessNegotiation.status == status))
    result = query.order_by(BusinessNegotiation.create_time.desc()).all()
    data = []
    for item in result:
        negotiation = item.get(True)
        if negotiation.get("status") == 2:
            user = User.query.filter(User.id == negotiation.get("negotation_userid")).first()
            negotiation["phone"] = user.phone
        data.append(negotiation)
    return make_succ_response(data)


@app.route('/api/business/list_receive_negotiation', methods=['GET'])
def business_list_receive_negotiation():
    """
    :return:获取收到洽谈列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    status = request.args.get('status')
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    query = BusinessNegotiation.query.filter(BusinessNegotiation.negotation_userid == user.id)
    if status is not None:
        query = query.filter(
            or_(BusinessNegotiation.status == status))
    result = query.order_by(BusinessNegotiation.create_time.desc()).all()
    data = []
    for item in result:
        negotiation = item.get(False)
        if negotiation.get("status") == 2:
            user = User.query.filter(User.id == negotiation.get("creater_userid")).first()
            negotiation["phone"] = user.phone
        data.append(negotiation)
    return make_succ_response(data)


@app.route('/api/business/negotiation_opt', methods=['POST'])
def business_negotiation_opt():
    """
    :return:商务洽谈
    """
    # 获取请求体参数
    params = request.get_json()
    negotiation = BusinessNegotiation.query.filter(
        BusinessNegotiation.id == params.get('id'),
        BusinessNegotiation.is_deleted == 0).first()
    negotiation.status = params.get('status')
    insert_user(negotiation)
    return make_succ_response(negotiation.id)


@app.route('/api/business/list_meeting_room', methods=['GET'])
def business_list_meeting_room():
    """
    :return:获取会议室列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    data = MeetingRoom.query.all()
    return make_succ_response([item.get() for item in data])


@app.route('/api/business/get_meeting_room_available_time', methods=['GET'])
def business_get_meeting_room_available_time():
    """
    :return:获取会议室可以预约时间
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    date = request.args.get('date')
    meeting_room_id = request.args.get('meeting_room_id')
    meeting_room_use_time = MeetingReservation.query.filter(
        MeetingReservation.meeting_room_id == meeting_room_id,
        func.date(MeetingReservation.start_time) == date).all()
    meeting_room_use_time = [item.start_time.strftime('%H:%M') for item in meeting_room_use_time]
    meeting_room_available_time = []
    day = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    start_work = datetime.time(9, 0)
    end_work = datetime.time(18, 0)
    cursor = datetime.datetime.combine(day, start_work)
    close = datetime.datetime.combine(day, end_work)
    while cursor + datetime.timedelta(minutes=30) <= close:
        if cursor.time().strftime('%H:%M') in meeting_room_use_time:
            cursor += datetime.timedelta(minutes=30)
            continue
        meeting_room_available_time.append(
            (cursor.time().strftime('%H:%M'), (cursor + datetime.timedelta(minutes=30)).time().strftime('%H:%M')))
        cursor += datetime.timedelta(minutes=30)
    return make_succ_response(meeting_room_available_time)


@app.route('/api/business/book_meeting_room', methods=['POST'])
def business_book_meeting_room():
    """
    :return:预约会议室
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    r = MeetingReservation.query.filter(
        MeetingReservation.creater_id == user.id,
        MeetingReservation.is_deleted == 0,
        func.date(MeetingReservation.start_time) == params.get('start_time')[:10]).all()
    if len(r) == 2:
        return make_err_response('每个用户每天可预约两个会议室')
    reservation = MeetingReservation()
    reservation.meeting_room_id = params.get('meeting_room_id')
    reservation.start_time = params.get('start_time')
    reservation.end_time = params.get('end_time')
    reservation.negotation_id = params.get('negotation_id')
    reservation.creater_id = user.id
    insert_user(reservation)
    return make_succ_response(reservation.id)


@app.route('/api/business/modify_meeting_room', methods=['POST'])
def business_modify_meeting_room():
    """
    :return:修改预约会议室
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    reservation = MeetingReservation.query.filter(
        MeetingReservation.id == params.get('meeting_book_id')).first()
    reservation.meeting_room_id = params.get('meeting_room_id')
    reservation.start_time = params.get('start_time')
    reservation.end_time = params.get('end_time')
    insert_user(reservation)
    return make_succ_response(reservation.id)


@app.route('/api/business/delete_meeting_room', methods=['POST'])
def business_delete_meeting_room():
    """
    :return:删除预约会议室
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    reservation = MeetingReservation.query.filter(
        MeetingReservation.id == params.get('meeting_room_id'), MeetingReservation.creater_id == user.id).first()
    if reservation is None:
        return make_err_response('用户无权限删除预约会议室')
    reservation.is_deleted = 1
    insert_user(reservation)
    return make_succ_response(reservation.id)


@app.route('/api/business/checkin_meeting_room', methods=['POST'])
def business_checkin_meeting_room():
    """
    :return:签到会议室
    """
    # 获取请求体参数
    params = request.get_json()
    user = User.query.filter(User.openid == request.headers['X-WX-OPENID']).first()
    if user is None:
        return make_err_response('用户不存在')
    reservation = MeetingReservation.query.filter(
        MeetingReservation.id == params.get('meeting_room_id'), MeetingReservation.creater_id == user.id).first()
    if reservation is None:
        return make_err_response('用户无权限签到会议室')
    reservation.checkin = 1
    insert_user(reservation)
    return make_succ_response(reservation.id)


@app.route('/api/business/get_meeting_record', methods=['GET'])
def business_get_meeting_record():
    """
    :return:获取会议室列表
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    user = User.query.filter(User.openid == wxopenid).first()
    if user is None:
        return make_err_response('用户不存在')
    result, total = get_meeting_record_list_byuserid(user.id, page, page_size)
    return make_succ_page_response(data=result, code=0, total=total)


@app.route('/api/refresh_ca_identity_verification', methods=['GET'])
def refresh_ca_identity_verification():
    """
    :return:刷新CA身份验证
    """
    # 获取请求体参数
    wxopenid = request.headers['X-WX-OPENID']
    users = User.query.filter(User.status == 2, User.type != '管理员', User.is_deleted == 0, User.name is not None,
                             User.phone is not None, User.code is not None, User.identity_verification ==0).all()
    for user in users:
        user.identity_verification = CA_identification(user.name, user.phone, user.code)
        insert_user(user)
    return make_succ_response(user.id)
