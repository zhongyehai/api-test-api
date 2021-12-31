#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site : 
# @File : models.py
# @Software: PyCharm
from app.baseModel import BaseModel, db


class AccountModel(BaseModel):
    """ 测试账号表 """
    __tablename__ = 'account'

    project = db.Column(db.String(255), comment='服务名')
    name = db.Column(db.String(255), comment='账户名')
    account = db.Column(db.String(255), comment='登录账号')
    password = db.Column(db.String(255), comment='登录密码')
    desc = db.Column(db.Text(), comment='备注')
    event = db.Column(db.String(50), comment='环境')

    @classmethod
    def make_pagination(cls, filter):
        """ 解析分页条件 """
        filters = []
        if filter.get("name"):
            filters.append(AccountModel.name.like(f'%{filter.get("name")}%'))
        if filter.get("event"):
            filters.append(AccountModel.event == filter.get("event"))
        return cls.pagination(
            page_num=filter.get("page_num"),
            page_size=filter.get("page_size"),
            filters=filters,
            order_by=cls.created_time.desc())
