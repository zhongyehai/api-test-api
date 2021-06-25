# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:10
# @Author : ZhongYeHai
# @Site :
# @File : file_manage.py
# @Software: PyCharm

from flask import request

from ..utils import restful
from ..utils.required import login_required
from ..utils.globalVariable import os, FILE_ADDRESS
from . import api


@api.route('/upload', methods=['POST'], strict_slashes=False)
# @login_required
def api_upload():
    """ 文件上传 """
    file, skip = request.files['file'], request.form.get('skip')  # 是否覆盖已存在名字的文件
    if os.path.exists(os.path.join(FILE_ADDRESS, file.filename)) and skip != '1':
        return restful.fail(msg='文件已存在，请修改文件名字后再上传', data=file.filename)
    else:
        file.save(os.path.join(FILE_ADDRESS, file.filename))
        return restful.success(msg='上传成功', data=file.filename)


@api.route('/checkFile', methods=['POST'], strict_slashes=False)
@login_required
def check_file():
    """ 检查文件是否存在 """
    return restful.fail('文件已存在') if os.path.exists(request.json.get('address')) else restful.success('文件不存在')
