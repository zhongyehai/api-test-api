#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

from flask import request
from flask_login import current_user

from ...utils import restful
from ...utils.required import login_required
from ...utils.changSort import num_sort
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from ..project.models import Project
from .models import Set
from .forms import AddCaseSetForm, EditCaseSetForm, FindCaseSet, GetCaseSetEditForm, DeleteCaseSetForm


@api.route('/caseSet/list', methods=['GET'])
@login_required
def set_list():
    """ 用例集list """
    form = FindCaseSet()
    if form.validate():
        return restful.success(data=Set.make_pagination(form))
    return restful.fail(form.get_error())


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
            return restful.success(data={'name': form.edit.name, 'num': form.edit.num})
        return restful.fail(form.get_error())

    def post(self):
        form = AddCaseSetForm()
        form.create_user.data = current_user.id
        if form.validate():
            with db.auto_commit():
                new_set, form.num.data = Set(), form.new_num()
                new_set.create(form.data)
                db.session.add(new_set)
            return restful.success(f'名为 {form.name.data} 的用例集新建成功', new_set.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditCaseSetForm()
        if form.validate():
            with db.auto_commit():
                case_set_list_of_project = Set.get_all(project_id=form.project_id.data)
                old_case_set = form.case_set
                num_sort(form.new_num(), old_case_set.num, case_set_list_of_project, old_case_set)
                old_case_set.name, old_case_set.project_id = form.name.data, form.project_id.data
            return restful.success(f'修改 {form.name.data} 成功', old_case_set.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteCaseSetForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.caseSet)
            return restful.success('删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/caseSet', view_func=CaseSetView.as_view('caseSet'))
