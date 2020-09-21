from django.conf.urls import url

from . import views

urlpatterns = [
    # 用户中心
    url(r'^$', views.IndexView.as_view(), name='index')
]