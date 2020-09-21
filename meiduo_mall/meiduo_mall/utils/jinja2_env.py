from jinja2 import Environment
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse


def jinja2_environment(**options):
    # 创建环境对象
    env = Environment(**options)
    # 自定义语法
    env.globals.update({
        'static': staticfiles_storage.url,  # 获取静态文件的前缀
        'url': reverse,  # 重定向
    })
    # 返回环境对象
    return env

"""
确保可以使用模板引擎中的{{ static('') }}、{{ url('') }}这类语句
"""
