#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
import json

from flask import request
from flask_login import current_user

from ..module.models import Module
from ..user.models import User
from ...utils import restful
from ...utils.required import login_required
from ...utils.changSort import num_sort
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from ..case.models import Case
from ..step.models import Step
from .forms import AddCaseForm, EditCaseForm, FindCaseForm, DeleteCaseForm, GetCaseForm, RunCaseForm
from ...utils.runHttpRunner import RunCase


def create_step(index, case_id, step):
    """ 插入步骤 """
    return Step(
        num=index,
        is_run=step['is_run'],
        run_times=step['run_times'],
        name=step['name'],
        up_func=step['up_func'],
        down_func=step['down_func'],
        headers=Step.dumps(step['headers']),
        params=Step.dumps(step['params']),
        data_form=Step.dumps(step['data_form']),
        data_json=Step.dumps(step['data_json']),
        extracts=Step.dumps(step['extracts']),
        validates=Step.dumps(step['validates']),
        project_id=step['project_id'],
        case_id=case_id,
        api_id=step['api_id'],
        create_user=current_user.id
    )


@api.route('/case/list', methods=['get'])
@login_required
def get_case_list():
    """ 根据模块查找用例list """
    form = FindCaseForm()
    if form.validate():
        return restful.success(data=Case.make_pagination(form))
    return restful.fail(form.get_error())


@api.route('/case/run', methods=['POST'])
@login_required
def run_case():
    """ 运行测试用例，并生成报告 """
    form = RunCaseForm()
    if form.validate():
        runner = RunCase(project_id=Module.get_first(id=form.case.module_id).project_id, case_id=form.caseId.data)
        json_result = runner.run_case()
        runner.build_report(json_result, User.get_first(id=current_user.id), form.case.name, 'case')
        return restful.success(msg='测试完成', data={'report_id': runner.new_report_id, 'data': json.loads(json_result)})
    return restful.fail(form.get_error())


@api.route('/case/changeIsRun', methods=['PUT'])
@login_required
def change_case_status():
    """ 修改用例状态（是否执行） """
    with db.auto_commit():
        Case.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
    return restful.success(f'用例已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@api.route('/case/copy', methods=['GET'])
@login_required
def copy_case():
    """ 复制用例，返回复制的用例和步骤 """
    # 复制用例
    old_case = Case.get_first(id=request.args.get('id'))
    with db.auto_commit():
        new_case = Case()
        new_case.create(old_case.to_dict(), 'func_files', 'variables', 'headers')
        new_case.name = old_case.name + '_01'
        new_case.create_user = current_user.id
        new_case.num = Case.get_new_num(None, module_id=old_case.module_id)
        db.session.add(new_case)

    # 复制步骤
    old_step_list = Step.query.filter_by(case_id=request.args.get('id')).order_by(Step.num.asc()).all()
    with db.auto_commit():
        for old_step in old_step_list:
            db.session.add(create_step(old_step.num, new_case.id, old_step.to_dict()))
    return restful.success(f'复制成功', data={'case': new_case.to_dict(),
                                          'steps': [step.to_dict() for step in Step.get_all(case_id=new_case.id)]})


class CaseView(BaseMethodView):
    """ 用例管理 """

    def get(self):
        form = GetCaseForm()
        if form.validate():
            return restful.success('获取成功', data=form.case.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddCaseForm()
        if form.validate():
            form.create_user.data = current_user.id
            num = Case.get_new_num(form.num.data, module_id=form.module_id.data)

            # 保存用例
            with db.auto_commit():
                new_case = Case()
                form.set_attr(num=num)
                new_case.create(form.data, 'func_files', 'variables', 'headers')
                db.session.add(new_case)

            # 测试步骤顺序有改动则重新排序
            Step.sort_num_by_list(form.steps.data)
            return restful.success('用例新建成功', data=new_case.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditCaseForm()
        if form.validate():
            num = Case.get_new_num(form.num.data, module_id=form.module_id.data)
            case, case_list = form.old_data, Case.get_all(module_id=form.module_id.data)

            # 修改用例
            with db.auto_commit():
                num_sort(num, case.num, case_list, case)
                case.update(form.data, 'func_files', 'variables', 'headers')
            # 测试步骤顺序有改动则重新排序
            Step.sort_num_by_list(form.steps.data)
            return restful.success(msg='修改成功', data=case.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteCaseForm()
        if form.validate():
            case, steps = form.case, Step.get_all(case_id=form.id.data)

            # 数据有依赖关系，先删除步骤，再删除用例
            if steps:
                with db.auto_commit():
                    for step in steps:
                        db.session.delete(step)
            with db.auto_commit():
                db.session.delete(case)
            return restful.success(f'用例 {case.name} 删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/case', view_func=CaseView.as_view('case'))
