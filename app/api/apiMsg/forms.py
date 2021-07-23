# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site : 
# @File : forms.py
# @Software: PyCharm

import ast
import re

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from ...baseForm import BaseForm
from ..case.models import Case
from ..step.models import Step
from ..apiMsg.models import ApiMsg
from ..module.models import Module
from ..project.models import Project


class AddApiForm(BaseForm):
    """ 添加接口信息的校验 """
    num = StringField()
    name = StringField(validators=[DataRequired('接口名必传'), Length(1, 128, '接口名长度为1~128位')])
    desc = StringField(validators=[Length(0, 256, message='接口描述长度为0~256位')])
    up_func = StringField()  # 前置条件
    down_func = StringField()  # 后置条件
    method = StringField(validators=[DataRequired('请求方法必传'), Length(1, 32, message='请求方法长度为1~32位')])
    host_index = IntegerField()
    addr = StringField(validators=[DataRequired('接口地址必传')])
    headers = StringField()
    params = StringField()
    data_type = StringField()
    data_form = StringField()
    data_json = StringField()
    extracts = StringField()
    validates = StringField()

    project_id = StringField(validators=[DataRequired('项目id必传')])
    module_id = StringField(validators=[DataRequired('模块id必传')])

    def validate_project_id(self, field):
        """ 校验项目id """
        if not Project.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的项目不存在')

    def validate_module_id(self, field):
        """ 校验模块id """
        if not Module.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的模块不存在')

    def validate_host_index(self, field):
        """ 选择的运行环境，InputRequired对于0无法校验，放在这里校验 """
        if field.data is None:
            raise ValidationError('请选择要运行的host')

    def validate_name(self, field):
        """ 校验同一模块下接口名不重复 """
        if ApiMsg.get_first(name=field.data, module_id=self.module_id.data):
            raise ValidationError(f'当前模块下，名为 {field.data} 的接口已存在')

    def validate_addr(self, field):
        """ 接口地址校验 """
        addr = field.data.split('?')[0]
        if not addr:
            raise ValidationError('接口地址不能为空')

    def validate_extracts(self, field):
        """ 校验提取数据表达式 """
        can = '可用属性：' \
              'http状态码=>status_code、' \
              'http响应耗时=>elapsed、' \
              'url=>url、' \
              'cookie=>cookies、' \
              '头部信息=>headers、' \
              '响应体=>content、text、json  ' \
              '或者正确的正则表达式'
        for index, extract in enumerate(field.data):
            key, value = extract.get('key'), extract.get('value')
            # 变量名和表达式需同时存在
            if (key and not value) or (not key and value):
                raise ValidationError(f'数据提取，第 {index + 1} 行错误，变量名和表达式需同时存在')
            if value:
                if not value.startswith(
                        ('elapsed', 'status_code', 'cookies', 'headers', 'content', 'text', 'json', 'url')) and \
                        not re.compile(r".*\(.*\).*").match(value):
                    raise ValidationError(f'数据提取，第 {index + 1} 行表达式 【{value}】 错误，{can}')

    def validate_validates(self, field):
        """ 校验断言表达式 """
        can = '可用属性：http状态码=>status_code、url=>url、cookie=>cookies、头部信息=>headers、响应体=>content、text、json  或者正确的正则表达式'
        for index, validate in enumerate(field.data):
            key, validate_type, value = validate.get('key'), validate.get('validate_type'), validate.get('value')
            # 变量名和表达式需同时存在
            if (key and not value) or (not key and value):
                raise ValidationError(f'断言，第 {index + 1} 行错误，预期结果和实际结果表达式需同时存在')
            # 实际结果
            if key:
                if not key.startswith(
                        ('elapsed', 'status_code', 'cookies', 'headers', 'content', 'text', 'json', 'url', '$')) and \
                        not re.compile(r".*\(.*\).*").match(key):
                    raise ValidationError(f'断言，第 {index + 1} 行表达式 【{key}】 错误，{can}')
            # 断言类型
            if key and not validate_type:
                raise ValidationError(f'断言，第 {index + 1} 行错误，请选择断言类型')
            # 预期结果
            if value:
                try:
                    ast.literal_eval(value)
                except Exception as error:
                    raise ValidationError(f'断言，第 {index + 1} 行, 预期结果 【{value}】 错误，请明确类型')

    def new_num(self):
        return ApiMsg.get_new_num(self.num.data, module_id=self.module_id.data)


class EditApiForm(AddApiForm):
    """ 修改接口信息 """
    id = IntegerField(validators=[DataRequired('接口id必传')])

    def validate_id(self, field):
        """ 校验接口id已存在 """
        old = ApiMsg.get_first(id=field.data)
        if not old:
            raise ValidationError(f'id为 {field.data} 的接口不存在')
        setattr(self, 'old', old)

    def validate_name(self, field):
        """ 校验接口名不重复 """
        old_api = ApiMsg.get_first(name=field.data, module_id=self.module_id.data)
        if old_api and old_api.id != self.id.data:
            raise ValidationError(f'当前模块下，名为 {field.data} 的接口已存在')


class ValidateProjectId(BaseForm):
    """ 校验项目id """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])

    def validate_projectId(self, field):
        """ 校验项目id """
        if not Project.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的项目不存在')


class RunApiMsgForm(ValidateProjectId):
    """ 运行接口 """
    apis = StringField(validators=[DataRequired('请选择接口，再进行测试')])
    configId = StringField()


class ApiListForm(BaseForm):
    """ 查询接口信息 """
    moduleId = IntegerField(validators=[DataRequired('请选择模块')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetApiById(BaseForm):
    """ 待编辑信息 """
    id = IntegerField(validators=[DataRequired('接口id必传')])

    def validate_id(self, field):
        api = ApiMsg.get_first(id=field.data)
        if not api:
            raise ValidationError(f'id为 {field.data} 的接口不存在')
        setattr(self, 'api', api)


class DeleteApiForm(GetApiById):
    """ 删除接口 """

    def validate_id(self, field):
        api = ApiMsg.get_first(id=field.data)
        if not api:
            raise ValidationError(f'id为 {field.data} 的接口不存在')

        # 校验接口是否被测试用例引用
        case_data = Step.get_first(api_id=field.data)
        if case_data:
            case = Case.get_first(id=case_data.case_id)
            raise ValidationError(f'用例 {case.name} 已引用此接口，请先解除引用')

        project_id = Module.get_first(id=api.module_id).project_id
        if not self.is_can_delete(project_id, api):
            raise ValidationError('不能删除别人项目下的接口')
        setattr(self, 'api', api)
