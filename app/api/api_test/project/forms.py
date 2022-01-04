# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm
import validators
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, Length, DataRequired

from ....baseForm import BaseForm
from .models import Project
from ...user.models import User


class AddProjectForm(BaseForm):
    """ 添加服务参数校验 """
    name = StringField(validators=[DataRequired('服务名称不能为空'), Length(1, 255, message='服务名长度不可超过255位')])
    manager = StringField(validators=[DataRequired('请选择负责人')])
    dev = StringField(validators=[Length(0, 255, message='开发环境域名长度不可超过255位')])
    test = StringField(validators=[DataRequired('测试环境域名必填'), Length(1, 255, message='测试环境域名长度不可超过255位')])
    uat = StringField(validators=[Length(0, 255, message='uat环境域名长度不可超过255位')])
    production = StringField(validators=[Length(0, 255, message='生产环境域名长度不可超过255位')])
    variables = StringField()
    headers = StringField()
    func_files = StringField()
    swagger = StringField()

    def validate_name(self, field):
        """ 校验服务名不重复 """
        if Project.get_first(name=field.data):
            raise ValidationError(f'服务名【{field.data}】已存在')

    def validate_manager(self, field):
        """ 校验服务负责人是否存在 """
        if not User.get_first(id=field.data):
            raise ValidationError(f'id为【{field.data}】的用户不存在')

    def validate_swagger(self, field):
        """ 校验swagger地址是否正确 """
        if field.data and validators.url(field.data) is not True:
            raise ValidationError(f'swagger地址【{field.data}】不正确')


class FindProjectForm(BaseForm):
    """ 查找服务form """
    name = StringField()
    manager = IntegerField()
    create_user = IntegerField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetProjectByIdForm(BaseForm):
    """ 获取具体服务信息 """
    id = IntegerField(validators=[DataRequired('服务id必传')])

    def validate_id(self, field):
        project = Project.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的服务不存在')
        setattr(self, 'project', project)


class DeleteProjectForm(GetProjectByIdForm):
    """ 删除服务 """

    def validate_id(self, field):
        project = Project.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为【{field.data}】的服务不存在')
        else:
            if not self.is_can_delete(project.id, project):
                raise ValidationError(f'不能删除别人负责的服务')
            if project.modules:
                raise ValidationError('请先去 接口管理 删除服务下的接口模块')
        setattr(self, 'pro_data', project)


class EditProjectForm(GetProjectByIdForm, AddProjectForm):
    """ 修改服务参数校验 """

    def validate_name(self, field):
        """ 校验服务名不重复 """
        old_project = Project.get_first(name=field.data)
        if old_project and old_project.name == field.data and old_project.id != self.id.data:
            raise ValidationError(f'服务名【{field.data}】已存在')
