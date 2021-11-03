""" 状态和权限校验装饰器 """

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : customDecorator.py
# @Software: PyCharm


from functools import wraps

from flask import request
from flask_login import current_user

from app.api.user.models import User
from app.utils import restful


def login_required(func):
    """ 校验用户的登录状态 token"""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        # 前端拦截器检测到响应为 '登录超时,请重新登录' ，自动跳转到登录页
        return func(*args, **kwargs) if User.parse_token(request.headers.get('X-Token')) else restful.fail('登录超时,请重新登录')

    return decorated_view


def permission_required(permission_name):
    """ 校验当前用户是否有访问当前接口的权限 """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            return restful.forbidden('没有该权限') if not current_user.can(permission_name) else func(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(func):
    """ 校验是否为管理员权限 """
    return permission_required('ADMINISTER')(func)
