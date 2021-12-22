#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
from ... import api
from .models import AutoTestPolyFactoring
from ....baseView import BaseMethodView
from ....utils import restful


class DataPoolView(BaseMethodView):
    """ 数据池 """

    def get(self):
        return restful.success('获取成功', data=[
            data_pool.to_dict() for data_pool in
            AutoTestPolyFactoring.query.filter().order_by(AutoTestPolyFactoring.id.desc()).all()
        ])


api.add_url_rule('/dataPool', view_func=DataPoolView.as_view('dataPool'))
