#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

import json

from flask_login import current_user

from ...utils import restful
from ...utils.required import login_required
from ...utils.runHttpRunner import RunApi
from ...utils.changSort import num_sort
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from ..apiMsg.models import ApiMsg
from ..step.models import Step
from ..module.models import Module
from .forms import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiById
from config.config import assert_mapping_list, method_mapping


@api.route('/apiMsg/assertMapping', methods=['GET'])
@login_required
def assert_mapping():
    """ 断言类型 """
    return restful.success('获取成功', data=assert_mapping_list)


@api.route('/apiMsg/methods', methods=['GET'])
@login_required
def methods_mapping():
    """ 请求方法 """
    return restful.success('获取成功', data=method_mapping)


@api.route('/apiMsg/list', methods=['GET'])
@login_required
def api_list():
    """ 根据模块查接口list """
    form = ApiListForm()
    if form.validate():
        return restful.success(data=ApiMsg.make_pagination(form))
    return restful.fail(form.get_error())


@api.route('/apiMsg/run', methods=['POST'])
@login_required
def run_api_msg():
    """ 跑接口信息 """
    form = RunApiMsgForm()
    if form.validate():
        json_result = RunApi(form.projectId.data, api_ids=form.apis.data).run_case()
        return restful.success(msg='测试完成', data={'data': json.loads(json_result)})
    return restful.fail(form.get_error())


class ApiMsgView(BaseMethodView):
    """ 接口信息 """

    def get(self):
        form = GetApiById()
        if form.validate():
            return restful.success(data=form.api.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddApiForm()
        form.create_user.data = current_user.id
        if form.validate():
            with db.auto_commit():
                form.num.data, new_api = form.new_num(), ApiMsg()
                new_api.create(form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates')
                db.session.add(new_api)
            return restful.success(f'接口 {form.name.data} 新建成功', data=new_api.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditApiForm()
        if form.validate():
            old, list_data, new_num = form.old, Module.get_first(id=form.module_id.data).api_msg.all(), form.new_num()
            num_sort(new_num, old.num, list_data, old)
            with db.auto_commit():
                old.update(form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates')
            return restful.success(f'接口 {form.name.data} 修改成功', old.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteApiForm()
        if form.validate():
            with db.auto_commit():
                # 同步删除接口信息下对应用例下的接口步骤信息
                for case_data in Step.get_all(api_id=form.id.data):
                    db.session.delete(case_data)
                db.session.delete(form.api)
            return restful.success('删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/apiMsg', view_func=ApiMsgView.as_view('apiMsg'))
