from django.conf.urls import url

from . import views

urlpatterns = [
    # 首页 广告
    url(r'^$', views.IndexView.as_view(), name='index')
]