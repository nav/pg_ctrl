from django import forms
from django.core.urlresolvers import reverse_lazy
from monitor.views import check_connection
from .models import Host, Attribute, AttributeValue


def checkbox(placeholder, url):
    return forms.CheckboxInput(attrs=dict(placeholder=placeholder, url=url))


class ChecklistForm(forms.Form):
    hosts_created = forms.BooleanField(required=False,
                                       widget=checkbox(placeholder="Create hosts",
                                                       url=reverse_lazy("controller:create_host")),
                                       help_text="We need to add hosts that will be running the database server")
    keys_generated = forms.BooleanField(required=False,
                                        widget=checkbox(placeholder="How to generate key pair",
                                                        url="https://duckduckgo.com/?q=how+to+generate+public+and+private+keys&t=ha&ia=web"),
                                        help_text="You must generate a new public-private key pair and place "
                                                  "them in ~/.ssh folder as pg_ctrl.id_rsa and pg_ctrl.id_rsa.pub")
    public_key_installed = forms.BooleanField(required=False,
                                              widget=checkbox(placeholder="Check connection",
                                                              url=reverse_lazy("controller:create_host")),
                                              help_text="Public key must be placed on the hosts for this system "
                                                        "to be able to connect")
    checklist_completed = forms.BooleanField(required=False,
                                             widget=forms.HiddenInput())

    def save(self):
        for key, value in self.cleaned_data.items():
            if value:
                attr, _ = Attribute.objects.get_or_create(name=key)
                try:
                    AttributeValue.objects.get(attribute=attr)
                except AttributeValue.MultipleObjectsReturned:
                    AttributeValue.objects.filter(attribute=attr).delete()
                    AttributeValue.objects.create(attribute=attr, value=1)
                except AttributeValue.DoesNotExist:
                    AttributeValue.objects.create(attribute=attr, value=1)


class HostForm(forms.ModelForm):
    class Meta:
        model = Host
        fields = ('fqdn', 'ip_address', 'username', 'is_primary')

    def clean(self):
        cleaned_data = super(HostForm, self).clean()
        fqdn = cleaned_data.get('fqdn')
        ip_address = cleaned_data.get('ip_address')
        username = cleaned_data.get('username')
        connection_result = check_connection(ip_address, username)

        if connection_result['status'] != 'ok':
            raise forms.ValidationError(
                "Unable to connect to {} ({}) using {}".format(fqdn, ip_address, username))


class FailoverForm(forms.Form):
    host = forms.ModelChoiceField(queryset=Host.objects.filter(is_primary=False), required=True)


class StandbyForm(forms.Form):
    parent = forms.ModelChoiceField(queryset=Host.objects.all(), required=True)
    host = forms.ModelChoiceField(queryset=Host.objects.filter(is_primary=False), required=True)
