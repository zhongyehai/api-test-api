# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : forms.py
# @Software: PyCharm
from wtforms import StringField, IntegerField

from ....baseForm import BaseForm


class FindErrorForm(BaseForm):
    """ 查找服务form """
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()
