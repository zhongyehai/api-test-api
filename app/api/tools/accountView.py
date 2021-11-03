#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/11/2 14:02
# @Author : ZhongYeHai
# @Site : 
# @File : accountView.py
# @Software: PyCharm

from flask import request
from flask_login import current_user

from .. import api
from .models import AccountModel, db
from ...utils import restful
from ...baseView import BaseMethodView
from ...utils.required import login_required


@api.route('/account/list')
@login_required
def get_account_list():
    """ 获取账号列表 """
    return restful.success('获取成功', data=AccountModel.make_pagination({
        'page_num': request.args.get('pageNum'),
        'page_size': request.args.get('pageSize'),
        'event': request.args.get('event'),
        'name': request.args.get('name')
    }))


class AccountView(BaseMethodView):
    """ 测试账号管理 """

    def get(self):
        """ 获取用户信息 """
        return restful.success('获取成功', data=AccountModel.get_first(id=request.args.get('id')).to_dict())

    def post(self):
        """ 新增账号 """

        if AccountModel.get_first(event=request.json['event'], account=request.json['account']):
            return restful.fail(f"当前环境下 {request.json['account']} 账号已存在，直接修改即可")
        with db.auto_commit():
            account = AccountModel()
            for key, value in request.json.items():
                setattr(account, key, value)
            account.create_user = current_user.id
            db.session.add(account)
        return restful.success('新增成功', data=account.to_dict())

    def put(self):
        """ 修改账号 """
        # 账号不重复
        account = AccountModel.get_first(event=request.json['event'], account=request.json.get('account'))
        if account and account.id != request.json.get('id'):
            return restful.fail(f'当前环境下账号 {account.aaccount} 已存在', data=account.to_dict())

        old_account = AccountModel.get_first(id=request.json.get('id'))
        with db.auto_commit():
            old_account.update(request.json)
        return restful.success('修改成功', data=old_account.to_dict())

    def delete(self):
        """ 删除账号 """
        with db.auto_commit():
            db.session.delete(AccountModel.get_first(id=request.json.get('id')))
        return restful.success('删除成功')


api.add_url_rule('/account', view_func=AccountView.as_view('account'))
