import json
import os

from flask import request

from .. import api
from .models import AutoTestPolyFactoring, YapiDiffRecord
from ...baseView import BaseMethodView
from ...utils import restful
from ...utils.globalVariable import DIFF_RESULT


class DataPoolView(BaseMethodView):
    """ 数据池 """

    def get(self):
        return restful.success('获取成功', data=[data_pool.to_dict() for data_pool in AutoTestPolyFactoring.get_all()])


@api.route('/diffRecord/list')
def get_diff_record_list():
    """ 接口对比结果列表 """
    return restful.success('获取成功', data=YapiDiffRecord.make_pagination({
        'pageNum': request.args.get('pageNum'),
        'pageSize': request.args.get('pageSize'),
        'create_user': request.args.get('create_user'),
        'name': request.args.get('name')
    }))


@api.route('/diffRecord/project')
def get_diff_record_project():
    """ 获取有对比结果的项目列表 """
    project_list = YapiDiffRecord.query.with_entities(YapiDiffRecord.name).distinct().all()
    return restful.success('获取成功', data=[{'key': project[0], 'value': project[0]} for project in project_list])


class DiffRecordView(BaseMethodView):
    """ 接口对比结果 """

    def get(self):
        data_id = request.args.get("id")
        if not data_id:
            return restful.fail('比对id必传')
        with open(os.path.join(DIFF_RESULT, f'{data_id}.json'), 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        return restful.success('获取成功', data=data)


api.add_url_rule('/dataPool', view_func=DataPoolView.as_view('dataPool'))
api.add_url_rule('/diffRecord', view_func=DiffRecordView.as_view('diffRecord'))
