#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : gunicornConfig.py
# @Software: PyCharm

import gevent.monkey
import multiprocessing

"""
gunicorn的配置文件
"""

gevent.monkey.patch_all()  # gevent的猴子魔法 变成非阻塞

bind = '0.0.0.0:8024'  # 访问地址

# 启动的进程数，
# workers = multiprocessing.cpu_count() * 2 + 1  # 按cpu个数来计算
workers = 1  # 固定写死

worker_class = 'gunicorn.workers.ggevent.GeventWorker'
