from django.contrib import admin

from .models import Host, HostStatus, Attribute, AttributeValue

admin.site.register(Host)
admin.site.register(HostStatus)
admin.site.register(Attribute)
admin.site.register(AttributeValue)