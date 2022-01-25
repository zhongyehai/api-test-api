#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : baseForm.py
# @Software: PyCharm
from flask import request
from flask_login import current_user
from wtforms import Form, ValidationError

from .api.api_test.func.models import Func
from .utils.jsonUtil import JsonUtil
from .api.api_test.project.models import Project
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

    def is_can_delete(self, project_id, obj):
        """
        判断是否有权限删除，
        可删除条件（或）：
        1.当前用户为系统管理员
        2.当前用户为当前数据的创建者
        3.当前用户为当前要删除服务的负责人
        """
        return Project.is_manager_id(project_id) or self.is_admin() or obj.is_create_user(current_user.id)

    def set_attr(self, **kwargs):
        """ 根据键值对 对form对应字段的值赋值 """
        for key, value in kwargs.items():
            if hasattr(self, key):
                getattr(self, key).data = value

    def validate_func(self, func_container: dict, func_files: list, content: str):
        if not func_container:
            func_container = Func.get_func_by_func_file_name(func_files)

        # 使用了自定义函数，但是没有引用函数文件的情况
        functions = extract_functions(content)
        if functions and not func_container:
            raise ValidationError(f'要使用自定义函数则需引用对应的函数文件')

        # 使用了自定义函数，但是引用的函数文件中没有当前函数的情况
        for function in functions:
            func_name = parse_function(function)['func_name']
            if func_name not in func_container:
                raise ValidationError(f'引用的自定义函数【{func_name}】在引用的函数文件中均未找到')

    def validate_variable(self, variables_container: dict, variables: list, content: str):
        """ 引用的变量需存在 """
        if not variables_container:
            variables_container = {
                variable.get('key'): variable.get('value') for variable in variables if variable.get('key')
            }
        for variable in extract_variables(content):
            if variable not in variables_container:
                raise ValidationError(f'引用的变量【{variable}】不存在')
