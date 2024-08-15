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
from wxcloudrun.dao import update_user_statusbyid
from wxcloudrun.model import ConferenceInfo, ConferenceSchedule, User, ConferenceHall, RelationFriend
from wxcloudrun.response import make_succ_page_response, make_succ_response, make_err_response
from wxcloudrun.utils import batchdownloadfile, uploadfile, valid_image, vaild_password
from datetime import timedelta
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_current_user


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
    return make_succ_response('操作成功',code=200)
