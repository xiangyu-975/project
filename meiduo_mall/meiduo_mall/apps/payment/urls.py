from django.conf.urls import url
from . import views

urlpatterns = [
    url('^payment/(?P<order_id>\d+)/$', views.PaymentView.as_view()),
    url('^payment/status/$', views.PaymentStatusView.as_view()),
]
