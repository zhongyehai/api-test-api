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

    project = db.Column(db.String(255), comment='项目名')
    name = db.Column(db.String(255), comment='账户名')
    account = db.Column(db.String(255), comment='登录账号')
    password = db.Column(db.String(255), comment='登录密码')
    desc = db.Column(db.Text(), comment='备注')
    event = db.Column(db.String(50), comment='环境')

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

    project = db.Column(db.String(255), comment='项目名')
    kym = db.Column(db.Text, default='{}', comment='kym分析')

    def to_dict(self):
        return self.base_to_dict(to_dict=['kym'])


class YapiDiffRecord(BaseModel):
    """ 数据比对记录 """
    __tablename__ = 'yapi_diff_record'

    name = db.Column(db.String(255), comment='比对标识，全量比对，或者具体分组的比对')
    is_changed = db.Column(db.Integer, default=0, comment='对比结果，1有改变，0没有改变')
    diff_summary = db.Column(db.Text, comment='比对结果数据')

    @classmethod
    def make_pagination(cls, attr):
        """ 解析分页条件 """
        filters = []
        if attr.get('name'):
            filters.append(YapiDiffRecord.name.like(f'%{attr.get("name")}%'))
        if attr.get('create_user'):
            filters.append(YapiDiffRecord.create_user == attr.get('create_user'))
        return cls.pagination(
            page_num=attr.get('pageNum', 1),
            page_size=attr.get('pageSize', 20),
            filters=filters,
            order_by=cls.created_time.desc())

    def to_dict(self):
        return self.base_to_dict()


class AutoTestPolyFactoring(BaseModel):
    """ 数据池 """
    __tablename__ = 'auto_test_poly_factoring'
    asset_code = db.Column(db.String(100), nullable=True, default='', comment='资产编号')
    payment_no = db.Column(db.String(100), nullable=True, default='', comment='付款单编号')
    bill_code = db.Column(db.String(100), nullable=True, default='', comment='付款申请单编号')
    batch_no = db.Column(db.String(40), nullable=True, unique=True, default='', comment='批次号')
    batch_code = db.Column(db.String(40), nullable=True, default='', comment='批次号（编号）')
    confirm_date = db.Column(db.TIMESTAMP, nullable=True, default=None, comment='定数时间')
    product_id = db.Column(db.String(40), nullable=True, default='', comment='融资产品id')
    product_name = db.Column(db.String(60), nullable=True, default='', comment='产品名称')
    supplier_org_id = db.Column(db.String(40), nullable=True, default='', comment='债权人公司id')
    supplier_org_name = db.Column(db.String(128), nullable=True, default='', comment='债权人（特定供应商）')
    project_org_id = db.Column(db.String(40), nullable=True, default='', comment='债务人公司id')
    project_org_name = db.Column(db.String(128), nullable=True, default='', comment='债务人（项目公司）')
    purchaser_org_name = db.Column(db.String(128), nullable=True, default='', comment='核心企业名称')
    purchaser_org_id = db.Column(db.String(40), nullable=True, default='', comment='核心企业公司id')
    finance_money = db.Column(db.String(128), nullable=True, default='', comment='融资金额')
    file_upload = db.Column(db.String(10), nullable=True, default='0', comment='文件上传状态(0为上传;1已上传)')
    pledge_init = db.Column(db.String(10), nullable=True, default='0', comment='中登初验(0未进行;1已初验；2已中登)')
    agreement_create = db.Column(db.String(10), nullable=True, default='0', comment='协议生成(0为未生成)')
    document_collect_status = db.Column(db.String(10), nullable=True, default='1', comment='文件收集状态（1未开始;2进行中;3已完成）')
    access_audit_status = db.Column(db.String(10), nullable=True, default='1', comment='准入审核状态（1未开始;2进行中;3不通过;4通过）')
    filter_compare_status = db.Column(db.String(10), nullable=True, default='1', comment='初筛对比状态（1未开始;2进行中;3已完成）')
    six_order_match_status = db.Column(db.String(10), nullable=True, default='1',
                                       comment='六单匹配状态（1未开始,2初审中,3初审不通过,4复审中,5复审通过）')
    pledge_init_status = db.Column(db.String(10), nullable=True, default='1',
                                   comment='中登初验状态（1未开始;2进行中;3复核中;4有风险通过;5无风险通过）')
    agreement_audit_status = db.Column(db.String(10), nullable=True, default='1', comment='协议审核状态（1未开始;2进行中;3不通过;4通过）')
    pledge_status = db.Column(db.String(10), nullable=True, default='1', comment='中登登记状态（1未开始;2进行中;3复核中;4有风险通过;5无风险通过）')
    exception_status = db.Column(db.String(10), nullable=True, default='1', comment='异常状态')
    eliminate_apply_status = db.Column(db.String(10), nullable=True, default='1', comment='剔单申请状态(1默认状态;2剔除申请中;3已剔除；)')
    revoke_status = db.Column(db.String(10), nullable=True, default='1', comment='撤回状态(1默认状态；2已撤回)')
    enable_flag = db.Column(db.String(10), nullable=True, default='1', comment='是否可用（0：不可用；1：可用）')

    def to_dict(self):
        return self.base_to_dict()
