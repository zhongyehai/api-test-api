#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

from threading import Thread

from flask import request, send_from_directory
from flask_login import current_user

from ..module.models import Module
from ..report.models import Report
from ...utils import restful
from ...utils.globalVariable import TEMPLATE_ADDRESS
from ...utils.parseExcel import parse_file_content
from ...utils.required import login_required
from ...utils.runHttpRunner import RunApi
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from ..apiMsg.models import ApiMsg
from ..step.models import Step
from ..config.models import Config
from .forms import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiById
from config.config import assert_mapping_list


@api.route('/apiMsg/assertMapping', methods=['GET'])
@login_required
def assert_mapping():
    """ 断言类型 """
    return restful.success('获取成功', data=assert_mapping_list)


@api.route('/apiMsg/methods', methods=['GET'])
@login_required
def methods_mapping():
    """ 获取配置的请求方法列表 """
    return restful.success(
        '获取成功',
        data=[{'value': method} for method in Config.get_first(name='http_methods').value.split(',')])


@api.route('/apiMsg/list', methods=['GET'])
@login_required
def get_api_list():
    """ 根据模块查接口list """
    form = ApiListForm()
    if form.validate():
        return restful.success(data=ApiMsg.make_pagination(form))


@api.route('/apiMsg/upload', methods=['POST'])
@login_required
def api_upload():
    """ 从excel中导入接口 """
    file, module, user_id = request.files.get('file'), Module.get_first(id=request.form.get('id')), current_user.id
    if not module:
        return restful.fail('模块不存在')
    if file and file.filename.endswith('xls'):
        excel_data = parse_file_content(file.read())  # [{'请求类型': 'get', '接口名称': 'xx接口', 'url': '/api/v1/xxx'}]
        with db.auto_commit():
            for api_data in excel_data:
                new_api = ApiMsg()
                for key, value in api_data.items():
                    if hasattr(new_api, key):
                        setattr(new_api, key, value)
                new_api.method = api_data.get('method', 'post').upper()
                new_api.num = new_api.get_new_num(None)
                new_api.project_id = module.project_id
                new_api.module_id = module.id
                new_api.create_user = user_id
                db.session.add(new_api)
        return restful.success('接口导入成功')
    return restful.fail('请上传后缀为xls的Excel文件')


@api.route('/apiMsg/template/download', methods=['GET'])
def download_api_template():
    """ 下载接口模板 """
    return send_from_directory(TEMPLATE_ADDRESS, '接口导入模板.xls', as_attachment=True)


@api.route('/apiMsg/run', methods=['POST'])
@login_required
def run_api_msg():
    """ 跑接口信息 """
    form = RunApiMsgForm()
    if form.validate():
        run_api = form.api
        project_id = run_api.project_id
        report = Report.get_new_report(run_api.name, 'api', current_user.name, current_user.id, project_id)

        # 新起线程运行接口
        Thread(
            target=RunApi(
                project_id=form.projectId.data, run_name=report.name, api_ids=form.apis.data, report_id=report.id
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return restful.fail(form.get_error())


@api.route('/apiMsg/sort', methods=['put'])
@login_required
def change_api_sort():
    """ 更新接口的排序 """
    api_id_list, num, size = request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize')
    with db.auto_commit():
        for index, api_id in enumerate(api_id_list):
            api_info = ApiMsg.get_first(id=api_id)
            api_info.num = (num - 1) * size + index
    return restful.success(msg='修改排序成功')


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
                new_api = ApiMsg()
                new_api.create(form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates')
                new_api.num = form.new_num()
                db.session.add(new_api)
            return restful.success(f'接口 {form.name.data} 新建成功', data=new_api.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditApiForm()
        if form.validate():
            old_api = form.old
            with db.auto_commit():
                old_api.update(form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates')
            return restful.success(f'接口 {form.name.data} 修改成功', old_api.to_dict())
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
