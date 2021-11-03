#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm

import os

from ...utils.report.report import render_html_report
from ...utils import restful
from ...utils.required import login_required
from .. import api
from ...baseView import BaseMethodView
from ...baseModel import db
from .models import Report
from .forms import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm


@api.route('/report/download', methods=['GET'])
@login_required
def download_report():
    """ 报告下载 """
    form = DownloadReportForm()
    if form.validate():
        return restful.success(data=render_html_report(form.report_content))
    return restful.fail(form.get_error())


@api.route('/report/list', methods=['GET'])
@login_required
def report_list():
    """ 报告列表 """
    form = FindReportForm()
    if form.validate():
        return restful.success(data=Report.make_pagination(form))
    return restful.fail(form.get_error())


class ReportView(BaseMethodView):
    """ 报告管理 """

    def get(self):
        form = GetReportForm()
        if form.validate():
            with db.auto_commit():
                form.report.status = '已读'
            return restful.success('获取成功', data=form.report_content)
        return restful.fail(form.get_error())

    def delete(self):
        form = DeleteReportForm()
        if form.validate():
            with db.auto_commit():
                db.session.delete(form.report)
            os.remove(form.report_path)
            return restful.success('删除成功')
        return restful.fail(form.get_error())


api.add_url_rule('/report', view_func=ReportView.as_view('report'))
