from django import http
from django.shortcuts import render
from django_redis import get_redis_connection
# Create your views here.
from django.views import View

from . import constants
from verifications.libs.captcha.captcha import captcha


class ImageCodeView(View):
    def get(self, request, uuid):
        '''
        :param request:请求对象
        :param uuid: 唯一标识图形验证码所属于的用户
        :return: image/jpg
        '''
        # 生成图形验证码
        text, image = captcha.generate_captcha()

        # 保存图形验证码
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 响应图形验证码
        return http.HttpResponse(image, content_type='image/jpg')
