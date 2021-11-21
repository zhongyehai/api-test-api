#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

from threading import Thread

import requests
from flask_login import current_user

from ..report.models import Report
from ..sets.models import Set
from ...utils import restful
from ...utils.required import login_required
from ...utils.runHttpRunner import RunCase
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from .models import Task
from .forms import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, GetTaskListForm


@api.route('/task/run', methods=['POST'])
@login_required
def run_task():
    """ 单次运行定时任务 """
    form = RunTaskForm()
    if form.validate():
        task = form.task
        project_id = task.project_id
        report = Report.get_new_report(task.name, 'task', current_user.name, current_user.id, project_id)

        # 新起线程运行任务
        Thread(
            target=RunCase(
                project_id=project_id,
                run_name=report.name,
                case_id=Set.get_case_id(task.project_id, form.loads(task.set_id), form.loads(task.case_id)),
                report_id=report.id
            ).run_case
        ).start()
        return restful.success(msg='触发执行成功，请等待执行完毕', data={'report_id': report.id})
    return restful.fail(form.get_error())


@api.route('/task/list', methods=['GET'])
@login_required
def task_list():
    """ 任务列表 """
    form = GetTaskListForm()
    if form.validate():
        return restful.success(data=Task.make_pagination(form))
    return restful.fail(form.get_error())


class TaskView(BaseMethodView):
    """ 任务管理 """

    def get(self):
        form = HasTaskIdForm()
        if form.validate():
            return restful.success(data=form.task.to_dict())
        return restful.fail(form.get_error())

    def post(self):
        form = AddTaskForm()
        form.create_user.data = current_user.id
        if form.validate():
            with db.auto_commit():
                new_task = Task()
                form.set_attr(num=form.new_num())
                new_task.create(form.data, 'set_id', 'case_id')
                db.session.add(new_task)
            return restful.success(f'定时任务 {form.name.data} 新建成功', new_task.to_dict())
        return restful.fail(form.get_error())

    def put(self):
        form = EditTaskForm()
        if form.validate():
            form.set_attr(num=form.new_num())
            form.task.update(form.data, 'set_id', 'case_id')
            return restful.success(f'定时任务 {form.name.data} 修改成功', form.task.to_dict())
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteTaskIdForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.task)
            return restful.success(f'任务 {form.task.name} 删除成功')
        return restful.fail(form.get_error())


class TaskStatus(BaseMethodView):
    """ 任务状态修改 """

    def post(self):
        """ 启用任务 """
        form = HasTaskIdForm()
        if form.validate():
            task = form.task
            try:
                res = requests.post(
                    url='http://localhost:8025/api/job/status',
                    json={'userId': current_user.id, 'taskId': task.id}
                ).json()
                if res["status"] == 200:
                    return restful.success(f'定时任务 {form.task.name} 启用成功', data=res)
                else:
                    return restful.fail(f'定时任务 {form.task.name} 启用失败', data=res)
            except Exception as error:
                return restful.fail(f'定时任务 {form.task.name} 启用失败', data=error)
        return restful.fail(form.get_error())

    def delete(self):
        """ 禁用任务 """
        form = HasTaskIdForm()
        if form.validate():
            if form.task.status != '启用中':
                return restful.fail(f'任务 {form.task.name} 的状态不为启用中')
            try:
                res = requests.delete(
                    url='http://localhost:8025/api/job/status',
                    json={'taskId': form.task.id}
                ).json()
                if res["status"] == 200:
                    return restful.success(f'定时任务 {form.task.name} 禁用成功', data=res)
                else:
                    return restful.fail(f'定时任务 {form.task.name} 禁用失败', data=res)
            except Exception as error:
                return restful.fail(f'定时任务 {form.task.name} 禁用失败', data=error)
        return restful.fail(form.get_error())


api.add_url_rule('/task', view_func=TaskView.as_view('task'))
api.add_url_rule('/task/status', view_func=TaskStatus.as_view('taskStatus'))
