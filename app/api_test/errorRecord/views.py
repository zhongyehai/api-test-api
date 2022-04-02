#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2022/2/11 17:31
# @Author : ZhongYeHai
# @Site : 
# @File : views.py
# @Software: PyCharm
from app.utils import restful
from app.api_test import api_test
from .models import ErrorRecord
from .forms import FindErrorForm


@api_test.route('/errorRecord/list', methods=['GET'])
# @login_required
def error_record_list():
    """ 错误列表 """
    form = FindErrorForm()
    if form.validate():
        return restful.success(data=ErrorRecord.make_pagination(form))
    return restful.fail(form.get_error())
