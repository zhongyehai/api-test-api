#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

import json
from threading import Thread

from flask_login import current_user

from ...utils import restful
from ...utils.required import login_required
from ...utils.sendReport import async_send_report
from ...utils.runHttpRunner import RunCase
from ...utils.parseCron import parse_cron
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from ..case.models import Case
from ..sets.models import Set
from ..user.models import User
from ... import scheduler
from .models import Task
from .forms import RunTaskForm, AddTaskForm, EditTaskForm, HasTaskIdForm, DeleteTaskIdForm, GetTaskListForm


def aps_test(case_ids, task, performer=None):
    """ 运行定时任务, 并发送测试报告 """
    runner = RunCase(project_id=task.project_id,  task_name=task.name, case_id_list=case_ids)
    jump_res = runner.run_case()
    runner.build_report(jump_res, performer, task.name, 'task')
    res = json.loads(jump_res)

    # 多线程发送测试报告
    async_send_report(content=res, **task.to_dict())

    db.session.rollback()  # 把连接放回连接池，不知道为什么定时任务跑完不会自动放回去，导致下次跑的时候，mysql连接超时断开报错
    return runner.new_report_id


def async_aps_test(*args):
    """ 多线程执行定时任务 """
    Thread(target=aps_test, args=args).start()


def get_case_id(project_id, set_id_list, case_id_list):
    """
    获取要执行的用例的id
    1.如果有用例id，则只拿对应的用例
    2.如果没有用例id，有用例集id，则拿用例集下的所有id
    3.如果没有用例id，也没有用例集id，则拿项目下所有用例集下的所有用例
    """
    if len(case_id_list) != 0:
        return case_id_list
    elif len(set_id_list) != 0:
        set_ids = set_id_list
    else:  # 获取项目下的所有用例集
        set_ids = [caseSet.id for caseSet in Set.query.filter_by(project_id=project_id).order_by(Set.num.asc()).all()]
    # 获取用例集列表下的所有用例
    case_ids = [case_data.id for set_id in set_ids for case_data in Case.query.filter_by(
        case_set_id=set_id).order_by(Case.num.asc()).all()]
    return case_ids


@api.route('/task/run', methods=['POST'])
@login_required
def run_task():
    """ 单次运行定时任务 """
    form = RunTaskForm()
    if form.validate():
        task = form.task
        cases_id = get_case_id(task.project_id, json.loads(task.set_id), json.loads(task.case_id))
        new_report_id = aps_test(cases_id, task, performer=User.get_first(id=current_user.id))
        return restful.success(msg='测试成功', data={'report_id': new_report_id})
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
        form = HasTaskIdForm()
        if form.validate():
            task = form.task
            cases_id = get_case_id(task.project_id, json.loads(task.set_id), json.loads(task.case_id))
            # 把定时任务添加到apscheduler_jobs表中
            scheduler.add_job(func=async_aps_test,  # 异步执行任务
                              trigger='cron',
                              misfire_grace_time=60,
                              coalesce=False,
                              args=[cases_id, task, User.get_first(id=current_user.id)],
                              id=str(form.id.data),
                              **parse_cron(task.cron))
            task.status = '启用中'
            db.session.commit()
            return restful.success(f'定时任务 {task.name} 启动成功')
        return restful.fail(form.get_error())

    def delete(self):
        form = HasTaskIdForm()
        if form.validate():
            if form.task.status != '启用中':
                return restful.fail(f'任务 {form.task.name} 的状态不为启用中')
            with db.auto_commit():
                form.task.status = '禁用中'
                scheduler.remove_job(str(form.task.id))  # 移除任务
            return restful.success(f'任务 {form.task.name} 禁用成功')
        return restful.fail(form.get_error())


api.add_url_rule('/task', view_func=TaskView.as_view('task'))
api.add_url_rule('/task/status', view_func=TaskStatus.as_view('taskStatus'))
