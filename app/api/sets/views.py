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
from ...utils import restful
from ...utils.required import login_required
from ...utils.changSort import num_sort
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from ..project.models import Project
from .models import Set
from .forms import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, DeleteCaseSetForm, GetCaseSetForm
from ...utils.runHttpRunner import RunCase


@api.route('/caseSet/list', methods=['GET'])
@login_required
def get_set_list():
    """ 用例集list """
    form = FindCaseSet()
    if form.validate():
        return restful.success(data=Set.make_pagination(form))
    return restful.fail(form.get_error())


@api.route('/caseSet/run', methods=['POST'])
@login_required
def run_case_set():
    """ 运行用例集下的用例 """
    form = GetCaseSetForm()
    if form.validate():
        project_id = form.set.project_id
        with db.auto_commit():
            report = Report()
            report.name = form.set.name
            report.run_type = 'set'
            report.performer = current_user.name
            report.create_user = current_user.id
            report.project_id = project_id
            db.session.add(report)

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


@api.route('/caseSet/tree', methods=['GET'])
@login_required
def case_set_tree():
    """ 获取当前项目下的用例集树 """
    set_list = [
        case_set.to_dict() for case_set in Set.query.filter_by(
            project_id=int(request.args.get('project_id'))).order_by(Set.parent.asc()).all()
    ]
    return restful.success(data=set_list)


@api.route('/caseSet/stick', methods=['PUT'])
@login_required
def stick_set():
    """ 置顶用例集合 """
    old_data = Set.get_first(id=request.json.get('id'))
    list_data = Project.get_first(id=request.json.get('projectId')).case_sets.all()
    with db.auto_commit():
        num_sort(1, old_data.num, list_data, old_data)
    return restful.success('置顶完成')


class CaseSetView(BaseMethodView):
    """ 用例集管理 """

    def get(self):
        form = GetCaseSetEditForm()
        if form.validate():
            return restful.success(data={'name': form.set.name, 'num': form.set.num})
        return restful.fail(form.get_error())

    def post(self):
        form = AddCaseSetForm()
        form.create_user.data = current_user.id
        if form.validate():
            with db.auto_commit():
                new_set, form.num.data = Set(), form.new_num()
                new_set.create(form.data)
                db.session.add(new_set)
            return restful.success(f'名为 {form.name.data} 的用例集创建成功', new_set.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditCaseSetForm()
        if form.validate():
            old, set_list, new_num = form.case_set, Set.get_all(project_id=form.project.id), form.new_num()
            num_sort(new_num, old.num, set_list, old)
            with db.auto_commit():
                old.update(form.data)
            return restful.success(f'用例集 {form.name.data} 修改成功', old.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteCaseSetForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.case_set)
            return restful.success('删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/caseSet', view_func=CaseSetView.as_view('caseSet'))
