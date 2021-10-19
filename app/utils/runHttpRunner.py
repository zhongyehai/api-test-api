""" 把数据取出来解析，并组装成httpRunner需要的数据格式 """

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : httpRun.py
# @Software: PyCharm

import json
import os
import types
import importlib
from datetime import datetime

from flask.json import JSONEncoder
from .httprunner.api import HttpRunner

from app.baseModel import db
from ..api.apiMsg.models import ApiMsg
from ..api.case.models import Case
from ..api.step.models import Step
from ..api.func.models import Func
from ..api.project.models import Project
from ..api.report.models import Report

from app.utils.globalVariable import REPORT_ADDRESS, FUNC_ADDRESS
from app.utils.parse import encode_object
from app import scheduler  # 定时任务实例
from .parseModel import ProjectFormatModel, ApiFormatModel, CaseFormatModel, StepFormatModel


class BaseParse:

    def __init__(self, project_id=None, task_name=None):

        self.environment = None
        self.project_id = project_id
        self.task_name = task_name
        self.parsed_project_dict = {}

        Func.create_func_file(FUNC_ADDRESS)

        self.func_file_list = Func.get_all()

        self.parsed_api_dict = {}
        self.new_report_id = None

        # httpRunner需要的数据格式
        self.DataTemplate = {
            'project': self.task_name or self.get_formated_project(self.project_id).name,
            'project_mapping': {
                'functions': self.parse_functions(),
                'variables': {}
            },
            'testcases': []
        }

    def get_formated_project(self, project_id):
        """ 从已解析的项目字典中取指定id的项目，如果没有，则取出来解析后放进去 """
        if project_id not in self.parsed_project_dict:
            self.parsed_project_dict.update({
                project_id: ProjectFormatModel(**Project.get_first(id=project_id).to_dict())
            })
        return self.parsed_project_dict[project_id]

    def get_formated_api(self, project, api):
        """ 从已解析的接口字典中取指定id的接口，如果没有，则取出来解析后放进去 """
        if api.id not in self.parsed_api_dict:
            self.parsed_api_dict.update({
                api.id: self.parse_api(project, ApiFormatModel(**api.to_dict()))
            })
        return self.parsed_api_dict[api.id]

    def parse_functions(self):
        """ 获取自定义函数 """
        func_file_dict = {}
        for func_file in self.func_file_list:
            func_file_data = importlib.reload(importlib.import_module('func_list.{}'.format(func_file.name)))
            func_file_dict.update({
                name: item for name, item in vars(func_file_data).items() if isinstance(item, types.FunctionType)
            })
        return func_file_dict

    def parse_api(self, project, api):
        """ 把解析后的接口对象 解析为httpRunner的数据结构 """
        return {
            'name': api.name,  # 接口名
            'setup_hooks': [api.up_func] if api.up_func else [],  # 前置钩子函数
            'teardown_hooks': [api.down_func] if api.down_func else [],  # 后置钩子函数
            'skip': '',  # 无条件跳过当前测试
            'skipIf': '',  # 如果条件为真，则跳过当前测试
            'skipUnless': '',  # 除非条件为真，否则跳过当前测试
            'times': 1,  # 运行次数
            'extract': api.extracts,  # 接口要提取的信息
            'validate': api.validates,  # 接口断言信息
            'base_url': getattr(project, self.environment),
            'request': {
                'method': api.method,
                'url': api.addr,
                'headers': api.headers,  # 接口头部信息
                'params': api.params,  # 接口查询字符串参数
                'json': api.data_json,
                'data': api.data_form['string'] if api.data_form else {},
                'files': api.data_form['files'] if api.data_form else {},
            }
        }

    def build_report(self, json_result, performer, name, run_type):
        """ 写入测试报告到数据库, 并把数据写入到文本中 """
        result = json.loads(json_result)
        report = Report()
        report.performer = performer.name
        report.create_user = performer.id
        report.project_id = self.project_id
        report.status = '待阅'
        report.is_passed = 1 if result['success'] else 0
        # report.name = ','.join([detail['name'] for detail in result['details']])
        report.name = name
        report.run_type = run_type

        with db.auto_commit():
            db.session.add(report)
        self.new_report_id = report.id

        # 测试报告写入到文本文件
        with open(os.path.join(REPORT_ADDRESS, f'{self.new_report_id}.txt'), 'w') as f:
            f.write(json_result)

    def run_case(self):
        """ 调 HttpRunner().run() 执行测试 """
        scheduler.app.logger.info(f'请求数据：{self.DataTemplate}')
        runner = HttpRunner()
        runner.run(self.DataTemplate)
        summary = runner.summary
        summary['time']['start_at'] = datetime.fromtimestamp(summary['time']['start_at']).strftime("%Y-%m-%d %H:%M:%S")
        return json.dumps(summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)


