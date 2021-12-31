#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/5/24 14:26
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
import os

from .. import api
from ..api_test.step.models import Step
from ...baseModel import db
from ..api_test.project.models import Project
from ..api_test.module.models import Module
from ..api_test.apiMsg.models import ApiMsg
from ..api_test.case.models import Case
from ..api_test.task.models import Task
from ..api_test.report.models import Report
from ...utils import restful
from ...utils.required import login_required
from ...utils.globalVariable import CASE_FILE_ADDRESS


@api.route('/count/title', methods=['GET'])
@login_required
def count_title():
    return restful.success('获取成功', data={
        'project': len(Project.get_all()),
        'module': len(Module.get_all()),
        'api': len(ApiMsg.get_all()),
        'file': len(os.listdir(CASE_FILE_ADDRESS)),
        'case': len(Case.get_all()),
        'step': len(Step.get_all()),
        'task': len(Task.get_all()),
        'report': len(Report.get_all())
    })


@api.route('/count/project', methods=['GET'])
@login_required
def count_project():
    return restful.success(data={
        'title': '服务',
        'options': ['总数'],
        'data': [len(Project.get_all())],
    })


@api.route('/count/module', methods=['GET'])
@login_required
def count_module():
    return restful.success(data={
        'title': '模块',
        'options': ['总数'],
        'data': [len(Module.get_all())],
    })


@api.route('/count/api', methods=['GET'])
@login_required
def count_api():
    data = db.execute_query_sql("""
        select methods, count(*) as totle
            from (select case
                     when method = 'GET' then 'GET'
                     when method = 'POST' then 'POST'
                     when method = 'PUT' then 'PUT'
                     when method = 'DELETE' then 'DELETE'
                     else 'Other' end as methods
                  from `apis`
                 ) as t
            group by methods
        """)
    return restful.success(data={
        'title': '接口',
        'options': ['总数', 'GET请求', 'POST请求', 'PUT请求', 'DELETE请求'],
        'data': [sum(data.values()), data.get('GET', 0), data.get('POST', 0), data.get('PUT', 0), data.get('DELETE', 0)]
    })


@api.route('/count/file', methods=['GET'])
@login_required
def count_file():
    return restful.success(data={
        'title': '测试文件',
        'options': ['总数'],
        'data': [len(os.listdir(CASE_FILE_ADDRESS))],
    })


@api.route('/count/case', methods=['GET'])
@login_required
def count_case():
    data = db.execute_query_sql("""
        select is_run, count(*) as totle
            from (select IF(is_run = 0, 'not_run', 'is_run') as is_run from `case`) as t
            group by is_run;
        """)
    return restful.success('获取成功', data={
        'title': '用例',
        'options': ['总数', '要执行的用例', '不执行的用例'],
        'data': [sum(data.values()), data.get('is_run', 0), data.get('not_run', 0)],
    })


@api.route('/count/step', methods=['GET'])
@login_required
def count_step():
    data = db.execute_query_sql("""
        select is_run, count(*) as totle
            from (select IF(is_run = 0, 'not_run', 'is_run') as is_run from `step`) as t
            group by is_run;
        """)
    return restful.success('获取成功', data={
        'title': '测试步骤',
        'options': ['总数', '要执行的步骤', '不执行的步骤'],
        'data': [sum(data.values()), data.get('is_run', 0), data.get('not_run', 0)],
    })


@api.route('/count/task', methods=['GET'])
@login_required
def count_task():
    status = db.execute_query_sql("""
        select status, count(*) as totle
            from (select IF(status = '启用中', 'enable', 'disable') as status from `tasks` ) as t
            group by status
        """)

    is_send = db.execute_query_sql("""
        select is_send, count(*) as totle
            from (select case
                     when is_send = 1 then 'is_send1'
                     when is_send = 2 then 'is_send2'
                     else 'is_send3' end as is_send
                  from `tasks`
                 ) as t
            group by is_send
        """)

    send_type = db.execute_query_sql("""
        select send_type, count(*) as totle
            from (select case
                     when send_type = 'all' then 'all'
                     when send_type = 'we_chat' then 'we_chat'
                     when send_type = 'ding_ding' then 'ding_ding'
                     else 'email' end as send_type
                  from `tasks`
                 ) as t
            group by send_type
        """)
    return restful.success('获取成功', data={
        'title': '定时任务',
        'options': [
            '总数', '启用中', '禁用中',
            '始终发送报告的任务', '不发送报告的任务', '失败时发送报告的任务',
            '都接收报告', '仅企业微信群接收报告', '仅钉钉群接收报告', '仅邮件接收报告',
        ],
        'data': [
            sum(status.values()),
            status.get('enable', 0), status.get('disable', 0),
            is_send.get('is_send2', 0), is_send.get('is_send1', 0), is_send.get('is_send3', 0),
            send_type.get('all', 0), send_type.get('we_chat', 0), send_type.get('ding_ding', 0),
            send_type.get('email', 0)
        ]
    })


@api.route('/count/report', methods=['GET'])
@login_required
def count_report():
    status = db.execute_query_sql("""
        select status, count(*) as totle
            from (select IF(status = '已读', 'is_read', 'not_read') as status from `report` ) as t
            group by status
        """)

    is_passed = db.execute_query_sql("""
        select is_passed, count(*) as totle
            from (select IF(is_passed = 1, 'is_passed', 'not_passed') as is_passed from `report`) as t
            group by is_passed
        """)

    run_type = db.execute_query_sql("""
        select run_type, count(*) as totle
            from (select case 
                     when run_type = 'api' then 'api'
                     when run_type = 'set' then 'set'
                     when run_type = 'case' then 'case'
                     when run_type = 'task' then 'task' end as run_type from `report`) as t
            group by run_type
        """)

    return restful.success('获取成功', data={
        'title': '测试报告',
        'options': [
            '总数', '已读', '未读', '通过数', '失败数',
            '接口生成的报告', '用例生成的报告', '用例集生成的报告', '定时任务生成的报告'
        ],
        'data': [
            sum(status.values()),
            status.get('is_read', 0), status.get('not_read', 0),
            is_passed.get('is_passed', 0), is_passed.get('not_passed', 0),
            run_type.get('api', 0), run_type.get('case', 0), run_type.get('set', 0), run_type.get('task', 0)
        ]
    })
