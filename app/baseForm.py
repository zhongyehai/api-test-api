#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : baseForm.py
# @Software: PyCharm
import re

from flask import request
from flask_login import current_user
from wtforms import Form, ValidationError

from .utils.jsonUtil import JsonUtil
# from app.api_test.project.models import Project
# from app.api_test.func.models import Func
from .utils.parse import extract_functions, parse_function, extract_variables


class BaseForm(Form, JsonUtil):
    """ 初始化Form校验基类，并初统一处理请求参数 """

    def __init__(self):
        """ 初始化的时候获取所有参数一起传给BaseForm """
        data, args = request.get_json(silent=True) or request.form.to_dict(), request.args.to_dict()
        super(BaseForm, self).__init__(data=data, **args)

    def get_error(self):
        """ 获取form校验不通过的报错 """
        return self.errors.popitem()[1][0]

    def is_admin(self):
        """ 角色为2，为管理员 """
        return current_user.role_id == 2

    def is_not_admin(self):
        """ 角色不为2，非管理员 """
        return not self.is_admin()

    def is_can_delete(self, is_manager, obj):
        """
        判断是否有权限删除，
        可删除条件（或）：
        1.当前用户为系统管理员
        2.当前用户为当前数据的创建者
        3.当前用户为当前要删除服务的负责人
        """
        return is_manager or self.is_admin() or obj.is_create_user(current_user.id)

    def set_attr(self, **kwargs):
        """ 根据键值对 对form对应字段的值赋值 """
        for key, value in kwargs.items():
            if hasattr(self, key):
                getattr(self, key).data = value

    def validate_func(self, func_container: dict, func_files: list, content: str, message=''):
        # if not func_container:
        #     func_container = Func.get_func_by_func_file_name(func_files)

        # 使用了自定义函数，但是没有引用函数文件的情况
        functions = extract_functions(content)
        if functions and not func_container:
            raise ValidationError(f'{message}要使用自定义函数则需引用对应的函数文件')

        # 使用了自定义函数，但是引用的函数文件中没有当前函数的情况
        for function in functions:
            func_name = parse_function(function)['func_name']
            if func_name not in func_container:
                raise ValidationError(f'{message}引用的自定义函数【{func_name}】在引用的函数文件中均未找到')

    def validate_is_regexp(self, regexp):
        """ 校验字符串是否为正则表达式 """
        return re.compile(r".*\(.*\).*").match(regexp)

    def validate_variable(self, variables_container: dict, variables: list, content: str, message=''):
        """ 引用的变量需存在 """
        if not variables_container:
            variables_container = {
                variable.get('key'): variable.get('value') for variable in variables if variable.get('key')
            }
        for variable in extract_variables(content):
            if variable not in variables_container:
                raise ValidationError(f'{message}引用的变量【{variable}】不存在')

    def validate_variable_and_header(self, content: list, message1='', message2=''):
        """ 自定义变量格式校验 """
        for index, data in enumerate(content):
            if (data['key'] and not data['value']) or (not data['key'] and data['value']):
                raise ValidationError(f'{message1}{index + 1}{message2}')

    def validate_base_validates(self, data, func_container, func_files):
        """ 校验断言信息 """
        for index, validate in enumerate(data):
            row = f'断言，第【{index + 1}】行，'
            data_source, key = validate.get('data_source'), validate.get('key')
            validate_type = validate.get('validate_type')
            data_type, value = validate.get('data_type'), validate.get('value')

            # 实际结果数据源和预期结果数据类型必须同时存在或者同时不存在
            if (data_source and not data_type) or (not data_source and data_type):
                raise ValidationError(f'{row}若要进行断言，则实际结果数据源和预期结果数据类型需同时存在，若不进行断言，则实际结果数据源和预期结果数据类型需同时不存在')
            elif not data_source and not data_type:  # 都没有，此条断言无效，不解析
                continue
            else:  # 有效的断言
                # 实际结果，选择的数据源为正则表达式，但是正则表达式错误
                if data_source == 'regexp' and not self.validate_is_regexp(key):
                    raise ValidationError(f'{row}正则表达式【{key}】错误')

                if not validate_type:  # 没有选择断言类型
                    raise ValidationError(f'{row}请选择断言类型')

                if value is None:  # 要进行断言，则预期结果必须有值
                    raise ValidationError(f'{row}预期结果需填写')

                if data_type == "str":  # 普通字符串，无需解析，填的是什么就用什么
                    pass
                elif data_type == "variable":  # 预期结果为自定义变量，能解析出变量即可
                    if extract_variables(value).__len__() < 1:
                        raise ValidationError(f'{row}引用的变量表达式【{value}】错误')
                elif data_type == "func":  # 预期结果为自定义函数，校验校验预期结果表达式、实际结果表达式
                    self.validate_func(func_container, func_files, value, message=row)  # 实际结果表达式是否引用自定义函数
                elif data_type == 'json':  # 预期结果为json
                    try:
                        self.dumps(self.loads(value))
                    except Exception as error:
                        raise ValidationError(f'{row}预期结果【{value}】，不可转为【{data_type}】')
                else:  # python数据类型
                    try:
                        eval(f'{data_type}({value})')
                    except Exception as error:
                        raise ValidationError(f'{row}预期结果【{value}】，不可转为【{data_type}】')

    def validate_base_extracts(self, data):
        """ 校验数据提取表达式 """
        for index, validate in enumerate(data):
            row = f'数据提取，第【{index + 1}】行，'
            data_source, key, value = validate.get('data_source'), validate.get('key'), validate.get('value')

            # 实际结果数据源和预期结果数据类型必须同时存在或者同时不存在
            if (data_source and not key) or (not data_source and key):
                raise ValidationError(f'{row}若要进行数据提取，则自定义变量名和提取数据源需同时存在，若不进行提取，则自定义变量名和提取数据源需同时不存在')
            elif not data_source and not key:  # 都没有，此条数据无效，不解析
                continue
            else:  # 有效的数据提取
                # 实际结果，选择的数据源为正则表达式，但是正则表达式错误
                if data_source == 'regexp' and not self.validate_is_regexp(value):
                    raise ValidationError(f'{row}正则表达式【{value}】错误')
