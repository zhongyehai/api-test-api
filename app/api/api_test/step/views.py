#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/4/16 9:42
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
from flask import request

from ... import api
from ....utils import restful
from ....utils.required import login_required
from ....baseView import BaseMethodView
from ....baseModel import db
from .models import Step
from .forms import GetStepListForm, GetStepForm, AddStepForm, EditStepForm


@api.route('/step/list', methods=['GET'])
@login_required
def get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm()
    if form.validate():
        step_obj_list = Step.query.filter_by(case_id=form.caseId.data).order_by(Step.num.asc()).all()
        return restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])
    return restful.error(form.get_error())


@api.route('/step/changeIsRun', methods=['PUT'])
@login_required
def change_step_status():
    """ 修改步骤状态（是否执行） """
    with db.auto_commit():
        Step.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
    return restful.success(f'步骤已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@api.route('/step/sort', methods=['put'])
@login_required
def change_step_sort():
    """ 更新步骤的排序 """
    with db.auto_commit():
        for index, step_id in enumerate(request.json.get('List')):
            step = Step.get_first(id=step_id)
            step.num = index
    return restful.success(msg='修改排序成功')


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
            with db.auto_commit():
                step = Step()
                step.create(
                    form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates', 'data_driver')
                step.num = Step.get_new_num(None, case_id=form.case_id.data)
                db.session.add(step)
            return restful.success('步骤新建成功', data=step.to_dict())
        return restful.error(form.get_error())

    def put(self):
        """ 修改步骤 """
        form = EditStepForm()
        if form.validate():
            step = form.step
            with db.auto_commit():
                step.update(
                    form.data, 'headers', 'params', 'data_form', 'data_json', 'extracts', 'validates', 'data_driver')
            return restful.success(msg='修改成功', data=form.step.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        """ 删除步骤 """
        form = GetStepForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.step)
            return restful.success(f'步骤 {form.step.name} 删除成功')
        return restful.error(form.get_error())


api.add_url_rule('/step', view_func=StepMethodView.as_view('step'))