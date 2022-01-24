#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
import json
from threading import Thread

from flask import request
from flask_login import current_user

from ... import api
from ....utils import restful
from ....utils.required import login_required
from ....utils.runHttpRunner import RunCase
from ....baseView import BaseMethodView
from ....baseModel import db
from ..case.models import Case
from ..step.models import Step
from ..report.models import Report
from ..sets.models import Set
from .forms import AddCaseForm, EditCaseForm, FindCaseForm, DeleteCaseForm, GetCaseForm, RunCaseForm


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
        quote_case=step['quote_case'],
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


@api.route('/case/name', methods=['get'])
@login_required
def get_case_name():
    """ 根据用例id获取用例名 """
    # caseId: '1,4,12'
    case_ids: list = request.args.to_dict().get('caseId').split(',')
    return restful.success(data=[{'id': int(case_id), 'name': Case.get_first(id=case_id).name} for case_id in case_ids])


@api.route('/case/quote', methods=['put'])
@login_required
def change_case_quote():
    """ 更新用例引用 """
    case_id, quote_type, quote = request.json.get('id'), request.json.get('quoteType'), request.json.get('quote')
    with db.auto_commit():
        case = Case.get_first(id=case_id)
        setattr(case, quote_type, json.dumps(quote))
    return restful.success(msg='引用关系修改成功')


@api.route('/case/sort', methods=['put'])
@login_required
def change_case_sort():
    """ 更新用例的排序 """
    Case.change_sort(request.json.get('List'), request.json.get('pageNum'), request.json.get('pageSize'))
    return restful.success(msg='修改排序成功')


@api.route('/case/run', methods=['POST'])
@login_required
def run_case():
    """ 运行测试用例，并生成报告 """
    form = RunCaseForm()
    if form.validate():
        case = form.case
        project_id = Set.get_first(id=case.set_id).project_id
        report = Report.get_new_report(case.name, 'case', current_user.name, current_user.id, project_id)

        # 新起线程运行用例
        Thread(
            target=RunCase(
                project_id=project_id,
                run_name=report.name,
                case_id=form.caseId.data,
                report_id=report.id
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
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
        new_case.name = old_case.name + '_copy'
        new_case.num = Case.get_insert_num(set_id=old_case.set_id)
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
            form.num.data = Case.get_insert_num(set_id=form.set_id.data)
            new_case = Case().create(form.data, 'func_files', 'variables', 'headers')
            return restful.success('用例新建成功', data=new_case.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditCaseForm()
        if form.validate():
            form.old_data.update(form.data, 'func_files', 'variables', 'headers')
            return restful.success(msg='修改成功', data=form.old_data.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteCaseForm()
        if form.validate():
            case_name, case, steps = form.case.name, form.case, Step.get_all(case_id=form.id.data)

            # 数据有依赖关系，先删除步骤，再删除用例
            with db.auto_commit():
                if steps:
                    for step in steps:
                        db.session.delete(step)
            db.session.delete(case)
            return restful.success(f'用例【{case_name}】删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/case', view_func=CaseView.as_view('case'))
