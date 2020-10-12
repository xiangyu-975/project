import json
from django.utils import timezone

from django.db import transaction
from django import http
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredMixin, LoginRequiredJSONMixin
from users.models import Address
from decimal import Decimal
from .models import OrderInfo, OrderGoods


# Create your views here.

class OrderSuccessView(LoginRequiredMixin, View):
    '''提供订单页面'''

    def get(self, request):
        order_id = request.GET.get('order_id')
        payment_amount = request.GET.get('payment_amount')
        pay_method = request.GET.get('pay_method')

        context = {
            'order_id': order_id,
            'payment_amount': payment_amount,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)


class OrderCommitView(LoginRequiredJSONMixin, View):
    '''递交订单'''

    def post(self, request):
        '''保存订单的基本信息和商品信息'''
        # 接收参数
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')
        # 校验参数
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('缺少必传参数')
            # 判断address_id是否合法
        # TODO 出现一个bug，如果用户登陆没有收货地址，明明try了，但是还是出现了一个报错，拿不到address_id 但是程序报错
        # TODO 未解决，回顾时候请注意！！
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('参数address_id错误')
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('pay_method 参数错误')
        # 事务的使用(开启一次)
        with transaction.atomic():
            # 在数据库操作之前需要指定保存点(数据库最初的状态)
            save_id = transaction.savepoint()
            # 暴力回滚
            try:
                # 保存订单的基本信息(一)
                # 获取用户
                user = request.user
                # 获取订单编号：时间+user_id = '2020101200000'
                order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('09%d' % user.id)
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal(0.00),
                    freight=Decimal(10.00),
                    pay_method=pay_method,
                    # status='UNPAID' if pay_method == 'ALIPAY' else 'UNSEND'
                    status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'ALIPAY'] else
                    OrderInfo.ORDER_STATUS_ENUM['UNSEND']
                )
                # 保存订单的商品信息(多)
                # 查询redis购物车中已勾选的商品
                redis_conn = get_redis_connection('carts')
                # 所有的购物车数据:包含了勾选与未勾选{b'1':b'1',b'2':b'2',}
                redis_cart = redis_conn.hgetall('carts_%s' % user.id)
                # 被勾选的sku_id：[b'1']
                redis_selected = redis_conn.smembers('selected_%s' % user.id)

                # 构造购物车中被勾选的商品的数据:{b'1':b'1'}
                new_cart_dict = {}
                for sku_id in redis_selected:
                    new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

                # 遍历new_cart_dict,取出其中的sku_id和count(被勾选的)
                sku_ids = new_cart_dict.keys()
                for sku_id in sku_ids:
                    # 每个商品都有多次下单的机会
                    while True:
                        # 读取购物车商品信息
                        sku = SKU.objects.get(id=sku_id)
                        # 获取原始的库存和销量
                        origin_stock = sku.stock
                        origin_sales = sku.sales
                        # 获取要提交商品订单的数量
                        sku_count = new_cart_dict[sku.id]
                        # 判断商品数量是否大于库存，如果大于库存，响应'库存不足'
                        if sku_count > origin_stock:
                            # 库存不足，回滚
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存补足'})

                        import time
                        time.sleep(7)
                        # SKU 减库存，加销量
                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count
                        result =  SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        # 如果在更新数据时，原始数据变化了，返回0，表示有资源抢夺
                        if result == 0:
                            # 如果库存10个 要买1个 下单时候资源抢夺  如果库存依然满足 继续下单，直到库存补足
                            continue
                        # SPU 加销量
                        sku.spu.sales += sku_count
                        sku.spu.save()
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )
                        # 累加订单的商品和总价到订单的基本信息表里
                        order.total_count += sku_count
                        order.total_amount += sku_count * sku.price
                        # 下单成功 跳出
                        break
                # 加上运费
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '下单失败'})
            # 数据库操作成功，明显的递交一次
            transaction.savepoint_commit(save_id)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'order_id': order_id})


class OrderSettlementView(LoginRequiredMixin, View):
    '''结算订单'''

    def get(self, request):
        '''查询并展示要结算订单数据'''
        # 获取登陆用户
        user = request.user
        # 查询用户的收货地址: 查询用户没有被删除的收货地址
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            # 如果没有收货地址显示编辑收货地址
            addresses = None
        # 查询redis购物车中已勾选的商品
        redis_conn = get_redis_connection('carts')
        # 所有的购物车数据:包含了勾选与未勾选{b'1':b'1',b'2':b'2',}
        redis_cart = redis_conn.hgetall('carts_%s' % user.id)
        # 被勾选的sku_id：[b'1']
        redis_selected = redis_conn.smembers('selected_%s' % user.id)

        # 构造购物车中被勾选的商品的数据:{b'1':b'1'}
        new_cart_dict = {}
        for sku_id in redis_selected:
            new_cart_dict[int(sku_id)] = int(redis_cart[sku_id])

        # 遍历new_cart_dict,取出其中的sku_id和count(被勾选的)
        sku_ids = new_cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)

        total_count = Decimal(0.00)
        total_amount = Decimal(0.00)
        # 取出所有的sku
        for sku in skus:
            # 遍历skus给每个商品补充count（数量）和amount（小计）
            sku.count = new_cart_dict[sku.id]
            sku.amount = sku.price * sku.count  # Decimal类型
            # 累加数量和金额
            total_count += sku.count
            total_amount += sku.amount  # 类型不同不能运算

        # 指定默认的邮费
        freight = Decimal(10.00)
        # 构建上下文
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': freight,
            'payment_amount': total_amount + freight,
        }
        return render(request, 'place_order.html', context)
