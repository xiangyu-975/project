from django.conf.urls import url

from . import views

urlpatterns = [
    url('^carts/$', views.CartsView.as_view(), name='info')
]
