# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : errors.py
# @Software: PyCharm
import traceback

import requests
from flask import current_app, request

from ..utils import restful
from . import ui_test
from config.config import conf


@ui_test.app_errorhandler(404)
def page_not_found(e):
    """ 捕获404的所有异常 """
    # current_app.logger.exception(f'404错误url: {request.path}')
    return restful.url_not_find(msg=f'接口 {request.path} 不存在')


@ui_test.app_errorhandler(Exception)
def error_handler(e):
    """ 捕获所有服务器内部的异常 """
    # 把错误发送到 即时达推送 的 系统错误 通道
    try:
        current_app.logger.error(f'系统出错了: {e}')
        requests.post(
            url=conf['error_push']['url'],
            json={
                'key': conf['error_push']['key'],
                'head': f'{conf["SECRET_KEY"]}报错了',
                'body': f'{e}'
            }
        )
    except:
        pass
    current_app.logger.exception(f'触发错误url: {request.path}\n{traceback.format_exc()}')
    return restful.error(f'服务器异常: {e}')
