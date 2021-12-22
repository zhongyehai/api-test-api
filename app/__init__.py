#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : __init__.py
# @Software: PyCharm
import os

from flask import Flask
from flask_login import LoginManager

from app.utils import globalVariable
from app.utils.log import logger
from config.config import conf, ProductionConfig  # ,logger
from app.baseModel import db

login_manager = LoginManager()
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.conf = conf
    app.config.from_object(ProductionConfig)
    app.logger = logger
    ProductionConfig.init_app(app)

    db.init_app(app)
    db.app = app
    db.create_all()
    login_manager.init_app(app)

    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
