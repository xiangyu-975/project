import json, base64, pickle

import logging
from django.shortcuts import render
from django.views import View
from django import http
from django_redis import get_redis_connection

from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE

# Create your views here.

logger = logging.getLogger('django')


class CartsSelectAllView(View):
    '''全选购物车'''

    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected', True)
        # 校验参数
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')

        # 判断用户是否登录
        user = request.user
        if user is not None and user.is_authenticated:
            # 用户已登录，操作redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 获取所有的记录{b'3':b'5',b'3':b'6'}
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 获取字典中所有的key [b'3',b'5']
            redis_sku_ids = redis_carts.keys()
            # 判断用户是否全选
            if selected:
                # 全选
                pl.sadd('selected_%s' % user.id, *redis_sku_ids)
            else:
                # 取消全选
                pl.srem('selected_%s' % user.id, *redis_sku_ids)
                pl.execute()  # 设置的时候用到就可以
            # 响应结果
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        else:
            # 用户未登录，操作cookie购物车
            cart_str = request.COOKIES.get('carts')
            # 构造响应数据
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            if cart_str:
                # 将cart_str转为bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 将bytes类型的字符串转bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 将bytes的字典转化为真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
                # 遍历所有的购物车记录   (未登录核心代码)
                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected  # True  / False
                # 将原始的购物车数据编码，将cart_dict转bytes
                cart_dict_bytes = pickle.dumps(cart_dict)
                # 将bytes字典转bytes的str
                cart_str_bytes = base64.b64encode(cart_dict_bytes)
                # 将bytes类型转为str
                cookie_carts_str = cart_str_bytes.decode()
                # 重新将购物车数据写入cookie
                response.set_cookie('carts', cookie_carts_str)
            return response


class CartsView(View):
    '''购物车管理'''

    def post(self, request):
        '''保存购物车'''
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)  # 可选
        # 校验参数
        # 判断参数是否齐全
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 校验sku参数是否合法
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('参数sku_id错误')
        # 校验参数是否是数字
        try:
            count = int(count)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('参数count错误')
        # 校验参数是否是bool
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('selected参数错误')
        # 判断用户是否登陆
        user = request.user
        if user.is_authenticated:
            # 如果已登陆操作Redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 需用用增量计算的形式保存商品数据
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            # 保存商品勾选状态
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            # 执行
            pl.execute()
            # 响应结果
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
        else:
            # 如果用户未登录,操作cookie购物车
            # 获取cookie中的购物车数据,并判断是否有购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str转为bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 将bytes类型的字符串转bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 将bytes的字典转化为真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
            '''
            {
                "sku_id1":{
                    "count":"1",
                    "selected":"True"
                },
            }
            '''
            # 判断当前要添加的商品在cart_dict中是否存在
            if sku_id in cart_dict:
                # 购物车已存在，增量计算
                origin_count = cart_dict[sku_id]['count']
                count += origin_count
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将原始的购物车数据编码，将cart_dict转bytes
            cart_dict_bytes = pickle.dumps(cart_dict)
            # 将bytes字典转bytes的str
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            # 将bytes类型转为str
            cookie_carts_str = cart_str_bytes.decode()
            # 将新的购物车数据写入cookie
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            response.set_cookie('carts', cookie_carts_str)
            # 响应结果
            return response

    def get(self, request):
        '''查询购物车'''
        # 判断用户是否登陆
        user = request.user
        if user.is_authenticated:
            # 已登陆查询redis购物车
            # 创建连接redis的连接
            redis_conn = get_redis_connection('carts')
            # 查询hash数据 {b'3':b'1'}
            redis_cart = redis_conn.hgetall('carts_%s' % user.id)
            # 查询set数据 {b'3'}
            cart_selected = redis_conn.smembers('selected_%s' % user.id)
            cart_dict = {}
            # 将redis_cart和redis_selected进行数据结构的构造，合并数据，数据结构和未登录用户购物车数据结构一致
            for sku_id, count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 未登录查询cookie购物车
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str转为bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 将bytes类型的字符串转bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 将bytes的字典转化为真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
        # 构造响应数据
        # 获取字典中所有的key,(sku_id)
        sku_ids = cart_dict.keys()
        # for sku_id in sku_ids:
        #     sku = SKU.objects.get(id=sku_id)
        # 一次性查询出所有skus
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': str(cart_dict.get(sku.id).get('selected')),  # 将True转为'True' 方便json解析
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # Decimal ('10.2')中取出'10.2',方便json解析
                'amount': str(sku.price * cart_dict.get(sku.id).get('count'))
            })
        context = {
            'cart_skus': cart_skus,
        }
        return render(request, 'cart.html', context)

    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 判断参数是否齐全
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品sku_id不存在')
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            return http.HttpResponseForbidden('参数count有误')
        # 判断selected是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return http.HttpResponseForbidden('参数selected有误')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，修改redis购物车
            redis_conn = get_redis_connection('carts')
            # 由于后端收到的数据是最终结果，所以覆盖输入
            # redis_conn.hincrby() # 使用新值加旧值（增量）
            redis_conn.hset('carts_%s' % user.id, sku_id, count)
            pl = redis_conn.pipeline()
            # 修改勾选的状态
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
            # 执行
            pl.execute()
            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'price': sku.price,
                'amount': sku.price * count,
                'default_image_url': sku.default_image.url
            }
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
        else:
            # 如果用户未登录,操作cookie购物车
            # 获取cookie中的购物车数据,并判断是否有购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str转为bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 将bytes类型的字符串转bytes类型的字典
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                # 将bytes的字典转化为真正的字典
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
            '''
            {
                "sku_id1":{
                    "count":"1",
                    "selected":"True"
                },
            }
            '''
            # 覆盖写入,由于后端收到的是最终的结果
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            # 将原始的购物车数据编码，将cart_dict转bytes
            cart_dict_bytes = pickle.dumps(cart_dict)
            # 将bytes字典转bytes的str
            cart_str_bytes = base64.b64encode(cart_dict_bytes)
            # 将bytes类型转为str
            cookie_carts_str = cart_str_bytes.decode()
            # 将新的购物车数据写入cookie
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_carts_str)
            # 响应结果
            return response

    def delete(self, request):
        '''删除购物车'''
        # 接收和校验参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 判断用户是否登陆
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('商品不存在')
        # 判断用户是否登陆
        user = request.user
        if user is not None and user.is_authenticated:
            # 用户已登陆，删除redis中的购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 删除键，等于删除了整条记录
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            # 删除数据后,没有响应数据,直接返回状态码即可
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除购物车成功'})
        else:
            # 用户未登录，删除cookie中
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
            if sku_id in cart_dict:
                del cart_dict[sku_id]  # 如果删除的key是不存在的，会抛出一个异常
                cookie_cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cookie_cart_str)
            return response
