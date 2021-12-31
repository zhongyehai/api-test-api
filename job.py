#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/17 15:13
# @Author : ZhongYeHai
# @Site : 
# @File : job.py
# @Software: PyCharm
import os
import json
from threading import Thread

from flask import request
from flask.views import MethodView
from flask_apscheduler import APScheduler

from app.utils import restful
from app.utils.sendReport import async_send_report
from app.utils.parseCron import parse_cron
from app.api.api_test.sets.models import Set, db
from app.api.api_test.task.models import Task
from app.api.user.models import User
from app import create_app
from app.utils.runHttpRunner import RunCase

os.environ['TZ'] = 'Asia/Shanghai'

job = create_app()

# 注册并启动定时任务
scheduler = APScheduler()
scheduler.init_app(job)
scheduler.start()


def aps_test(case_ids, task, user_id=None):
    """ 运行定时任务, 并发送测试报告 """
    user = User.get_first(id=user_id)
    runner = RunCase(
        project_id=task.project_id,
        run_name=task.name,
        case_id=case_ids,
        task=task,
        performer=user.name,
        create_user=user.id)
    jump_res = runner.run_case()

    # 多线程发送测试报告
    async_send_report(content=task.loads(jump_res), **task.to_dict(), report_id=runner.new_report_id)

    db.session.rollback()  # 把连接放回连接池
    return runner.new_report_id


def async_aps_test(*args):
    """ 多线程执行定时任务 """
    Thread(target=aps_test, args=args).start()


class JobStatus(MethodView):
    """ 任务状态修改 """

    def post(self):
        """ 添加定时任务 """
        user_id, task_id = request.json.get('userId'), request.json.get('taskId')
        task = Task.get_first(id=task_id)
        cases_id = Set.get_case_id(task.project_id, json.loads(task.set_id), json.loads(task.case_id))
        try:
            # 把定时任务添加到apscheduler_jobs表中
            scheduler.add_job(func=async_aps_test,  # 异步执行任务
                              trigger='cron',
                              misfire_grace_time=60,
                              coalesce=False,
                              args=[cases_id, task, user_id],
                              id=str(task.id),
                              **parse_cron(task.cron))
            task.status = '启用中'
            db.session.commit()
            return restful.success(f'定时任务 {task.name} 启动成功')
        except Exception as error:
            return restful.error(f'定时任务启动失败', data=error)

    def delete(self):
        """ 删除定时任务 """
        task = Task.get_first(id=request.json.get('taskId'))
        with db.auto_commit():
            task.status = '禁用中'
            scheduler.remove_job(str(task.id))  # 移除任务
        return restful.success(f'任务 {task.name} 禁用成功')


job.add_url_rule('/api/job/status', view_func=JobStatus.as_view('jobStatus'))

if __name__ == '__main__':
    job.run(host='0.0.0.0', port=8025)
