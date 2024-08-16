# encoding: utf-8
"""
@version: python3.9
@software: PyCharm
@file: mangerviews.py
@describe: 
@time: 2024/8/15 1:20 PM
"""
from flask import request
from run import app
from wxcloudrun.dao import update_user_statusbyid, insert_user, get_guests_list
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule, User, ConferenceHall, RelationFriend
from wxcloudrun.response import make_succ_page_response, make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, valid_image, vaild_password, uploadwebfile
from datetime import timedelta
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import uuid
import config
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
    access_token = create_access_token(identity=username, expires_delta=timedelta(days=1))
    return make_succ_response({"access_token": access_token}, code=200)


@app.route('/api/manage/logout', methods=['POST'])
@jwt_required()
def logout():
    """
        :return:用户登出
        """
    operator = get_jwt_identity()
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
    users = User.query.filter(User.name.like('%' + name + '%'), User.status != 2, User.is_deleted == 0).paginate(page,
                                                                                                                 per_page=page_size,
                                                                                                                 error_out=False)
    return make_succ_page_response([user.get_full() for user in users.items], code=200, total=users.total)


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
    params = request.get_json()
    user = User()
    user.name = params.get('name')
    user.company = params.get('company')
    user.title = params.get('title')
    user.guest_info = params.get('info')
    user.img_url = params.get('cdn_param')
    user.type = '嘉宾'
    user.status = 2
    insert_user(user)
    data = get_guests_list()
    uploadwebfile(data, file='get_guest_list.json')
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
    insert_user(user)
    data = get_guests_list()
    uploadwebfile(data, file='get_guest_list.json')
    return make_succ_response(user.id, code=200)

@app.route('/api/manage/delete_guest', methods=['post'])
@jwt_required()
def delete_guest():
    """
        :return:编辑嘉宾用户
        """
    operator = get_jwt_identity()
    params = request.get_json()
    user = User.query.filter_by(id=params.get('id')).first()
    user.is_deleted = 1
    insert_user(user)
    data = get_guests_list()
    uploadwebfile(data, file='get_guest_list.json')
    return make_succ_response(user.id, code=200)

@app.route('/api/manage/get_guest_list', methods=['GET'])
@jwt_required()
def get_guest_list():
    """
    :return:获取嘉宾列表
    """
    # 获取请求体参数
    data = get_guests_list()
    return make_succ_response(data,code=200)

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
        filename='guest/' + str(u) + format
        file.save(filename)
        uploadfile(filename)
        return make_succ_response({'img_url':'https://{}.tcb.qcloud.la/{}'.format(config.COS_BUCKET, filename),"cdn_param":filename},code=200)
    else:
        return make_err_response('请上传文件')