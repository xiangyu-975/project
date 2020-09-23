from django import http

from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from verifications import constants
from verifications.libs.captcha.captcha import captcha


# Create your views here.

class ImageCodeView(View):
    '''图形验证码'''

    def get(self, request, uuid):
        '''
        :param request:
        :param uuid: 通用唯一识别码,用于唯一表示该图形验证吗属于哪个用户
        :return: image/jpg
        '''
        # 接收和校验参数
        # 实现主体业务逻辑： 生成，保存，响应图形验证码
        # 生成图形验证码
        text, image = captcha.generate_captcha()
        # 保存图形验证码
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        # 响应图形验证码
        return http.HttpResponse(image, content_type='image/jpg')
