# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm

import re

from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from flask_login import current_user

from ...baseForm import BaseForm
from ..case.models import Case
from ..project.models import Project
from .models import Func


class GetFuncFileForm(BaseForm):
    """ 获取函数文件列表 """
    pageNum = IntegerField()
    pageSize = IntegerField()


class HasFuncForm(BaseForm):
    """ 获取自定义函数文件 """
    id = IntegerField(validators=[DataRequired('请输选择函数文件')])

    def validate_id(self, field):
        """ 校验自定义函数文件需存在 """
        func = Func.get_first(id=field.data)
        if not func:
            raise ValidationError(f'id为 【{field.data}】 的函数文件不存在')
        setattr(self, 'func', func)


class SaveFuncForm(HasFuncForm):
    """ 修改自定义函数文件 """
    func_data = StringField()
    func_file_name = StringField(validators=[DataRequired('请输入函数文件名')])

    def validate_func_file_name(self, field):
        """ 校验自定义函数文件名不重复 """
        func = Func.get_first(func_file_name=field.data)

        if func and func.id != self.id.data:
            raise ValidationError(f'函数文件名 {field.data} 已存在')


class CreatFuncForm(BaseForm):
    """ 创建自定义函数文件 """
    func_file_name = StringField(validators=[DataRequired('请输入函数文件名')])

    def validate_func_file_name(self, field):
        """ 校验Python函数文件 """
        if Func.get_first(func_file_name=field.data):
            raise ValidationError(f'函数文件【{field.data}】已经存在')


class DebuggerFuncForm(HasFuncForm):
    """ 调试函数 """
    debug_data = StringField(validators=[DataRequired('请输入要调试的函数')])

    def validate_debug_data(self, field):
        if not re.findall(r"\$\{([\w_]+\([\$\w\.\-/_ =,]*\))\}", field.data):
            raise ValidationError('格式错误，请使用【 ${func(*args)} 】格式')


class DeleteFuncForm(BaseForm):
    """ 删除form """

    func_file_name = StringField(validators=[DataRequired('函数文件必传')])

    def validate_func_file_name(self, field):
        """
        1.校验自定义函数文件需存在
        2.校验是否有引用
        3.校验当前用户是否为管理员或者创建者
        """
        func = Func.get_first(func_file_name=field.data)
        if not func:
            raise ValidationError(f'函数文件【{field.data}】不存在')
        else:
            # 项目引用
            project = Project.query.filter(Project.func_files.like(f'%{field.data}%')).first()
            if project:
                raise ValidationError(f'项目【{project.name}】已引用此函数文件，请先解除依赖再删除')
            # 用例引用
            case = Case.query.filter(Case.func_files.like(f'%{field.data}%')).first()
            if case:
                raise ValidationError(f'用例【{case.name}】已引用此函数文件，请先解除依赖再删除')
            # 用户是管理员或者创建者
            if self.is_not_admin() and not func.is_create_user(current_user.id):
                raise ValidationError('函数文件仅【管理员】或【当前函数文件的创建者】可删除')
        setattr(self, 'func', func)
