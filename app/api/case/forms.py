# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm

import json
import re

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired

from ..sets.models import Set
from ...utils.parse import extract_variables, convert
from ...baseForm import BaseForm
from ..task.models import Task
from .models import Case


class AddCaseForm(BaseForm):
    """ 添加用例的校验 """
    num = StringField()
    name = StringField(validators=[DataRequired('用例名称不能为空')])
    desc = StringField()
    choice_host = StringField(validators=[DataRequired('请选择要运行的环境')])
    func_files = StringField()
    variables = StringField()
    headers = StringField()
    run_times = IntegerField()
    set_id = IntegerField(validators=[DataRequired('请选择用例集')])
    steps = StringField()

    # TODO 校验头部参数，与变量校验方式一致

    def validate_variables(self, field):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用自定义函数文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """

        # 获取待验证的是否有引用的变量
        temp_check = extract_variables(convert(field.data))

        # 校验是否存在有使用了自定义函数但是没有引用自定义函数文件的情况
        if re.search('\${(.*?)}', '{}{}'.format(field.data, json.dumps(self.steps.data)),
                     flags=0) and not self.func_files.data:
            raise ValidationError('参数引用函数后，必须引用函数文件')
        #
        if temp_check:
            raise ValidationError('参数引用${}在业务变量和项目公用变量均没找到'.format(',$'.join(temp_check)))

    def validate_set_id(self, field):
        """ 校验用例集存在 """
        if not Set.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的用例集不存在')

    def validate_name(self, field):
        """ 用例名不重复 """
        if Case.get_first(name=field.data, set_id=self.set_id.data):
            raise ValidationError(f'用例名 {field.data} 已存在')


class EditCaseForm(AddCaseForm):
    """ 修改用例 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        """ 校验用例id已存在 """
        old_data = Case.get_first(id=field.data)
        if not old_data:
            raise ValidationError(f'id为 {field.data} 的用例不存在')
        setattr(self, 'old_data', old_data)

    def validate_name(self, field):
        """ 同一用例集下用例名不重复 """
        old_data = Case.get_first(name=field.data, set_id=self.set_id.data)
        if old_data and old_data.id != self.id.data:
            raise ValidationError(f'用例名 {field.data} 已存在')


class FindCaseForm(BaseForm):
    """ 根据用例集查找用例 """
    name = StringField()
    setId = IntegerField(validators=[DataRequired('请选择用例集')])
    pageNum = IntegerField()
    pageSize = IntegerField()

    def validate_name(self, field):
        if field.data:
            case = Case.query.filter_by(
                set_id=self.setId.data).filter(Case.name.like('%{}%'.format(field.data)))
            setattr(self, 'case', case)


class DeleteCaseForm(BaseForm):
    """ 删除用例 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        case = Case.get_first(id=field.data)
        if not case:
            raise ValidationError(f'没有该用例')

        if not self.is_can_delete(Set.get_first(id=case.set_id).project_id, case):
            raise ValidationError(f'不能删除别人的用例')

        # 校验是否有定时任务已引用此用例
        for task in Task.query.filter(Task.case_id.like(f'%{field.data}%')).all():
            if field.data in json.loads(task.case_id):
                raise ValidationError(f'定时任务 {task.name} 已引用此用例，请先解除引用')

        setattr(self, 'case', case)


class GetCaseForm(BaseForm):
    """ 获取用例信息 """
    id = IntegerField(validators=[DataRequired('用例id必传')])

    def validate_id(self, field):
        case = Case.get_first(id=field.data)
        if not case:
            raise ValidationError(f'id为 {field.data} 的用例不存在')
        setattr(self, 'case', case)


class RunCaseForm(BaseForm):
    """ 运行用例 """
    caseId = StringField(validators=[DataRequired('请选择用例')])

    def validate_caseId(self, field):
        """ 校验用例id存在 """
        case = Case.get_first(id=field.data)
        if not case:
            raise ValidationError(f'id为 {field.data} 的用例不存在')
        setattr(self, 'case', case)
