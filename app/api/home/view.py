#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/5/24 14:26
# @Author : ZhongYeHai
# @Site : 
# @File : index.py
# @Software: PyCharm

import json

from flask_login import current_user

from app.api.case.models import Case
from app.api.project.models import Project
from app.api.task.models import Task
from app.utils import restful
from app.utils.required import login_required
from app.utils.runHttpRunner import RunApi

from .. import api

from app.api.apiMsg.models import ApiMsg
from app.api.step.models import Step
from app.api.module.models import Module


@api.route('/count/title', methods=['GET'])
@login_required
def count_title():
    return restful.success('获取成功', data={
        'project': len(Project.get_all()),
        'api': len(ApiMsg.get_all()),
        'case': len(Case.get_all()),
        # 'step': len(Step.get_all()),
        'task': len(Task.get_all())
    })
