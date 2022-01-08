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
from ..utils.log import logger
from app.baseModel import db
from ..api.api_test.apiMsg.models import ApiMsg
from ..api.api_test.case.models import Case
from ..api.api_test.step.models import Step
from app.api.api_test.func.models import Func
from ..api.api_test.project.models import Project
from ..api.api_test.report.models import Report

from app.utils.globalVariable import REPORT_ADDRESS, FUNC_ADDRESS
from app.utils.parse import encode_object
from .parseModel import ProjectFormatModel, ApiFormatModel, CaseFormatModel, StepFormatModel


class BaseParse:

    def __init__(self, project_id=None, name=None, report_id=None, performer=None, create_user=None):

        self.environment = None
        self.project_id = project_id
        self.run_name = name

        if not report_id:
            self.report = Report.get_new_report(self.run_name, 'task', performer, create_user, project_id)

        self.report_id = report_id or self.report.id
        self.parsed_project_dict = {}
        self.parsed_case_dict = {}
        self.parsed_api_dict = {}

        Func.create_func_file(FUNC_ADDRESS)  # 创建所有函数文件
        self.func_file_list = Func.get_all()

        self.new_report_id = None

        # httpRunner需要的数据格式
        self.DataTemplate = {
            'project': self.run_name or self.get_formated_project(self.project_id).name,
            'project_mapping': {
                'functions': {},
                'variables': {}
            },
            'testcases': []
        }

    def get_formated_project(self, project_id):
        """ 从已解析的服务字典中取指定id的服务，如果没有，则取出来解析后放进去 """
        if project_id not in self.parsed_project_dict:
            project = Project.get_first(id=project_id)
            self.parse_functions(json.loads(project.func_files))
            self.parsed_project_dict.update({project_id: ProjectFormatModel(**project.to_dict())})
        return self.parsed_project_dict[project_id]

    def get_formated_case(self, case_id):
        """ 从已解析的用例字典中取指定id的用例，如果没有，则取出来解析后放进去 """
        if case_id not in self.parsed_case_dict:
            case = Case.get_first(id=case_id)
            self.parse_functions(json.loads(case.func_files))
            self.parsed_case_dict.update({case_id: CaseFormatModel(**case.to_dict())})
        return self.parsed_case_dict[case_id]

    def get_formated_api(self, project, api):
        """ 从已解析的接口字典中取指定id的接口，如果没有，则取出来解析后放进去 """
        if api.id not in self.parsed_api_dict:
            if api.project_id not in self.parsed_project_dict:
                self.parse_functions(json.loads(Project.get_first(id=api.project_id).func_files))
            self.parsed_api_dict.update({
                api.id: self.parse_api(project, ApiFormatModel(**api.to_dict()))
            })
        return self.parsed_api_dict[api.id]

    def parse_functions(self, func_list):
        """ 获取自定义函数 """
        for func_file_name in func_list:
            func_file_data = importlib.reload(importlib.import_module('func_list.{}'.format(func_file_name)))
            self.DataTemplate['project_mapping']['functions'].update({
                name: item for name, item in vars(func_file_data).items() if isinstance(item, types.FunctionType)
            })

    def parse_api(self, project, api):
        """ 把解析后的接口对象 解析为httpRunner的数据结构 """
        return {
            'name': api.name,  # 接口名
            'setup_hooks': [up.strip() for up in api.up_func.split(';') if up] if api.up_func else [],
            'teardown_hooks': [func.strip() for func in api.down_func.split(';') if func] if api.down_func else [],
            'skip': '',  # 无条件跳过当前测试
            'skipIf': '',  # 如果条件为真，则跳过当前测试
            'skipUnless': '',  # 除非条件为真，否则跳过当前测试
            'times': 1,  # 运行次数
            'extract': api.extracts,  # 接口要提取的信息
            'validate': api.validates,  # 接口断言信息
            'base_url': getattr(project, self.environment),
            'data_type': api.data_type,
            'request': {
                'method': api.method,
                'url': api.addr,
                'headers': api.headers,  # 接口头部信息
                'params': api.params,  # 接口查询字符串参数
                'json': api.data_json,
                'data': api.data_form['string'] if api.data_type.upper() == 'DATA' else api.data_xml,
                'files': api.data_form['files'] if api.data_form else {},
            }
        }

    def build_report(self, json_result):
        """ 写入测试报告到数据库, 并把数据写入到文本中 """
        result = json.loads(json_result)
        report = Report.get_first(id=self.report_id)
        with db.auto_commit():
            report.is_passed = 1 if result['success'] else 0
            report.is_done = 1

        # 测试报告写入到文本文件
        with open(os.path.join(REPORT_ADDRESS, f'{report.id}.txt'), 'w') as f:
            f.write(json_result)

    def run_case(self):
        """ 调 HttpRunner().run() 执行测试 """
        logger.info(f'请求数据：\n{self.DataTemplate}')
        runner = HttpRunner()
        runner.run(self.DataTemplate)
        summary = runner.summary
        summary['time']['start_at'] = datetime.fromtimestamp(summary['time']['start_at']).strftime("%Y-%m-%d %H:%M:%S")
        jump_res = json.dumps(summary, ensure_ascii=False, default=encode_object, cls=JSONEncoder)
        self.build_report(jump_res)
        return jump_res


