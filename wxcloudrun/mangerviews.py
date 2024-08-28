# encoding: utf-8
"""
@version: python3.9
@software: PyCharm
@file: mangerviews.py
@describe: 
@time: 2024/8/15 1:20 PM
"""
import datetime
import json

from flask import request, send_file
from run import app
from wxcloudrun.dao import update_user_statusbyid, insert_user, get_guests_list, get_review_conference_list, \
    update_schedule_statusbyid, refresh_cooperater, refresh_guest, refresh_guest_info, get_hall_schedule_bydate, \
    get_live_data, refresh_conference_info, refresh_schedule_info, delete_reocrd, get_hall_schedule_byid
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule, User, ConferenceHall, RelationFriend, \
    ConferenCoopearter, Media
from wxcloudrun.response import make_succ_page_response, make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, valid_image, vaild_password, uploadwebfile, \
    download_cdn_file, zip_folder, get_ticket, get_urllink
from datetime import timedelta
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
import uuid
import config
import requests
import base64
import pandas as pd
import os


@app.route('/api/manage/login', methods=['POST'])
def login():
    """
        :return:用户登录
        """
    params = request.get_json()
    username = params.get('username')
    pwdhash = params.get('pwdhash')
    user = User.query.filter_by(name=username, type='管理员').first()
    if not user:
        return make_err_response('不存在该用户')
    if pwdhash != vaild_password(user.password):
        return make_err_response('密码错误')
    additional_claims = {"forum": user.forum}
    access_token = create_access_token(identity=username, expires_delta=timedelta(days=1),
                                       additional_claims=additional_claims)
    if user.forum == '':
        branch = 0
    else:
        branch = 1
    return make_succ_response({"access_token": access_token, "branch": branch}, code=200)


@app.route('/api/manage/logout', methods=['POST'])
@jwt_required()
def logout():
    """
        :return:用户登出
        """
    forum = get_jwt().get("forum", "")
    return make_succ_response('用户已登出', code=200)


@app.route('/api/manage/get_register_list', methods=['GET'])
@jwt_required()
def get_register_list():
    """
        :return:获取用户审核列表
    """
    operator = get_jwt_identity()
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    name = request.args.get('name', default='', type=str)
    status = request.args.get('status', type=int)
    if status is None:
        users = User.query.filter(User.name.like('%' + name + '%'), User.status != 2, User.is_deleted == 0).paginate(
            page,
            per_page=page_size,
            error_out=False)
    else:
        users = User.query.filter(User.name.like('%' + name + '%'), User.status == status,
                                  User.is_deleted == 0).paginate(
            page,
            per_page=page_size,
            error_out=False)
    return make_succ_page_response([user.get_full() for user in users.items], code=200, total=users.total)


@app.route('/api/manage/get_user_list', methods=['GET'])
@jwt_required()
def get_success_user_list():
    """
        :return:获取已审核用户列表
    """
    operator = get_jwt_identity()
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    name = request.args.get('name', default='', type=str)
    users = User.query.filter(User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                              User.type.notin_(['管理员', '嘉宾'])).paginate(page,
                                                                             per_page=page_size,
                                                                             error_out=False)
    return make_succ_page_response([user.get_full() for user in users.items], code=200, total=users.total)


@app.route('/api/manage/edit_user', methods=['post'])
@jwt_required()
def edit_user():
    """
        :return:编辑用户
        """
    operator = get_jwt_identity()
    params = request.get_json()
    user = User.query.filter_by(id=params.get('id')).first()
    user.name = params.get('name')
    user.company = params.get('company')
    user.title = params.get('title')
    user.phone = params.get('phone')
    user.img_url = params.get('cdn_param')
    user.type = params.get('type')
    insert_user(user)
    return make_succ_response(user.id, code=200)


@app.route('/api/manage/delete_user', methods=['post'])
@jwt_required()
def delete_user():
    """
        :return:删除用户
        """
    operator = get_jwt_identity()
    params = request.get_json()
    user = User.query.filter_by(id=params.get('id')).first()
    user.is_deleted = 1
    insert_user(user)
    return make_succ_response(user.id, code=200)


@app.route('/api/manage/review_register', methods=['post'])
@jwt_required()
def review_register():
    """
        :return:审核用户注册
        """
    operator = get_jwt_identity()
    params = request.get_json()
    opt = params.get('opt')
    userlist = params.get('userlist')
    if opt == 'agree':
        update_user_statusbyid(userlist, 2)
    elif opt == 'unagree':
        update_user_statusbyid(userlist, 1)
    else:
        return make_err_response('无该操作方法')
    return make_succ_response('操作成功', code=200)


