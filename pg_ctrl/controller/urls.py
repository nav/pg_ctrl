from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^checklist/$', views.ChecklistView.as_view(), name='checklist'),
    url(r'^inventory/$', views.InventoryView.as_view(), name='inventory'),
    url(r'^playbook/$', views.PlaybookView.as_view(), name='playbook'),

    url(r'^hosts/create/$', views.CreateHostView.as_view(), name='create_host'),
]