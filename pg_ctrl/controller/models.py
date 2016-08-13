from __future__ import unicode_literals

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import shortuuid


def generate_uuid():
    return shortuuid.ShortUUID().random(length=22)

class BaseUUID(models.Model):
    uuid = models.CharField(max_length=22, unique=True, db_index=True, default=generate_uuid)

    class Meta:
        abstract = True


class Attribute(models.Model):
    name = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute)
    value = models.CharField(max_length=255, blank=True, default='', db_index=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()

    def __str__(self):
        return '{}: {}'.format(self.attribute_id, self.value)


class Host(BaseUUID):
    parent = models.ForeignKey('self', related_name='children', blank=True, null=True)
    fqdn = models.CharField(verbose_name="FQDN", max_length=255)
    ip_address = models.GenericIPAddressField(protocol='both', verbose_name="IP Address", unique=True)
    username = models.CharField(max_length=255)
    is_primary = models.BooleanField(verbose_name="primary server", default=False, help_text="Is this the primary database server?")

    def __str__(self):
        return self.fqdn

    def save(self, *args, **kwargs):
        create_default_status = False
        if not self.pk:
            create_default_status = True
        super(Host, self).save(*args, **kwargs)
        if create_default_status:
            HostStatus.objects.create(host=self)

class HostStatus(models.Model):
    BRAND_NEW = 0
    CONNECTED = 1
    DISCONNECTED = 2
    DEPLOYED = 3
    PROMOTED = 4
    SHOT = 5

    STATUS_CHOICES = ((BRAND_NEW, 'Brand new'),
                      (CONNECTED, 'Connected'),
                      (DISCONNECTED, 'Disconnected'),
                      (DEPLOYED, 'Deployed'),
                      (PROMOTED, 'Promoted'),
                      (SHOT, 'Shot'))

    datetime = models.DateTimeField(auto_now=True)
    host = models.ForeignKey(Host, related_name='statuses')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, blank=True, default=BRAND_NEW)

    class Meta:
        verbose_name = 'Host Status'
        verbose_name_plural = 'Host Statuses'

    def __str__(self):
        return '{} - {}'.format(self.host_id, self.get_status_display())