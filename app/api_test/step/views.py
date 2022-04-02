#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/4/16 9:42
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
from flask import request

from app.api_test import api_test
from app.utils import restful
from app.utils.required import login_required
from app.baseView import BaseMethodView
from app.baseModel import db
from .models import Step
from .forms import GetStepListForm, GetStepForm, AddStepForm, EditStepForm


@api_test.route('/step/list', methods=['GET'])
@login_required
def get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm()
    if form.validate():
        step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
        return restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])
    return restful.error(form.get_error())


@api_test.route('/step/changeIsRun', methods=['PUT'])
@login_required
def change_step_status():
    """ 修改步骤状态（是否执行） """
    with db.auto_commit():
        Step.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
    return restful.success(f'步骤已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@api_test.route('/step/sort', methods=['PUT'])
@login_required
def change_step_sort():
    """ 更新步骤的排序 """
    Step.change_sort(request.json.get('List'), request.json.get('pageNum', 0), request.json.get('pageSize', 0))
    return restful.success(msg='修改排序成功')


@api_test.route('/step/copy', methods=['POST'])
@login_required
def copy_step():
    """ 复制步骤 """
    old = Step.get_first(id=request.json.get('id')).to_dict()
    old['name'] = f"{old['name']}_copy"
    old['num'] = Step.get_insert_num(case_id=old['case_id'])
    step = Step().create(old, "headers", "params", "data_form", "data_json", "extracts", "validates", "data_driver")
    return restful.success(msg='步骤复制成功', data=step.to_dict())


class StepMethodView(BaseMethodView):

    def get(self):
        """ 获取步骤 """
        form = GetStepForm()
        if form.validate():
            return restful.success('获取成功', data=form.step.to_dict())
        return restful.error(form.get_error())

    def post(self):
        """ 新增步骤 """
        form = AddStepForm()
        if form.validate():
            form.num.data = Step.get_insert_num(case_id=form.case_id.data)
            step = Step().create(
                form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates', 'data_driver')
            return restful.success(f'步骤【{step.name}】新建成功', data=step.to_dict())
        return restful.error(form.get_error())

    def put(self):
        """ 修改步骤 """
        form = EditStepForm()
        if form.validate():
            form.step.update(
                form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates', 'data_driver'
            )
            return restful.success(msg=f'步骤【{form.step.name}】修改成功', data=form.step.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        """ 删除步骤 """
        form = GetStepForm()
        if form.validate():
            form.step.delete()
            return restful.success(f'步骤【{form.step.name}】删除成功')
        return restful.error(form.get_error())


api_test.add_url_rule('/step', view_func=StepMethodView.as_view('step'))
