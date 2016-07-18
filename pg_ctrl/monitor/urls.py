from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^check_connection/$', views.CheckConnectionView.as_view(), name='check_connection'),
]