#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

from flask import request

from ....utils import restful
from ....utils.required import login_required
from ....utils.changSort import num_sort
from ... import api
from ....baseView import BaseMethodView
from ....baseModel import db
from .models import Module
from .forms import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm


@api.route('/module/list', methods=['GET'])
@login_required
def get_module_list():
    """ 模块列表 """
    form = FindModelForm()
    if form.validate():
        return restful.get_success(data=Module.make_pagination(form))
    return restful.fail(form.get_error())


@api.route('/module/tree', methods=['GET'])
@login_required
def module_tree():
    """ 获取当前项目下的模块树 """
    project_id = int(request.args.get('project_id'))
    module_list = [
        module.to_dict() for module in Module.query.filter_by(
            project_id=project_id).order_by(Module.parent.asc()).all()
    ]
    return restful.success(data=module_list)


class ModuleView(BaseMethodView):
    """ 模块管理 """

    def get(self):
        form = GetModelForm()
        if form.validate():
            return restful.get_success(data=form.module.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddModelForm()
        if form.validate():
            with db.auto_commit():
                new_model, form.num.data = Module(), form.new_num()
                new_model.create(form.data)
                db.session.add(new_model)
            setattr(new_model, 'children', [])
            return restful.success(f'名为 {form.name.data} 的模块创建成功', new_model.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditModelForm()
        if form.validate():
            old, module_list, new_num = form.old_module, Module.get_all(project_id=form.project.id), form.new_num()
            num_sort(new_num, old.num, module_list, old)
            with db.auto_commit():
                old.update(form.data)
            return restful.success(f'模块 {form.name.data} 修改成功', old.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteModelForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.module)
            return restful.success(f'名为 {form.module.name} 的模块删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/module', view_func=ModuleView.as_view('module'))
