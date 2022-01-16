#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/3/17 9:51
# @Author : ZhongYeHai
# @Site :
# @File : parseModel.py
# @Software: PyCharm
import ast
import os

from .globalVariable import CASE_FILE_ADDRESS, CONTENT_TYPE
from .jsonUtil import JsonUtil
from config.config import assert_mapping


class Base(JsonUtil):

    def build_file_path(self, filename):
        """ 拼装要上传文件的路径 """
        # print(f'文件路径：{os.path.join(CASE_FILE_ADDRESS, filename)}')
        return os.path.join(CASE_FILE_ADDRESS, filename)

    def parse_headers(self, headers_list):
        """ 解析头部信息
        headers_list:
            [{"key": "x-auth-token", "value": "aaa"}, {"key": null, "value": null}]
        :return
            {"x-auth-token": "aaa"}
        """
        return {
            header['key']: header['value'].replace('%', '&') for header in headers_list if header.get('key')
        }

    def parse_variables(self, variables_list):
        """ 解析公用变量
        variables_list:
            [
                {"key":"auto_test_token","remark":"token","value":"eyJhbGciOiJIUzI1NiJ9"},
                {"key":"rating_amount","remark":"申请金额","value":"500000"}
            ]
        :return
            {"auto_test_token": "eyJhbGciOiJIUzI1NiJ9", "rating_amount": "500000"}
        """
        return {variable['key']: variable['value'] for variable in variables_list if
                variable.get('key') and variable.get('value') is not None}

    def parse_params(self, params_list):
        """ 解析查询字符串参数
        params_list:
            [{"key": "name", "value": "aaa"}]
        :return
            {"name": "aaa"}
        """
        return {param['key']: param['value'].replace('%', '&') for param in params_list if
                param.get('key') and param.get('value') is not None}

    def parse_extracts(self, extracts_list, extract_key_list):
        """ 解析要提取的参数
        extracts_list:
            [{"key": "project_id", "value": "content.data.id", "remark": "服务id"}]
        return:
            [{"project_id": "content.data.id"}]
        """
        # return [{extract['key']: extract['value']} for extract in extracts_list if extract.get('key')]
        extracts = []
        for extract in extracts_list:
            if extract.get('key') and extract.get('value') is not None:
                extract_key_list.append(extract.get('key'))
                extracts.append({extract['key']: extract['value']})
        return extracts

    def parse_validates(self, validates_list):
        """ 解析断言
        validates:
            [{"key": "1", "value": "content.message", "validate_type": "equals"}]
        return:
            [{"equals": ["1", "content.message"]}]
        """
        return [
            {
                assert_mapping[validate['validate_type']]: [validate['key'], ast.literal_eval(validate['value'])]
            } for validate in validates_list if validate.get('key') and validate.get('value') is not None
        ]

    def parse_form_data(self, form_data_list):
        """ 解析form参数 """
        string, files = {}, {}
        for data in form_data_list:
            if data.get('key'):

                # 字符串
                if data['data_type'] == 'string':
                    string.update({data['key']: data['value']})

                # 上传文件
                elif data['data_type'] == 'file':
                    files.update({
                        data['key']: (
                            data['value'].split('/')[-1],  # 文件名
                            open(self.build_file_path(data['value']), 'rb'),  # 文件流
                            CONTENT_TYPE['.{}'.format(data['value'].split('.')[-1])]  # content-type，根据文件后缀取
                        )
                    })
        return {'string': string, 'files': files}


class ProjectFormatModel(Base):
    """ 格式化服务信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.manager = kwargs.get('manager')
        self.dev = kwargs.get('dev')
        self.test = kwargs.get('test')
        self.uat = kwargs.get('uat')
        self.production = kwargs.get('production')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.variables = self.parse_variables(kwargs.get('variables', {}))
        self.func_files = kwargs.get('func_files')
        self.create_user = kwargs.get('create_user')


class ApiFormatModel(Base):
    """ 格式化接口信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.desc = kwargs.get('desc')
        self.up_func = kwargs.get('up_func')
        self.down_func = kwargs.get('down_func')
        self.choice_host = kwargs.get('choice_host')
        self.method = kwargs.get('method')
        self.addr = kwargs.get('addr')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.data_type = kwargs.get('data_type', 'json').upper()
        self.params = self.parse_params(kwargs.get('params', {}))
        self.data_json = kwargs.get('data_json') if self.data_type == 'JSON' else {}
        self.data_form = self.parse_form_data(kwargs.get('data_form')) if self.data_type == 'DATA' else {}
        self.data_xml = kwargs.get('data_xml', '')
        self.extracts = self.parse_extracts(kwargs.get('extracts', {}), extract_key_list=kwargs.get('extract_list', []))
        self.validates = self.parse_validates(kwargs.get('validates', {}))
        self.module_id = kwargs.get('module_id')
        self.project_id = kwargs.get('project_id')
        self.create_user = kwargs.get('create_user')


class CaseFormatModel(Base):
    """ 格式化用例信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.desc = kwargs.get('desc')
        self.choice_host = kwargs.get('choice_host')
        self.func_files = kwargs.get('func_files')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.variables = self.parse_variables(kwargs.get('variables', {}))
        self.is_run = kwargs.get('is_run')
        self.run_times = kwargs.get('run_times')
        self.module_id = kwargs.get('module_id')
        self.create_user = kwargs.get('create_user')


class StepFormatModel(Base):
    """ 格式化步骤信息 """

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.num = kwargs.get('num')
        self.name = kwargs.get('name')
        self.run_times = kwargs.get('run_times')
        self.up_func = kwargs.get('up_func')
        self.down_func = kwargs.get('down_func')
        self.is_run = kwargs.get('is_run')
        self.headers = self.parse_headers(kwargs.get('headers', {}))
        self.params = self.parse_params(kwargs.get('params', {}))
        self.data_json = kwargs.get('data_json', {})
        self.data_form = self.parse_form_data(kwargs.get('data_form', {}))
        self.data_xml = kwargs.get('data_xml', '')
        self.extracts = self.parse_extracts(kwargs.get('extracts', {}), kwargs.get('extract_list', []))
        self.validates = self.parse_validates(kwargs.get('validates', {}))
        self.data_driver = kwargs.get('data_driver', {})
        self.quote_case = kwargs.get('quote_case', {})
        self.case_id = kwargs.get('case_id')
        self.api_id = kwargs.get('api_id')
        self.project_id = kwargs.get('project_id')
        self.create_user = kwargs.get('create_user')
