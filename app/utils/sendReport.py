#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : sendReport.py
# @Software: PyCharm

from datetime import datetime
from threading import Thread

import requests

from app.utils.sendEmail import SendEmail
from app.utils.report.report import render_html_report
from config.config import conf


def by_webhook(content, webhook):
    """ 通过企业微信机器人发送测试报告
    content
    {
      "stat": {
        "testcases": {
          "project": 'atom',
          "total": 1,
          "success": 1,
          "fail": 0
        }
      }
    }
    """
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                       f'任务名：{content["stat"]["testcases"]["project"]} \n'
                       f'>执行用例:<font color="comment"> {content["stat"]["testcases"]["total"]} </font>条\n'
                       f'>成功:<font color="info"> {content["stat"]["testcases"]["success"]} </font>条\n'
                       f'>失败:<font color="warning"> {content["stat"]["testcases"]["fail"]} </font>条\n'
                       f'详情请登录[测试平台]({conf["report_addr"]})查看'
        }
    }
    try:
        print(f'运行结果发送企业微信：{requests.post(webhook, json=data).json()}')
    except Exception as error:
        print(f'向企业微信发送测试报告失败，错误信息：\n{error}')


def by_email(email_server, email_from, email_pwd, email_to, content):
    """ 通过邮件发送测试报告 """
    SendEmail(email_server, email_from, email_pwd, email_to.split(','), render_html_report(content)).send_email()


def send_report(**kwargs):
    """ 封装发送测试报告提供给多线程使用 """
    is_send, send_type, content = kwargs.get('is_send'), kwargs.get('send_type'), kwargs.get('content')
    if is_send == '2' or (is_send == '3' and content['success'] is False):
        if send_type == 'webhook':
            by_webhook(content, kwargs.get('webhook'))
        elif send_type == 'email':
            by_email(kwargs.get('email_server'), kwargs.get('email_from'), kwargs.get('email_pwd'),
                     kwargs.get('email_to'), content)
        elif send_type == 'all':
            by_webhook(content, kwargs.get('webhook'))
            by_email(kwargs.get('email_server'), kwargs.get('email_from'), kwargs.get('email_pwd'),
                     kwargs.get('email_to'), content)


def async_send_report(**kwargs):
    """ 多线程发送测试报告 """
    print('开始多线程发送测试报告')
    Thread(target=send_report, kwargs=kwargs).start()
    print('多线程发送测试报告完毕')


if __name__ == '__main__':
    pass
