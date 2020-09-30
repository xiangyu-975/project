import json, re

import logging
from django import http
from django.contrib.auth import login, authenticate, logout
from users.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
from django.urls import reverse
from django.views import View
from pymysql import DatabaseError
from django_redis import get_redis_connection
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredJSONMixin
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url, check_verify_email_token

# 创建日志器
logger = logging.getLogger('django')


class AddressView(LoginRequiredMixin, View):
    '''用户收货地址'''

    def get(self, request):
        return render(request, 'user_center_site.html')


class VerifyEmailView(View):
    '''验证邮箱'''

    def get(self, request):
        # 接收参数
        token = request.GET.get('token')
        # 校验参数
        if not token:
            return http.HttpResponseForbidden('缺少token')
        # 从token中提取用户的信息 user_id  ==> user
        user = check_verify_email_token(token)
        if not user:
            return http.HttpResponseBadRequest('无效的token')
        # 将用户的email_active字段设置True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('激活邮箱失败')
        # 响应结果:重定向到拥护衷心
        return redirect(reverse(('users:info')))


class EmailView(LoginRequiredJSONMixin, View):
    '''添加邮箱'''

    def put(self, request):
        # 接收参数
        json_str = request.body.decode()  # body 类型是bytes
        json_dict = json.loads(json_str)
        email = json_dict.get('email')
        # 校验参数
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')
        # 将用户传入的邮箱保存到用户数据库email字段中
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})
        # 发送邮箱验证邮件
        verify_url = generate_verify_email_url(request.user)
        # send_verify_email(email, verify_url)  错误写法
        send_verify_email.delay(email, verify_url)
        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class UserInfoView(LoginRequiredMixin, View):
    '''用户中心页面'''

    def get(self, request):
        # if request.user.is_authenticated():
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect(reverse('users:login'))
        # login_url = '/login/'
        # redirect_field_name = 'redirect_to'
        # 如果LoginRequiredMixin判断出用户已登陆，那么request.user就是登陆用户对象
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
        }
        return render(request, 'user_center_info.html', context)


class LogoutView(View):
    '''用户退出登陆'''

    def get(self, request):
        '''实现用户退出登陆的逻辑'''
        # 清除状态保持信息
        logout(request)
        # 退出登陆重定向到首页
        response = redirect(reverse('contents:index'))
        # 删除cookies中的用户名
        response.delete_cookie('username')
        # 响应结果
        return response


class LoginView(View):
    '''用户登陆'''

    def get(self, request):
        '''提供用户登陆页面'''
        return render(request, 'login.html')

    def post(self, request):
        '''实现用户登录逻辑'''
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')
        # 校验参数
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        # 认证用户:使用账号查询用户是否存在，如果用户存在，再去校验密码是否正确
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})
        # 状态保持
        login(request, user)
        # 使用remembered确定状态保持周期（实现记住登陆）
        if remembered != 'on':
            # 没有记住登陆：状态保持在浏览器回话结束后就销毁
            request.session.set_expiry(0)  # 单位是秒
        else:
            # 记住登陆：状态保持周期为两周
            request.session.set_expiry(None)
        # 响应结果
        # 先取出next
        next = request.GET.get('next')
        print(next)
        if next:
            response = redirect(next)
        else:
            # 重定向到首页
            response = redirect(reverse('contents:index'))
        # 为了实现在首页右上角展示用户名信息，我们需要将用户名缓存到cookie中
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        # 重定向到首页
        return response


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        # :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class UsernameCountView(View):
    '''判断用户名是否重复'''

    def get(self, request, username):
        '''
        :param request:请求对象
        :param username: 用户名
        :return: Json
        '''
        # 实现主体业务逻辑：使用username查询对应的记录条数（filter返回的是满足条件的结果集）
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        """

        :param request:
        :return:
        """
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code_client = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        # 判断参数是否齐全
        if not all([username, password, password2, mobile, sms_code_client, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 校验短信验证码
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
        if sms_code_server.decode() != sms_code_client:
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})
        # return render(request, 'register.html', {'register_errmsg': '注册失败'})
        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})
        # 登录用户 实现状态保持
        # TODO : redis疑问，redis2.10.6版本与低版本如4.2的kombu兼容，(celery的问题引出)与高版本不兼容（不知是不是这样）
        # TODO :然而login()模块与redis4.3版本不兼容，会报数据类型的错误，暂时没搞明白原因，redis2.10.6却没问题
        login(request, user)
        # 响应结果
        response = redirect(reverse('contents:index'))
        # 为了实现在首页右上角展示用户名信息，我们需要将用户名缓存到cookie中
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        # 相应结果
        # reverse('contents:index') == '/'
        # return http.HttpResponse('注册成功，重定向到首页')
        # return redirect('/')
        return response
