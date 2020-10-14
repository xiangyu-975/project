# 静态化首页
import os
from collections import OrderedDict
from django.template import loader
from contents.models import ContentCategory
from contents.utils.utils import get_categories
from django.conf import settings


def generate_static_index_html():
    '''静态化首页'''
    # 查询首页数据
    # 查询并展示商品分类
    categories = get_categories()
    # 查询所有广告类别
    contents = OrderedDict()
    content_categories = ContentCategory.objects.all()
    for content_category in content_categories:
        contents[content_category.key] = content_category.content_set.filter(status=True).order_by(
            'sequence')  # 查询到未下架的广告并排序
    # 使用广告类别查询出该类别对应的所有广告内容
    # 构造上下文
    context = {
        'categories': categories,
        'contents': contents
    }
    # 渲染模板
    # 先使用模板文件
    template = loader.get_template('index.html')
    # 再使用上下文渲染模板文件
    html_text = template.render(context)
    # 将模板文件写入静态路径
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)
