from . import views
from django.conf.urls import url

urlpatterns = [
    # 结算订单
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement'),
    # 提交订单
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),
    # 提交订单成功跳转界面
    url(r'^orders/success/$', views.OrderSuccessView.as_view(), name='info')
]