@app.route('/api/manage/add_guest', methods=['post'])
@jwt_required()
def add_guest():
    """
        :return:新增嘉宾用户
        """
    operator = get_jwt_identity()
    forum = get_jwt().get("forum", "")
    params = request.get_json()
    user = User()
    user.name = params.get('name')
    user.company = params.get('company')
    user.title = params.get('title')
    user.guest_info = params.get('info')
    user.img_url = params.get('cdn_param')
    user.type = '嘉宾'
    user.status = 2
    user.forum = forum
    if params.get('order') is not None:
        user.order = params.get('order')
    insert_user(user)
    refresh_guest()
    refresh_guest_info(user.id)
    return make_succ_response(user.id, code=200)


@app.route('/api/manage/edit_guest', methods=['post'])
@jwt_required()
def edit_guest():
    """
        :return:编辑嘉宾用户
        """
    operator = get_jwt_identity()
    params = request.get_json()
    user = User.query.filter_by(id=params.get('id')).first()
    user.name = params.get('name')
    user.company = params.get('company')
    user.title = params.get('title')
    user.guest_info = params.get('info')
    user.img_url = params.get('cdn_param')
    user.order = params.get('order')
    insert_user(user)
    refresh_guest()
    refresh_guest_info(user.id)
    return make_succ_response(user.id, code=200)


@app.route('/api/manage/delete_guest', methods=['post'])
@jwt_required()
def delete_guest():
    """
        :return:删除嘉宾用户
        """
    operator = get_jwt_identity()
    params = request.get_json()
    user = User.query.filter_by(id=params.get('id')).first()
    user.is_deleted = 1
    insert_user(user)
    refresh_guest()
    return make_succ_response(user.id, code=200)


@app.route('/api/manage/get_guest_list', methods=['GET'])
@jwt_required()
def manage_get_guest_list():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    name = request.args.get('name', '')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=200, type=int)
    forum1 = request.args.get('forum', '')
    forum = get_jwt().get("forum", "")
    if forum1 != '' and forum == '':
        forum = forum1
    guests = User.query.filter(User.type == '嘉宾', User.is_deleted == 0, User.name.like('%' + name + '%'),
                               User.forum.like('%' + forum + '%')).order_by(
        User.order.desc()).paginate(
        page,
        per_page=page_size,
        error_out=False)
    data = [guest.get_guest() for guest in guests.items]
    return make_succ_page_response(data, code=200, total=guests.total)


