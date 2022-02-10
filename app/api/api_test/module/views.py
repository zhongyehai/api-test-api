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
from ... import api
from ....baseView import BaseMethodView
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
    """ 获取当前服务下的模块树 """
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
            form.num.data = Module.get_insert_num(project_id=form.project_id.data)
            new_model = Module().create(form.data)
            setattr(new_model, 'children', [])
            return restful.success(f'名为【{form.name.data}】的模块创建成功', new_model.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditModelForm()
        if form.validate():
            form.old_module.update(form.data)
            return restful.success(f'模块【{form.name.data}】修改成功', form.old_module.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteModelForm()
        if form.validate():
            form.module.delete()
            return restful.success(f'名为【{form.module.name}】的模块删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/module', view_func=ModuleView.as_view('module'))
