#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/5/24 14:26
# @Author : ZhongYeHai
# @Site : 
# @File : index.py
# @Software: PyCharm

import os

from .. import api
from ..project.models import Project
from ..module.models import Module
from ..apiMsg.models import ApiMsg
from ..sets.models import Set
from ..case.models import Case
from ..step.models import Step
from ..task.models import Task
from ..report.models import Report
from ...utils import restful
from ...utils.required import login_required
from ...utils.globalVariable import FILE_ADDRESS


@api.route('/count/title', methods=['GET'])
@login_required
def count_title():
    return restful.success('获取成功', data={
        'project': len(Project.get_all()),
        'module': len(Module.get_all()),
        'api': len(ApiMsg.get_all()),
        'file': len(os.listdir(FILE_ADDRESS)),
        'set': len(Set.get_all()),
        'case': len(Case.get_all()),
        # 'step': len(Step.get_all()),
        'task': len(Task.get_all()),
        'report': len(Report.get_all())
    })


@api.route('/count/project', methods=['GET'])
@login_required
def count_project():
    return restful.success(data={
        'title': '项目',
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
    return restful.success(data={
        'title': '接口',
        'options': ['总数'],
        'data': [len(ApiMsg.get_all())],
    })


@api.route('/count/file', methods=['GET'])
@login_required
def count_file():
    return restful.success(data={
        'title': '文件',
        'options': ['总数'],
        'data': [len(os.listdir(FILE_ADDRESS))],
    })


@api.route('/count/set', methods=['GET'])
@login_required
def count_set():
    return restful.success('获取成功', data={
        'title': '用例集',
        'options': ['总数'],
        'data': [len(Set.get_all())],
    })


@api.route('/count/case', methods=['GET'])
@login_required
def count_case():
    return restful.success('获取成功', data={
        'title': '用例',
        'options': ['总数'],
        'data': [len(Case.get_all())],
    })


@api.route('/count/task', methods=['GET'])
@login_required
def count_task():
    return restful.success('获取成功', data={
        'title': '定时任务',
        'options': [
            '总数', '启用中', '禁用中',
            '始终发送报告的任务', '不发送报告的任务', '失败时发送报告的任务',
            '都接收报告', '仅工作群接收报告', '仅邮件接收报告',
        ],
        'data': [
            len(Task.get_all()),
            # 任务状态
            len(Task.get_all(status='启用中')),
            len(Task.get_all(status='禁用中')),
            # 测试报告接收状态
            len(Task.get_all(is_send=2)),
            len(Task.get_all(is_send=1)),
            len(Task.get_all(is_send=3)),
            # 接收形式
            len(Task.get_all(send_type='all')),
            len(Task.get_all(is_send='webhook')),
            len(Task.get_all(is_send='email'))
        ]
    })


@api.route('/count/report', methods=['GET'])
@login_required
def count_report():
    return restful.success('获取成功', data={
        'title': '测试报告',
        'options': ['总数', '已读', '未读', '通过数', '失败数'],
        'data': [
            len(Report.get_all()),
            len(Report.get_all(status='已读')),
            len(Report.get_all(status='待阅')),
            len(Report.get_all(is_passed=1)),
            len(Report.get_all(is_passed=0)),
        ]
    })
