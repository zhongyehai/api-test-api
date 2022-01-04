#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/12/31 11:34
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class SwaggerData(BaseModel):
    """ swagger数据 """
    __tablename__ = 'swagger_data'

    project_name = db.Column(db.String(255), comment='当前服务名字')
    swagger_data = db.Column(db.Text, comment='当前服务在swagger的数据')
