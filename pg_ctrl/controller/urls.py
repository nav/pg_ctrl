from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^checklist/$', views.ChecklistView.as_view(), name='checklist'),
    url(r'^inventory/$', views.InventoryView.as_view(), name='inventory'),
    url(r'^playbook/install/$', views.PlaybookInstallView.as_view(), name='playbook_install'),
    url(r'^playbook/failover/$', views.PlaybookFailoverView.as_view(), name='playbook_failover'),
    url(r'^playbook/add_standby/$', views.PlaybookAddStandbyView.as_view(), name='playbook_add_standby'),

    url(r'^hosts/create/$', views.CreateHostView.as_view(), name='create_host'),
]