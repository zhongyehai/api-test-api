#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/4/16 9:42
# @Author : ZhongYeHai
# @Site : 
# @File : forms.py
# @Software: PyCharm
import ast
import re

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired, Length

from ..apiMsg.models import ApiMsg
from ..case.models import Case
from ....baseForm import BaseForm
from ..project.models import Project
from .models import Step


class GetStepListForm(BaseForm):
    """ 根据用例id获取步骤列表 """
    caseId = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_caseId(self, field):
        case = Case.get_first(id=field.data)
        if not case:
            raise ValidationError(f'id为 {field.data} 的用例不存在')
        setattr(self, 'case', case)


class GetStepForm(BaseForm):
    """ 根据步骤id获取步骤 """
    id = IntegerField(validators=[DataRequired('步骤id必传')])

    def validate_id(self, field):
        step = Step.get_first(id=field.data)
        if not step:
            raise ValidationError(f'id为 {field.data} 的步骤不存在')
        setattr(self, 'step', step)


can = '可用属性：' \
      'http状态码=>status_code、' \
      'http响应耗时(秒)=>elapsed.total_seconds、' \
      'url=>url、' \
      'cookie=>cookies、' \
      '头部信息=>headers、' \
      '响应体=>content、text、json  ' \
      '或者正确的正则表达式'


class AddStepForm(BaseForm):
    """ 添加步骤校验 """

    name = StringField(validators=[DataRequired('步骤名称不能为空'), Length(1, 255, message='步骤名长度为1~255位')])
    up_func = StringField()
    down_func = StringField()
    is_run = IntegerField()
    run_times = IntegerField()
    headers = StringField()
    params = StringField()
    data_form = StringField()
    data_json = StringField()
    data_xml = StringField()
    extracts = StringField()
    validates = StringField()
    data_driver = StringField()
    num = StringField()
    quote_case = IntegerField()

    project_id = IntegerField()
    case_id = IntegerField(validators=[DataRequired('用例id必传')])
    api_id = IntegerField()

    def validate_extracts(self, field):
        """ 校验数据提取信息 """
        if not self.quote_case.data:
            for extract_index, extract in enumerate(field.data):
                key, value = extract.get('key'), extract.get('value')

                # 变量名和表达式需同时存在
                if (key and not value) or (not key and value):
                    raise ValidationError(f'数据提取第【{extract_index + 1}】行错误，变量名和表达式需同时存在')

                if value:
                    if not value.startswith(
                            ('elapsed', 'status_code', 'cookies', 'headers', 'content', 'text', 'json', 'url')) and \
                            not re.compile(r".*\(.*\).*").match(value):
                        raise ValidationError(f'数据提取第【{extract_index + 1}】行表达式【{value}】错误，【{can}】')

    def validate_validates(self, field):
        """ 校验断言信息 """
        if not self.quote_case.data:
            for validate_index, validate in enumerate(field.data):
                key, validate_type, value = validate.get('key'), validate.get('validate_type'), validate.get('value')

                # 变量名和表达式需同时存在
                if (key and not value) or (not key and value):
                    raise ValidationError(f'断言第【{validate_index + 1}】行错误，预期结果和实际结果表达式需同时存在')

                # 实际结果
                if key:
                    if not key.startswith(
                            ('elapsed', 'status_code', 'cookies', 'headers', 'content', 'text', 'json', 'url', '$')) and \
                            not re.compile(r".*\(.*\).*").match(key):
                        raise ValidationError(f'断言第【{validate_index + 1}】行表达式【{key}】错误，【{can}】')

                # 断言类型
                if key and not validate_type:
                    raise ValidationError(f'断言第【{validate_index + 1}】行错误，请选择断言类型')

                # 预期结果
                if value:
                    try:
                        ast.literal_eval(value)
                    except Exception as error:
                        raise ValidationError(f'断言第【{validate_index + 1}】行, 预期结果【{value}】错误，请明确数据类型')

    def validate_project_id(self, field):
        """ 校验服务id """
        if not self.quote_case.data:
            if not Project.get_first(id=field.data):
                raise ValidationError(f'id为【{field.data}】的服务不存在')

    def validate_case_id(self, field):
        """ 校验用例存在 """
        if not Case.get_first(id=field.data):
            raise ValidationError(f'id为【{field.data}】的用例不存在')

    def validate_api_id(self, field):
        """ 校验接口存在 """
        if not self.quote_case.data:
            if not ApiMsg.get_first(id=field.data):
                raise ValidationError(f'id为【{field.data}】的接口不存在')

    def validate_quote_case(self, field):
        """ 不能自己引用自己 """
        if field.data and field.data == self.case_id:
            raise ValidationError(f'不能自己引用自己')


class EditStepForm(AddStepForm):
    """ 修改步骤校验 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        """ 校验步骤id已存在 """
        step = Step.get_first(id=field.data)
        if not step:
            raise ValidationError(f'id为【{field.data}】的步骤不存在')
        setattr(self, 'step', step)
