#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
from threading import Thread

from flask import request
from flask_login import current_user

from ..case.models import Case
from ..report.models import Report
from app.utils import restful
from app.utils.required import login_required
from app.utils.runHttpRunner import RunCase
from app.api_test import api_test
from app.baseView import BaseMethodView
from .models import Set
from .forms import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, DeleteCaseSetForm, GetCaseSetForm


@api_test.route('/caseSet/list', methods=['GET'])
@login_required
def get_set_list():
    """ 用例集list """
    form = FindCaseSet()
    if form.validate():
        return restful.success(data=Set.make_pagination(form))
    return restful.fail(form.get_error())


@api_test.route('/caseSet/run', methods=['POST'])
@login_required
def run_case_set():
    """ 运行用例集下的用例 """
    form = GetCaseSetForm()
    if form.validate():
        project_id = form.set.project_id
        report = Report.get_new_report(form.set.name, 'set', current_user.name, current_user.id, project_id)

        # 新起线程运行任务
        Thread(
            target=RunCase(
                project_id=project_id,
                run_name=report.name,
                case_id=[case.id for case in Case.query.filter_by(set_id=form.set.id).order_by(Case.num.asc()).all()
                         if case.is_run],
                report_id=report.id
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return restful.fail(form.get_error())


@api_test.route('/caseSet/tree', methods=['GET'])
@login_required
def case_set_tree():
    """ 获取当前服务下的用例集树 """
    set_list = [
        case_set.to_dict() for case_set in Set.query.filter_by(
            project_id=int(request.args.get('project_id'))).order_by(Set.parent.asc()).all()
    ]
    return restful.success(data=set_list)


class CaseSetView(BaseMethodView):
    """ 用例集管理 """

    def get(self):
        form = GetCaseSetEditForm()
        if form.validate():
            return restful.success(data={'name': form.set.name, 'num': form.set.num})
        return restful.fail(form.get_error())

    def post(self):
        form = AddCaseSetForm()
        if form.validate():
            form.num.data = Set.get_insert_num(project_id=form.project_id.data)
            new_set = Set().create(form.data)
            return restful.success(f'名为【{form.name.data}】的用例集创建成功', new_set.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditCaseSetForm()
        if form.validate():
            form.case_set.update(form.data)
            return restful.success(f'用例集【{form.name.data}】修改成功', form.case_set.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteCaseSetForm()
        if form.validate():
            form.case_set.delete()
            return restful.success('删除成功')
        return restful.fail(form.get_error())


api_test.add_url_rule('/caseSet', view_func=CaseSetView.as_view('caseSet'))