@app.route('/api/manage/upload_img', methods=['post'])
@jwt_required()
def upload_img():
    """
        :return:上传图片
        """
    operator = get_jwt_identity()
    file = request.files['file']
    if file:  # 这里可以加入文件类型判断等逻辑
        format = valid_image(file.stream)
        u = uuid.uuid4()
        filename = 'guest/' + str(u) + format
        file.save(filename)
        uploadfile(filename)
        return make_succ_response(
            {'img_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, filename), "cdn_param": filename},
            code=200)
    else:
        return make_err_response('请上传文件')


@app.route('/api/manage/upload_base64img', methods=['post'])
@jwt_required()
def upload_base64img():
    """
        :return:上传图片
        """
    params = request.get_json()
    src = params.get('img_encode')
    data = src.split(',')[1]
    image_data = base64.b64decode(data)
    u = uuid.uuid4()
    filename = 'guest/' + str(u) + '.jpeg'
    with open(filename, 'wb') as file_to_save:
        file_to_save.write(image_data)
    uploadfile(filename)
    return make_succ_response(
        {'img_url': 'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, filename), "cdn_param": filename})


@app.route('/api/manage/get_hall_schedule', methods=['GET'])
@jwt_required()
def manage_get_hall_schedule():
    """
        :return:大会会场日程
    """
    # 获取请求体参数
    title = request.args.get('title', '')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    forum = get_jwt().get("forum", "")
    result = ConferenceSchedule.query.filter(ConferenceSchedule.is_deleted == 0,
                                             ConferenceSchedule.title.like('%' + title + '%'),
                                             ConferenceSchedule.forum.like('%' + forum + '%')).paginate(page,
                                                                                                        per_page=page_size,
                                                                                                        error_out=False)
    data = []
    for item in result.items:
        schedule = item.get_schedule()
        schedule['guest_info'] = []
        if len(schedule.get('guest_id', [])) > 0:
            for guest in schedule.get('guest_id', []):
                user = User.query.filter_by(id=guest).first()
                schedule['guest_info'].append(user.get_guest())
        data.append(schedule)
    return make_succ_page_response(data, code=200, total=result.total)


@app.route('/api/manage/get_hall_list', methods=['GET'])
@jwt_required()
def manage_get_hall_list():
    """
        :return:大会会场列表
    """
    # 获取请求体参数
    result = ConferenceHall.query.all()
    return make_succ_response([{'hall_name': item.name, 'id': item.id} for item in result], code=200)


@app.route('/api/manage/add_hall_schedule', methods=['post'])
@jwt_required()
def add_hall_schedule():
    """
        :return:新增日程
        """
    forum = get_jwt().get("forum")
    operator = get_jwt_identity()
    params = request.get_json()
    schedule = ConferenceSchedule()
    schedule.title = params.get('title')
    schedule.hall = params.get('hall')
    schedule.location = params.get('location')
    schedule.conference_date = params.get('conference_date')
    schedule.begin_time = params.get('begin_time')
    schedule.end_time = params.get('end_time')
    schedule.status = params.get('status')
    schedule.guest = ','.join([str(item) for item in params.get('guest_id')])
    schedule.live_status = params.get('live_status')
    schedule.live_url = params.get('live_url')
    schedule.record_url = params.get('record_url')
    schedule.org = params.get('org')
    schedule.agenda = json.dumps(params.get('agenda', ''))
    schedule.img_url = params.get('cdn_param')
    schedule.forum = forum
    insert_user(schedule)
    refresh_guest()
    if schedule.live_status:
        data = get_live_data()
        uploadwebfile(data, file='get_live_list.json')
    data = get_hall_schedule_bydate(params.get('conference_date'))
    uploadwebfile(data, file='get_hall_schedule' + params.get('conference_date') + '.json')
    data = get_hall_schedule_byid(schedule.id)
    uploadwebfile(data, file='get_schedule_by_id' + str(schedule.id) + '.json')
    return make_succ_response(schedule.id, code=200)


@app.route('/api/manage/edit_hall_schedule', methods=['post'])
@jwt_required()
def edit_hall_schedule():
    """
        :return:编辑日程
        """
    operator = get_jwt_identity()
    params = request.get_json()
    schedule = ConferenceSchedule.query.filter_by(id=params.get('id')).first()
    schedule.title = params.get('title')
    schedule.hall = params.get('hall')
    schedule.location = params.get('location')
    schedule.conference_date = params.get('conference_date')
    schedule.begin_time = params.get('begin_time')
    schedule.end_time = params.get('end_time')
    schedule.status = params.get('status')
    schedule.guest = ','.join([str(item) for item in params.get('guest_id')])
    schedule.live_status = params.get('live_status')
    schedule.live_url = params.get('live_url')
    schedule.record_url = params.get('record_url')
    schedule.org = params.get('org')
    schedule.agenda = json.dumps(params.get('agenda'))
    schedule.img_url = params.get('cdn_param')
    insert_user(schedule)
    refresh_guest()
    if schedule.live_status:
        data = get_live_data()
        uploadwebfile(data, file='get_live_list.json')
    data = get_hall_schedule_bydate(params.get('conference_date'))
    uploadwebfile(data, file='get_hall_schedule' + params.get('conference_date') + '.json')
    data = get_hall_schedule_byid(schedule.id)
    uploadwebfile(data, file='get_schedule_by_id' + str(schedule.id) + '.json')
    return make_succ_response(schedule.id, code=200)


@app.route('/api/manage/delete_hall_schedule', methods=['post'])
@jwt_required()
def delete_hall_schedule():
    """
        :return:删除日程
        """
    operator = get_jwt_identity()
    params = request.get_json()
    schedule = ConferenceSchedule.query.filter_by(id=params.get('id')).first()
    schedule.is_deleted = 1
    insert_user(schedule)
    refresh_guest()
    data = get_live_data()
    uploadwebfile(data, file='get_live_list.json')
    data = get_hall_schedule_bydate(schedule.conference_date.strftime('%Y-%m-%d'))
    uploadwebfile(data, file='get_hall_schedule' + schedule.conference_date.strftime('%Y-%m-%d') + '.json')
    return make_succ_response(schedule.id, code=200)


@app.route('/api/manage/get_cooperater', methods=['GET'])
@jwt_required()
def get_cooperater():
    """
        :return:大会合作伙伴
    """
    # 获取请求体参数
    name = request.args.get('name', '')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    result = ConferenCoopearter.query.filter(ConferenCoopearter.is_deleted == 0,
                                             ConferenCoopearter.name.like('%' + name + '%')).paginate(page,
                                                                                                      per_page=page_size,
                                                                                                      error_out=False)
    return make_succ_page_response([item.get() for item in result.items], code=200, total=result.total)


@app.route('/api/manage/add_cooperater', methods=['post'])
@jwt_required()
def add_cooperater():
    """
        :return:新增合作伙伴
        """
    operator = get_jwt_identity()
    params = request.get_json()
    cooperater = ConferenCoopearter()
    cooperater.name = params.get('name')
    cooperater.img_url = params.get('cdn_param')
    cooperater.url = params.get('url')
    cooperater.type = params.get('type')
    insert_user(cooperater)
    refresh_cooperater()
    return make_succ_response(cooperater.id, code=200)


@app.route('/api/manage/edit_cooperater', methods=['post'])
@jwt_required()
def edit_cooperater():
    """
        :return:编辑合作伙伴
        """
    operator = get_jwt_identity()
    params = request.get_json()
    cooperater = ConferenCoopearter.query.filter_by(id=params.get('id')).first()
    cooperater.name = params.get('name')
    cooperater.img_url = params.get('cdn_param')
    cooperater.url = params.get('url')
    cooperater.type = params.get('type')
    insert_user(cooperater)
    refresh_cooperater()
    return make_succ_response(cooperater.id, code=200)


@app.route('/api/manage/delete_cooperater', methods=['post'])
@jwt_required()
def delete_cooperater():
    """
        :return:删除合作伙伴
        """
    operator = get_jwt_identity()
    params = request.get_json()
    cooperater = ConferenCoopearter.query.filter_by(id=params.get('id')).first()
    cooperater.is_deleted = 1
    insert_user(cooperater)
    refresh_cooperater()
    return make_succ_response(cooperater.id, code=200)


@app.route('/api/manage/review_conference_sign_up', methods=['post'])
@jwt_required()
def review_conference_sign_up():
    """
        :return:审核用户报名会议
        """
    operator = get_jwt_identity()
    params = request.get_json()
    opt = params.get('opt')
    signuplist = params.get('signuplist')
    if opt == 'agree':
        update_schedule_statusbyid(signuplist, 2)
    elif opt == 'unagree':
        update_schedule_statusbyid(signuplist, 1)
    else:
        return make_err_response('无该操作方法')
    return make_succ_response('操作成功', code=200)


@app.route('/api/manage/get_conference_sign_up', methods=['GET'])
@jwt_required()
def get_conference_sign_up():
    """
        :return:获取报名会议列表
    """
    # 获取请求体参数
    name = request.args.get('user_name', '')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    status = request.args.get('status', default=None, type=int)
    forum = get_jwt().get("forum", "")
    result, total = get_review_conference_list(name, page, page_size, forum, status)
    return make_succ_page_response(result, code=200, total=total)


@app.route('/api/manage/add_media', methods=['post'])
@jwt_required()
def add_media():
    """
        :return:创建门户介质
        """
    operator = get_jwt_identity()
    media = Media()
    params = request.get_json()
    media.name = params.get('name')
    media.info = params.get('info')
    media.type = params.get('type')
    media.media_param = params.get('cdn_param', params.get('doc', ''))
    insert_user(media)
    filename = 'web/' + str(media.id)
    if params.get('type') == '文字':
        with open(filename, 'w') as f:
            f.write(params.get('doc'))
        uploadfile(filename)
    if params.get('type') == '图片':
        response = requests.get('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, params.get('cdn_param')))
        img = response.content
        with open(filename, 'wb') as f:
            f.write(img)
        uploadfile(filename)
    return make_succ_response(media.id, code=200)


@app.route('/api/manage/edit_media', methods=['post'])
@jwt_required()
def edit_media():
    """
        :return:编辑门户介质
        """
    operator = get_jwt_identity()
    params = request.get_json()
    media = Media.query.filter(Media.id == params.get('id')).first()
    media.name = params.get('name')
    media.info = params.get('info')
    media.type = params.get('type')
    media.media_param = params.get('cdn_param', params.get('doc', ''))
    insert_user(media)
    filename = 'web/' + str(media.id)
    if params.get('type') == '文字':
        with open(filename, 'w') as f:
            f.write(params.get('doc'))
        uploadfile(filename)
    if params.get('type') == '图片':
        response = requests.get('https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, params.get('cdn_param')))
        img = response.content
        with open(filename, 'wb') as f:
            f.write(img)
        uploadfile(filename)
    return make_succ_response(media.id, code=200)


@app.route('/api/manage/delete_media', methods=['post'])
@jwt_required()
def delete_media():
    """
        :return:删除门户介质
        """
    operator = get_jwt_identity()
    params = request.get_json()
    media = Media.query.filter(Media.id == params.get('id')).first()
    media.is_deleted = 1
    insert_user(media)
    return make_succ_response(media.id, code=200)


@app.route('/api/manage/get_media', methods=['GET'])
@jwt_required()
def get_media():
    """
        :return:获取门户介质
        """
    operator = get_jwt_identity()
    name = request.args.get('name', '')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    result = Media.query.filter(Media.is_deleted == 0,
                                Media.name.like('%' + name + '%')).paginate(page,
                                                                            per_page=page_size,
                                                                            error_out=False)
    return make_succ_page_response([item.get() for item in result.items], code=200, total=result.total)


@app.route('/api/manage/get_information_list', methods=['GET'])
@jwt_required()
def manage_get_information_list():
    """
        :return:大会资讯列表
        """
    # 获取请求体参数
    title = request.args.get('title', '')
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    result = ConferenceInfo.query.filter(ConferenceInfo.is_deleted == 0,
                                         ConferenceInfo.title.like('%' + title + '%')).paginate(page,
                                                                                                per_page=page_size,
                                                                                                error_out=False)
    return make_succ_page_response([item.get() for item in result.items], code=200, total=result.total)


@app.route('/api/manage/add_information_list', methods=['post'])
@jwt_required()
def manage_add_information_list():
    """
        :return:添加大会资讯
        """
    # 获取请求体参数
    conferenceinfo = ConferenceInfo()
    params = request.get_json()
    conferenceinfo.title = params.get('title')
    conferenceinfo.org = params.get('org')
    conferenceinfo.create_time = params.get('create_time')
    conferenceinfo.file_url = params.get('cdn_param')
    conferenceinfo.link_url = params.get('link_url')
    insert_user(conferenceinfo)
    refresh_conference_info()
    return make_succ_response(conferenceinfo.id, code=200)


@app.route('/api/manage/edit_information_list', methods=['post'])
@jwt_required()
def manage_edit_information_list():
    """
        :return:编辑大会资讯
        """
    # 获取请求体参数
    params = request.get_json()
    conferenceinfo = ConferenceInfo.query.filter(ConferenceInfo.id == params.get('id')).first()
    conferenceinfo.title = params.get('title')
    conferenceinfo.org = params.get('org')
    conferenceinfo.create_time = params.get('create_time')
    conferenceinfo.file_url = params.get('cdn_param')
    conferenceinfo.link_url = params.get('link_url')
    insert_user(conferenceinfo)
    refresh_conference_info()
    return make_succ_response(conferenceinfo.id, code=200)


@app.route('/api/manage/delete_information_list', methods=['post'])
@jwt_required()
def manage_delete_information_list():
    """
        :return:删除大会资讯
        """
    # 获取请求体参数
    params = request.get_json()
    conferenceinfo = ConferenceInfo.query.filter(ConferenceInfo.id == params.get('id')).first()
    conferenceinfo.is_deleted = 1
    insert_user(conferenceinfo)
    refresh_conference_info()
    return make_succ_response(conferenceinfo.id, code=200)


@app.route('/api/manage/download_user_list', methods=['GET'])
@jwt_required()
def download_user_list():
    """
        :return:下载已审核用户列表
    """
    name = request.args.get('name', default='', type=str)
    users = User.query.filter(User.name.like('%' + name + '%'), User.status == 2, User.is_deleted == 0,
                              User.type.notin_(['管理员', '嘉宾'])).all()
    df = pd.read_excel('template.xlsx')
    now = datetime.datetime.now().strftime('%Y-%m-%d%H:%M:%S')
    os.mkdir(now)
    os.mkdir('{}/guest'.format(now))
    for user in users:
        if user.img_url is not None:
            download_cdn_file(user.img_url, '{}/{}'.format(now, user.img_url))
        df = df.append({"序号": user.id, "员工编号": user.id, "姓名": user.name, "性别": "男", "电话号码": user.phone,
                        "证件类型": "身份证" if user.code is None or len(user.code) == 18 else '普通护照',
                        "证件号码": user.code,
                        "照片路径(相对路径)": user.img_url}, ignore_index=True)
    df.to_excel('{}/人员信息表.xlsx'.format(now), index=False)
    zip_folder(now, '数商大会人员信息导出{}.zip'.format(now))
    return send_file('../数商大会人员信息导出{}.zip'.format(now),
                     download_name='数商大会人员信息导出{}.zip'.format(now))


@app.route('/api/manage/get-signature', methods=['GET'])
def get_signature():
    url = request.args.get('url', default='', type=str)
    response, data = get_ticket(url)
    return make_succ_response([response, data])


@app.route('/api/manage/generate_urllink', methods=['GET'])
def generate_urllink():
    return make_succ_response(get_urllink())
