# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from ...baseForm import BaseForm
from ..case.models import Case
from ..project.models import Project
from .models import Set


class AddCaseSetForm(BaseForm):
    """ 添加用例集的校验 """
    project_id = StringField(validators=[DataRequired('请先选择首页项目')])
    name = StringField(validators=[DataRequired('用例集名称不能为空'), Length(0, 128, message='接口名长度为0~128位')])
    num = StringField(validators=[DataRequired('用例集序号必传')])

    def validate_project_id(self, field):
        """ 校验项目id """
        if not Project.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的项目不存在')

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        if Set.get_first(name=field.data, project_id=self.project_id.data):
            raise ValidationError(f'用例集名字 {field.data} 已存在')

    def new_num(self):
        return Set.get_new_num(self.num.data, project_id=self.project_id.data)


class GetCaseSetEditForm(BaseForm):
    """ 返回待编辑用例集合 """
    id = IntegerField(validators=[DataRequired('用例集id必传')])

    def validate_id(self, field):
        edit = Set.get_first(id=field.data)
        if not edit:
            raise ValidationError('没有此用例集')
        setattr(self, 'edit', edit)


class DeleteCaseSetForm(GetCaseSetEditForm):
    """ 删除用例集 """

    def validate_id(self, field):
        case_set = Set.get_first(id=field.data)
        if not self.is_can_delete(case_set.project_id, case_set):
            raise ValidationError('不能删除别人项目下的用例集')
        if Case.get_first(case_set_id=field.data):
            raise ValidationError('请先删除集合下的接口用例')
        setattr(self, 'caseSet', case_set)


class EditCaseSetForm(GetCaseSetEditForm, AddCaseSetForm):
    """ 编辑用例集 """

    def validate_id(self, field):
        """ 用例集id已存在 """
        case_set = Set.get_first(id=field.data)
        if not case_set:
            raise ValidationError(f'不存在id为 {field.data} 的用例集')
        setattr(self, 'case_set', case_set)

    def validate_name(self, field):
        """ 校验用例集名不重复 """
        old_set = Set.get_first(name=field.data, project_id=self.project_id.data)
        if old_set and old_set.id != self.id.data:
            raise ValidationError(f'用例集名字 {field.data} 已存在')


class FindCaseSet(BaseForm):
    """ 查找用例集合 """
    pageNum = IntegerField()
    pageSize = IntegerField()
    projectId = IntegerField(validators=[DataRequired('项目id必传')])

    def validate_projectId(self, field):
        all_sets = Project.get_first(id=field.data).case_sets
        setattr(self, 'all_sets', all_sets)
