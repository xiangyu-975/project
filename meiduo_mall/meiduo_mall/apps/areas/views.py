from django import http
import logging
from django.shortcuts import render
from meiduo_mall.utils.response_code import RETCODE
# Create your views here.
from django.views import View
from areas.models import Area
from django.core.cache import cache

logger = logging.getLogger('django')


class AreasView(View):
    '''省市区三级联动'''

    def get(self, request):
        # 判断当前要查询省份数据还是市份数据
        area_id = request.GET.get('area_id')
        if not area_id:
            # 获取并判断是否有缓存
            province_list = cache.get('province_list')
            if not province_list:
                # 查询省级数据
                try:
                    # Area.objects.filter(属性名__条件表达式=值)
                    province_model_list = Area.objects.filter(parent__isnull=True)
                    # 将模型列表转换成字典列表
                    province_list = []
                    for province_model in province_model_list:
                        province_dict = {
                            'id': province_model.id,
                            'name': province_model.name
                        }
                        province_list.append(province_dict)
                    # 缓存省份字典列表数据:默认存储在default数据库中
                    cache.set('province_list', province_list, 3600)
                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询省份数据错误'})
            # 响应省级JSON数据
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            '''
            {
              "code":"0",
              "errmsg":"OK",
              "sub_data":{
                  "id":130000,
                  "name":"河北省",
                  "subs":[
                      {
                          "id":130100,
                          "name":"石家庄市"
                      },
                      ......
                  ]
              }
            }
            '''
            # 判断是否有缓存
            sub_data = cache.get('sub_area_' + area_id)
            if not sub_data:
                # 查询城市或者区县数据
                try:
                    parent_model = Area.objects.get(id=area_id)
                    # sub_model_list = parent_model.area_set.all()
                    sub_model_list = parent_model.subs.all()
                    # 将子级模型列表转化成字典列表
                    sub_list = []
                    for sub_model in sub_model_list:
                        sub_dict = {
                            "id": sub_model.id,
                            "name": sub_model.name,
                        }
                        sub_list.append(sub_dict)
                    # 构造子级JSON数据
                    sub_data = {
                        'id': parent_model.id,  # 父级id
                        'name': parent_model.name,  # 父级name
                        'subs': sub_list  # 父级子集
                    }
                    # 缓存城市或者区县
                    cache.set('sub_area_' + area_id, sub_data, 3600)

                except Exception as e:
                    logger.error(e)
            # 响应城市或者区县JSON数据
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})
