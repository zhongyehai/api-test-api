#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2022/2/11 17:31
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
from ....utils import restful
from ....utils.required import login_required
from ... import api
from .models import ErrorRecord
from .forms import FindErrorForm


@api.route('/errorRecord/list', methods=['GET'])
@login_required
def error_record_list():
    """ 错误列表 """
    form = FindErrorForm()
    if form.validate():
        return restful.success(data=ErrorRecord.make_pagination(form))
    return restful.fail(form.get_error())

# class ProjectView(BaseMethodView):
#     """ 服务管理 """
#
#     def get(self):
#         """ 获取服务 """
#         form = GetProjectByIdForm()
#         if form.validate():
#             return restful.success(data=form.project.to_dict())
#         return restful.fail(form.get_error())
#
#     def post(self):
#         """ 新增服务 """
#         form = AddProjectForm()
#         if form.validate():
#             project = Project().create(form.data, 'hosts', 'variables', 'headers', 'func_files')
#             return restful.success(f'服务【{form.name.data}】新建成功', project.to_dict())
#         return restful.fail(msg=form.get_error())
#
#     def put(self):
#         """ 修改服务 """
#         form = EditProjectForm()
#         if form.validate():
#             form.project.update(form.data, 'hosts', 'variables', 'headers', 'func_files')
#             return restful.success(f'服务【{form.name.data}】修改成功', form.project.to_dict())
#         return restful.fail(msg=form.get_error())
#
#     def delete(self):
#         """ 删除服务 """
#         form = DeleteProjectForm()
#         if form.validate():
#             form.pro_data.delete()
#             return restful.success(msg=f'服务【{form.pro_data.name}】删除成功')
#         return restful.fail(form.get_error())
#
#
# api.add_url_rule('/project', view_func=ProjectView.as_view('project'))
