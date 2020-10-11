from . import views
from django.conf.urls import url

urlpatterns = [
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement')
]
