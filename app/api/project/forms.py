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
from .models import Project
from ..user.models import User


class AddProjectForm(BaseForm):
    """ 添加项目参数校验 """
    name = StringField(validators=[DataRequired('项目名称不能为空'), Length(1, 64, message='项目名长度不可超过64位')])
    manager = StringField(validators=[DataRequired('请选择负责人')])
    dev = StringField(validators=[Length(0, 100, message='开发环境域名长度不可超过100位')])
    test = StringField(validators=[DataRequired('测试环境域名必填'), Length(1, 100, message='测试环境域名长度不可超过100位')])
    uat = StringField(validators=[Length(0, 100, message='uat环境域名长度不可超过100位')])
    production = StringField(validators=[Length(0, 100, message='生产环境域名长度不可超过100位')])
    variables = StringField()
    headers = StringField()
    func_files = StringField()

    def validate_name(self, field):
        """ 校验项目名不重复 """
        if Project.get_first(name=field.data):
            raise ValidationError(f'项目名 {field.data} 已存在')

    def validate_manager(self, field):
        """ 校验项目负责人是否存在 """
        if not User.get_first(id=field.data):
            raise ValidationError(f'id为 {field.data} 的用户不存在')


class FindProjectForm(BaseForm):
    """ 查找项目form """
    name = StringField()
    manager = IntegerField()
    create_user = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetProjectByIdForm(BaseForm):
    """ 获取具体项目信息 """
    id = IntegerField(validators=[DataRequired('项目id必传')])

    def validate_id(self, field):
        project = Project.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为 {field.data} 的项目不存在')
        setattr(self, 'project', project)


class DeleteProjectForm(GetProjectByIdForm):
    """ 删除项目 """

    def validate_id(self, field):
        project = Project.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为 {field.data} 的项目不存在')
        else:
            if not self.is_can_delete(project.id, project):
                raise ValidationError(f'不能删除别人负责的项目')
            if project.modules.all():
                raise ValidationError('请先去 接口管理 删除项目下的接口模块')
            if project.case_sets.all():
                raise ValidationError('请先去 用例管理 删除项目下的用例集')
        setattr(self, 'pro_data', project)


class EditProjectForm(GetProjectByIdForm, AddProjectForm):
    """ 修改项目参数校验 """

    def validate_name(self, field):
        """ 校验项目名不重复 """
        old_project = Project.get_first(name=field.data)
        if old_project and old_project.name == field.data and old_project.id != self.id.data:
            raise ValidationError(f'项目名 {field.data} 已存在')
