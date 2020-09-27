import logging
from django import http
from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
# Create your views here.
from django.views import View
from django.conf import settings
from meiduo_mall.utils.response_code import RETCODE

# 创建日志输入器
logger = logging.getLogger('django')


class QQAuthUserView(View):
    '''处理QQ登陆回调：oauth_callback'''

    def get(self, request):
        '''处理QQ回调的业务逻辑'''
        # 获取code
        code = request.GET.get('code')
        if code is None:
            return http.HttpResponseServerError('获取code失败')
        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 使用code获取access_token
            access_token = oauth.get_access_token(code)
            # 使用access_token获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('OAuth2.0认证失败')
            # 使用openid判断该QQ用户是否绑定过美多商城的用户


class QQAuthURLView(View):
    '''
    提供QQ登陆页面网址
    https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id=xxx&redirect_uri=xxx&state=xxx
    '''

    def get(self, request):
        # next 表示从哪个页面进入到登陆页面，将来登陆成功后，就自动回到那个页面
        next = request.GET.get('next')
        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        # 获取QQ登陆页面网址,扫码链接
        login_url = oauth.get_qq_url()
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})