class RunApi(BaseParse):
    """ 接口调试 """

    def __init__(self, project_id=None, task_name=None, api_ids=None):
        super().__init__(project_id, task_name)

        # 解析当前项目信息
        self.project = self.get_formated_project(self.project_id)

        # 要执行的接口id列表
        self.api_ids = api_ids

        # 解析api
        self.format_data_for_template()

    def format_data_for_template(self):
        """ 接口调试 """
        scheduler.app.logger.info(f'本次测试的接口id：{self.api_ids}')

        # 用例的数据结构
        test_case_template = {
            'config': {
                'variables': {},
            },
            'teststeps': []  # 测试步骤
        }

        # 解析api
        api_obj = ApiMsg.get_first(id=self.api_ids)
        self.environment = api_obj.choice_host
        api = self.get_formated_api(self.project, api_obj)

        # 合并头部信息
        headers = {}
        headers.update(self.project.headers)
        headers.update(api['request']['headers'])
        api['request']['headers'] = headers

        # 把api加入到步骤
        test_case_template['teststeps'].append(api)

        # 更新公共变量
        test_case_template['config']['variables'].update(self.project.variables)
        self.DataTemplate['testcases'].append(test_case_template)


class RunCase(BaseParse):
    """ 运行测试用例 """

    def __init__(self, project_id=None, task_name=None, case_id=[], task=None):
        super().__init__(project_id, task_name)
        self.task = task
        self.environment = task.choice_host if task else None
        # 接口对应的项目字典，在需要解析项目时，先到这里面查，没有则去数据库取出来解析
        self.projects_dict = {}

        # 步骤对应的接口字典，在需要解析字典时，先到这里面查，没有则去数据库取出来解析
        self.apis_dict = {}

        # 任务名
        self.task_name = task_name

        # 要执行的用例id_list
        self.case_id_list = case_id

        self.parse_all_case()

    def parse_step(self, project, case, api, step):
        """ 解析测试步骤
        project: 解析后的project
        case: 解析后的case
        api: 解析后的api
        step: 原始step
        返回解析后的步骤 {}
        """
        # 解析头部信息，继承
        headers = {}
        headers.update(project.headers)
        headers.update(api['request']['headers'])
        headers.update(case.headers)
        headers.update(step.headers)

        return {
            'name': step.name,
            'setup_hooks': [step.up_func] if step.up_func else [],  # 前置钩子函数
            'teardown_hooks': [step.down_func] if step.down_func else [],  # 后置钩子函数
            'skip': '',  # 无条件跳过当前测试
            'skipIf': step.is_run,  # 如果条件为真，则跳过当前测试
            'skipUnless': '',  # 除非条件为真，否则跳过当前测试
            'times': step.run_times,  # 运行次数
            'extract': step.extracts,  # 接口要提取的信息
            'validate': step.validates,  # 接口断言信息
            'base_url': getattr(project, self.environment),
            'request': {
                'method': api['request']['method'],
                'url': api['request']['url'],
                'headers': headers,  # 接口头部信息
                'params': step.params,  # 接口查询字符串参数
                'json': step.data_json,
                'data': step.data_form.get('string', {}),
                'files': step.data_form.get('files', {}),
            }
        }

    def parse_all_case(self):
        """ 解析所有用例 """

        # 遍历用例
        for case_id in self.case_id_list:
            case, extract_key_list = Case.get_first(id=case_id, is_run=True), []  # extract_key_list：步骤中要提取的变量的key
            if case:  # 可能有用例设置为不运行的情况
                if not self.task:
                    self.environment = case.choice_host
                case = CaseFormatModel(**Case.get_first(id=case_id, is_run=True).to_dict())
                # 用例格式模板
                case_template = {
                    'config': {
                        'variables': {},
                        'headers': {},
                        'name': case.name
                    },
                    'teststeps': []
                }

                all_variables = {}

                # 遍历解析用例对应的步骤list, 根据num排序
                steps = Step.query.filter_by(case_id=case_id, is_run=True).order_by(Step.num.asc()).all()
                for step in steps:
                    step = StepFormatModel(**step.to_dict(), extract_list=extract_key_list)
                    project = self.get_formated_project(step.project_id)
                    api = self.get_formated_api(project, ApiMsg.get_first(id=step.api_id))
                    if step.data_driver:  # 如果有step.data_driver，则说明是数据驱动
                        method = api.get('request', {}).get('method', {})
                        for data in step.data_driver:
                            if method == 'GET':
                                step.params = data
                            else:
                                step.data_json = step.data_form = data
                            case_template['teststeps'].append(self.parse_step(project, case, api, step))
                    else:
                        case_template['teststeps'].append(self.parse_step(project, case, api, step))

                    # 把项目的自定义变量留下来
                    all_variables.update(project.variables)

                # 在最后生成的请求数据中，在用例级别使用合并后的公共变量
                all_variables.update(case.variables)
                # 如果要提取的变量key在公共变量中已存在，则从公共变量中去除
                for extract_key in extract_key_list:
                    if extract_key in all_variables:
                        del all_variables[extract_key]

                case_template['config']['variables'] = all_variables

                # 设置的用例执行多少次就加入多少次
                for i in range(case.run_times or 1):
                    self.DataTemplate['testcases'].append(case_template)

        # 去除项目级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate['project_mapping']['variables'] = {}