class RunApi(BaseParse):
    """ 接口调试 """

    def __init__(self, project_id=None, run_name=None, api_ids=None, report_id=None):
        super().__init__(project_id, run_name, report_id)

        # 解析当前服务信息
        self.project = self.get_formated_project(self.project_id)

        # 要执行的接口id列表
        self.api_ids = api_ids

        # 解析api
        self.format_data_for_template()

    def format_data_for_template(self):
        """ 接口调试 """
        logger.info(f'本次测试的接口id：\n{self.api_ids}')

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

    def __init__(self, project_id=None, run_name=None, case_id=[], task={}, report_id=None, performer=None,
                 create_user=None):
        super().__init__(project_id, run_name, report_id, performer=performer, create_user=create_user)
        self.task = task
        self.environment = task.get('choice_host') if isinstance(task, dict) else task.choice_host
        # 接口对应的服务字典，在需要解析服务时，先到这里面查，没有则去数据库取出来解析
        self.projects_dict = {}

        # 步骤对应的接口字典，在需要解析字典时，先到这里面查，没有则去数据库取出来解析
        self.apis_dict = {}

        # 要执行的用例id_list
        self.case_id_list = case_id

        # 前置用例
        self.before_case = []
        self.before_case_headers = {}
        self.before_case_variables = {}

        # 后置用例
        self.after_case = []
        self.after_case_headers = {}
        self.after_case_variables = {}

        self.parse_all_case()

    def parse_quote(self, quote_case: list, position: str):
        """ 解析引用的用例 """
        quote_case.reverse()
        for quote in quote_case:
            case = self.get_formated_case(quote)

            if case:
                temp_case_list = getattr(self, f'{position}_case')
                # 记录引用的用例
                temp_case_list.append(case)

                # 更新引用的用例对应的头部信息
                # case.headers.update(getattr(self, f'{position}_case_headers'))
                setattr(self, f'{position}_case_headers', case.headers)

                # 更新引用的用例对应的公共变量
                case.variables.update(getattr(self, f'{position}_case_variables'))
                setattr(self, f'{position}_case_variables', case.variables)

                if getattr(case, f'{position}_case'):
                    self.parse_quote(getattr(case, f'{position}_case'), position)

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
            'setup_hooks': [up.strip() for up in step.up_func.split(';') if up] if step.up_func else [],
            'teardown_hooks': [func.strip() for func in step.down_func.split(';') if func] if step.down_func else [],
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
                'data': step.data_form.get('string', {}) if api['data_type'] == 'DATA' else step.data_xml,
                'files': step.data_form.get('files', {}),
            }
        }

    def parse_all_case(self):
        """ 解析所有用例 """

        # 遍历要运行的用例
        for case_id in self.case_id_list:

            # 递归解析前置引用
            self.parse_quote([case_id], 'before')
            self.before_case.reverse()
            logger.info(f'前置引用用例：{[case.id for case in self.before_case]}')

            # 递归解析后置引用
            self.parse_quote([case_id], 'after')
            logger.info(f'后置引用用例：{[case.id for case in self.after_case]}')

            # 当前用例含引用用例的执行顺序
            current_case = self.after_case.pop(0)  # 前置的最后一个id为当前用例的id，后置的第一个id为当前用例id，去重复
            case_list = self.before_case + self.after_case
            logger.info(f'当前用例含引用用例的排列情况: {[case.id for case in case_list]}')

            # 选择运行环境
            if not self.task:
                self.environment = current_case.choice_host

            # 用例格式模板
            case_template = {
                'config': {
                    'variables': {},
                    'headers': {},
                    'name': current_case.name
                },
                'teststeps': []
            }

            # 当前用例的所有公共变量
            all_variables = {}
            all_variables.update(self.before_case_variables)
            all_variables.update(self.after_case_variables)

            # 根据执行顺序逐个解析用例
            extract_key_list = []  # 步骤中提取的key
            for case in case_list:

                # 遍历解析用例对应的步骤list, 根据num排序
                steps = Step.query.filter_by(case_id=case.id, is_run=True).order_by(Step.num.asc()).all()
                for step in steps:
                    step = StepFormatModel(**step.to_dict(), extract_list=extract_key_list)
                    project = self.get_formated_project(step.project_id)
                    api = self.get_formated_api(project, ApiMsg.get_first(id=step.api_id))

                    # 如果有step.data_driver，则说明是数据驱动
                    if step.data_driver:
                        method = api.get('request', {}).get('method', {})
                        for data in step.data_driver:
                            # 数据驱动的 comment 字段，用于做标识
                            if '_comment' in data:
                                comment = data.pop('_comment')
                                step.name += f'_{comment}'
                            if method == 'GET':
                                step.params = data
                            else:
                                step.data_json = step.data_form = data
                            case_template['teststeps'].append(self.parse_step(project, case, api, step))
                    else:
                        case_template['teststeps'].append(self.parse_step(project, case, api, step))

                    # 把服务的自定义变量留下来
                    all_variables.update(project.variables)

                # 在最后生成的请求数据中，在用例级别使用合并后的公共变量
                all_variables.update(case.variables)

            # 如果要提取的变量key在公共变量中已存在，则从公共变量中去除
            for extract_key in extract_key_list:
                if extract_key in all_variables:
                    del all_variables[extract_key]

            case_template['config']['variables'].update(all_variables)  # = all_variables

            # 设置的用例执行多少次就加入多少次
            for i in range(current_case.run_times or 1):
                self.DataTemplate['testcases'].append(case_template)

            # 完整的解析完一条用例后，去除对应的引用信息
            self.before_case = []
            self.before_case_headers = {}
            self.before_case_variables = {}
            self.after_case = []
            self.after_case_headers = {}
            self.after_case_variables = {}

        # 去除服务级的公共变量，保证用步骤上解析后的公共变量
        self.DataTemplate['project_mapping']['variables'] = {}
