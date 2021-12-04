#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:05
# @Author : ZhongYeHai
# @Site : 
# @File : accountModel.py
# @Software: PyCharm
from ...baseModel import BaseModel, db


class AccountModel(BaseModel):
    """ 测试账号表 """
    __tablename__ = 'account'

    project = db.Column(db.String(50), comment='项目名')
    name = db.Column(db.String(50), comment='账户名')
    account = db.Column(db.String(50), comment='登录账号')
    password = db.Column(db.String(50), comment='登录密码')
    desc = db.Column(db.Text(), comment='备注')
    event = db.Column(db.String(10), comment='环境')

    def to_dict(self, *args, **kwargs):
        return self.base_to_dict(*args, **kwargs)

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


class KYMModule(BaseModel):
    """ KYM分析表 """
    __tablename__ = 'kym'

    project = db.Column(db.String(50), comment='项目名')
    kym = db.Column(db.Text, default='{}', comment='kym分析')

    def to_dict(self):
        return self.base_to_dict(json_to_dict_list=['kym'])
