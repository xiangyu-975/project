from django import http

from django.shortcuts import render
from django.views import View
from goods.models import GoodsCategory, SKU
from contents.utils.utils import get_categories
# 分页器（有100W字文字，转化为一本书，先规定每页多少字，再计算出有多少页）
# 数据库的记录就是文字，我们需要考虑在分页时每页记录的条数，然后得出一共多少页
from django.core.paginator import Paginator
# Create your views here.
from goods.utils import get_breadcrumb


class ListView(View):
    '''商品的列表页'''

    def get(self, request, category_id, page_num):
        '''查询并渲染商品列表页'''
        # 校验category_id的范围：11111111111
        try:
            # 三级类别
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('参数category_id不存在')
        # 获取sort（排序规则）：如果sort没有值，取default
        sort = request.GET.get('sort', 'default')
        # 根据sort选择排序字段，排序字段必须是模型类的属性
        if sort == 'price':
            sort_field = 'price'  # 按照价格由低到高排序
        elif sort == 'hot':
            sort_field = '-sales'  # 按照销量从高到低排序
        else:  # 只要不是'price'和'sales'其他的所有情况都归为'default'
            sort = 'default'  # 当出现了？sort=itcast 也把sort设置为'default'
            sort_field = 'create_time'
        # 查询商品分类
        categories = get_categories()
        # 查询面包屑导航:一级 -> 二级 -> 三级
        breadcrumb = get_breadcrumb(category)
        # 分页和排序查询：category查询sku,一查多,一方的模型对象，多方关联字段.all/filter
        # skus = SKU.objects.filter(category=category,is_launcher=True)   # 无经验查询
        # skus = SKU.objects.filter(category_id=category_id,is_launcher=True)   # 无经验查询
        # skus = category.sku_set.filter(is_launcher=True).order_by('排序字段:create_time,price,-sales')  # 有经验的查询
        skus = category.sku_set.filter(is_launched=True).order_by(sort_field)  # 有经验的查询

        # 创建分页器
        # Paginator('要分页的记录','每页记录的条数')
        paginator = Paginator(skus, 5)
        # 获取用户当前要看的数据
        page_skus = paginator.page(page_num)
        # 获取总页数:前端的插件需要使用
        total_page = paginator.num_pages
        # 构造上下文
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
        }
        return render(request, 'list.html', context)
