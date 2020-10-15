from django.conf.urls import url

from . import views

urlpatterns = [
    # 提供QQ登陆扫码页面
    url(r'^qq/login/$', views.QQAuthURLView.as_view()),
    url(r'^oauth_callback/$', views.QQAuthUserView.as_view()),
]
