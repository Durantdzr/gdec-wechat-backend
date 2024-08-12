from datetime import datetime
from flask import render_template, request
from run import app
# from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import ConferenceInfo
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response

@app.route('/api/conference/get_information_list', methods=['GET'])
def get_total_():
    """
        :return:提交预约
        """
    # 获取请求体参数
    result=ConferenceInfo.query.all()
    return make_succ_response([item.get() for item in result])