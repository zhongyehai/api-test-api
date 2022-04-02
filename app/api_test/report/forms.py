# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm
import json
import os

from wtforms import IntegerField
from wtforms.validators import ValidationError, DataRequired

from app.utils.globalVariable import REPORT_ADDRESS
from app.baseForm import BaseForm
from ..report.models import Report


class DownloadReportForm(BaseForm):
    """ 报告下载 """
    id = IntegerField(validators=[DataRequired('请选择报告')])

    def validate_id(self, field):
        """ 校验报告是否存在 """
        report = Report.get_first(id=field.data)
        if not report:
            raise ValidationError('报告还未生成, 请联系管理员处理')
        report_path = os.path.join(REPORT_ADDRESS, f'{report.id}.txt')
        if not os.path.exists(report_path):
            raise ValidationError('报告文件不存在, 可能是未生成，请联系管理员处理')
        with open(report_path, 'r') as file:
            report_content = json.load(file)
        setattr(self, 'report', report)
        setattr(self, 'report_path', report_path)
        setattr(self, 'report_content', report_content)


class GetReportForm(DownloadReportForm):
    """ 查看报告 """


class DeleteReportForm(BaseForm):
    """ 删除报告 """
    id = IntegerField(validators=[DataRequired('请选择报告')])

    def validate_id(self, field):
        report = Report.get_first(id=field.data)
        if not report:
            raise ValidationError('报告不存在')
        report_path = os.path.join(REPORT_ADDRESS, f'{report.id}.txt')
        if not report_path:
            raise ValidationError('报告文件不存在, 请联系管理员处理')
        setattr(self, 'report', report)
        setattr(self, 'report_path', report_path)


class FindReportForm(BaseForm):
    """ 查找报告 """
    projectId = IntegerField(validators=[DataRequired('请选择服务')])
    pageNum = IntegerField()
    pageSize = IntegerField()
