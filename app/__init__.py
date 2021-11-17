# encoding: utf-8
import os

from flask import Flask
from flask_login import LoginManager
from flask_apscheduler import APScheduler

from app.utils import globalVariable
from app.utils.log import GetLogger
from config.config import conf, ProductionConfig
from app.baseModel import db

scheduler = APScheduler()
login_manager = LoginManager()
basedir = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.conf = conf
    app.config.from_object(ProductionConfig)
    app.logger = GetLogger().get_logger()
    ProductionConfig.init_app(app)

    db.init_app(app)
    db.app = app
    db.create_all()
    login_manager.init_app(app)

    scheduler.init_app(app)
    scheduler.start()  # 定时任务启动

    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
