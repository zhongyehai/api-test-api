# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm

import validators
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from crontab import CronTab

from ...baseForm import BaseForm
from .models import Task


def validate_email(email_server, email_from, email_pwd, email_to):
    """ 发件邮箱、发件人、收件人、密码 """
    if not email_server:
        raise ValidationError('选择了要邮件接收，则发件邮箱服务器必填')

    if not email_to or not email_from or not email_pwd:
        raise ValidationError('选择了要邮件接收，则发件人、收件人、密码3个必须有值')

    # 校验发件邮箱
    if not validators.email(email_from):
        raise ValidationError(f'发件人邮箱 {email_from} 格式错误')

    if '@qq' not in email_from.lower() and '@bbd' not in email_from.lower():
        raise ValidationError('发件邮箱暂时只支持qq邮箱和公司邮箱')

    # 校验收件邮箱
    for mail in email_to.split(','):
        if not validators.email(mail):
            raise ValidationError(f'收件人邮箱 {mail} 格式错误')


def validate_webhook(webhook):
    """ 校验webhook地址是否合法 """
    if not webhook:
        raise ValidationError(f'选择了要微信群接收，则webhook地址必填')
    if not webhook.startswith('https://'):
        raise ValidationError(f'webhook地址错误: {webhook}')


class AddTaskForm(BaseForm):
    """ 添加定时任务的校验 """
    project_id = IntegerField(validators=[DataRequired('请选择项目')])
    module_id = StringField()
    case_id = StringField()
    choice_host = StringField(validators=[DataRequired('请选择要运行的环境')])
    name = StringField(validators=[DataRequired('任务名不能为空')])
    webhook = StringField()
    is_send = StringField(validators=[DataRequired('请选择是否发送报告')])
    send_type = StringField()
    email_server = StringField()
    email_to = StringField()
    email_from = StringField()
    email_pwd = StringField()
    cron = StringField()
    num = StringField()

    def validate_is_send(self, field):
        """ 发送报告类型 1.不发送、2.始终发送、3.仅用例不通过时发送 """
        if field.data in ['2', '3']:

            # 接收地址验证：webhook，email，all
            # 仅微信群
            if self.send_type.data == 'webhook':
                validate_webhook(self.webhook.data)
            elif self.send_type.data == 'email':
                validate_email(self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data)
            elif self.send_type.data == 'all':
                validate_webhook(self.webhook.data)
                validate_email(self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data)

    def validate_cron(self, field):
        """ 校验cron格式 """
        try:
            if len(field.data.strip().split(' ')) == 6:
                field.data += ' *'
            CronTab(field.data)
        except Exception as error:
            raise ValidationError(f'时间配置 {field.data} 错误，需为cron格式, 请检查')

    def validate_name(self, field):
        """ 校验任务名不重复 """
        if Task.get_first(project_id=self.project_id.data, name=field.data):
            raise ValidationError(f'当前项目中，任务名 {field.data} 已存在')

    def new_num(self):
        return Task.get_new_num(self.num.data, project_id=self.project_id.data)


class HasTaskIdForm(BaseForm):
    """ 校验任务id已存在 """
    id = IntegerField(validators=[DataRequired('任务id必传')])

    def validate_id(self, field):
        """ 校验id存在 """
        task = Task.get_first(id=field.data)
        if not task:
            raise ValidationError(f'任务id {field.data} 不存在')
        setattr(self, 'task', task)


class RunTaskForm(HasTaskIdForm):
    """ 运行任务 """


class EditTaskForm(AddTaskForm, HasTaskIdForm):
    """ 编辑任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = Task.get_first(id=field.data)
        if not task:
            raise ValidationError(f'任务id {field.data} 不存在')
        elif task.status != '禁用中':
            return ValidationError(f'任务 {task.name.data} 的状态不为禁用中，请先禁用再修改')
        setattr(self, 'task', task)

    def validate_name(self, field):
        """ 校验任务名不重复 """
        old = Task.get_first(project_id=self.project_id.data, name=field.data)
        if old and old.id != self.id.data:
            raise ValidationError(f'当前项目中，任务名 {field.data} 已存在')


class GetTaskListForm(BaseForm):
    """ 获取任务列表 """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    pageNum = IntegerField()
    pageSize = IntegerField()


class FindTaskForm(BaseForm):
    """ 查找任务信息 """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    taskName = StringField()
    page = IntegerField()
    sizePage = IntegerField()

    def validate_taskName(self, field):
        """ 校验任务名存在 """
        task_select = Task.query.filter_by(project_id=self.projectId.data)
        if field.data:
            task_select = task_select.filter(Task.name.like('%{}%'.format(field.data)))
            if not task_select:
                raise ValidationError(f'名为 {field.data} 的任务不存在')
        setattr(self, 'task_filter', task_select)


class DeleteTaskIdForm(HasTaskIdForm):
    """ 删除任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = Task.get_first(id=field.data)
        if not task:
            raise ValidationError(f'任务id 【{field.data}】 不存在')
        if task.status != '禁用中':
            raise ValidationError(f'请先禁用任务 【{task.name}】')
        if not self.is_can_delete(task.project_id, task):
            raise ValidationError(f'不能删除别人的数据 【{task.name}】')
        setattr(self, 'task', task)
