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
from ..project.models import Project
from .models import Module


class AddModelForm(BaseForm):
    """ 添加模块的校验 """
    project_id = IntegerField(validators=[DataRequired('项目id必传')])
    name = StringField(validators=[DataRequired('模块名必传'), Length(0, 64, message='模块名称为0~64位')])
    id = StringField()
    num = IntegerField(validators=[DataRequired('模块序号必传')])

    def validate_project_id(self, field):
        """ 项目id合法 """
        project = Project.get_first(id=field.data)
        if not project:
            raise ValidationError(f'id为 {field.data} 的项目不存在，请先创建')
        setattr(self, 'project', project)

    def validate_name(self, field):
        """ 模块名不重复 """
        old_module = Module.get_first(project_id=self.project_id.data, name=field.data)
        if old_module:
            raise ValidationError(f'当前项目中已存在名为 {field.data} 的模块')

    def new_num(self):
        return Module.get_new_num(self.num.data, project_id=self.project_id.data)


class FindModelForm(BaseForm):
    """ 查找模块 """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetModelForm(BaseForm):
    """ 获取模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = Module.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为 {field.data} 的模块不存在')
        setattr(self, 'module', module)


class ModuleIdForm(BaseForm):
    """ 返回待编辑模块信息 """
    id = IntegerField(validators=[DataRequired('模块id必传')])

    def validate_id(self, field):
        module = Module.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为 {field.data} 的模块不存在')
        setattr(self, 'module', module)


class DeleteModelForm(ModuleIdForm):
    """ 删除模块 """

    def validate_id(self, field):
        module = Module.get_first(id=field.data)
        if not module:
            raise ValidationError(f'id为 {field.data} 的模块不存在')
        if not self.is_can_delete(module.project_id, module):
            raise ValidationError('不能删除别人项目下的模块')
        if module.api_msg.all():
            raise ValidationError('请先删除模块下的接口')
        setattr(self, 'module', module)


class EditModelForm(ModuleIdForm, AddModelForm):
    """ 修改模块的校验 """

    def validate_id(self, field):
        """ 模块必须存在 """
        old_module = Module.get_first(id=field.data)
        if not old_module:
            raise ValidationError(f'id为 {field.data} 的模块不存在')
        setattr(self, 'old_module', old_module)

    def validate_name(self, field):
        """ 同一个项目下，模块名不重复 """
        old_module = Module.get_first(name=field.data, project_id=self.project_id.data)
        if old_module and old_module.id != self.id.data:
            raise ValidationError(f'id为 {self.project_id.data} 的项目下已存在名为 {field.data} 的模块')


class StickModuleForm(BaseForm):
    """ 置顶模块 """
    project_id = IntegerField(validators=[DataRequired('项目id必传')])
    id = IntegerField(validators=[DataRequired('模块id必传')])
