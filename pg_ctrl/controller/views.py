import os
import subprocess

import sys
from django import http
from django.conf import settings
from django.views import generic
from django.template import loader
from django.core.urlresolvers import reverse
from .models import Host, AttributeValue
from .forms import HostForm, ChecklistForm, FailoverForm, StandbyForm


class ChecklistView(generic.FormView):
    template_name = 'controller/checklist_form.html'
    form_class = ChecklistForm

    def get(self, request, *args, **kwargs):
        checklist_completed = AttributeValue.objects.filter(attribute__name='checklist_completed',
                                                            value='1')
        if checklist_completed.exists():
            return http.HttpResponseRedirect(reverse('controller:inventory'))
        return super(ChecklistView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ChecklistView, self).get_context_data(**kwargs)
        context['hosts'] = Host.objects.all()
        return context

    def get_form_kwargs(self):
        kwargs = super(ChecklistView, self).get_form_kwargs()
        attr_values = AttributeValue.objects.filter(attribute__name__in=ChecklistForm.declared_fields.keys())
        kwargs['initial'] = dict([(av.attribute.name, av.value) for av in attr_values])
        return kwargs

    def form_valid(self, form):
        form.save()
        return http.HttpResponseRedirect(reverse('controller:checklist'))



class CreateHostView(generic.CreateView):
    template_name = 'controller/host_form.html'
    form_class = HostForm

    def get_success_url(self):
        return reverse('controller:create_host')

    def get_context_data(self, **kwargs):
        context = super(CreateHostView, self).get_context_data(**kwargs)
        context['hosts'] = Host.objects.all()
        return context


class DeleteHostView(generic.DeleteView):
    queryset = Host.objects.all()


def get_inventory_context():
    return dict(hosts=Host.objects.all(),
                private_key='{}/.ssh/pg_ctrl.id_rsa'.format(os.getenv('HOME')),
                python_executable=sys.executable)

class InventoryView(generic.TemplateView):
    template_name = 'controller/inventory_form.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryView, self).get_context_data(**kwargs)
        context.update(get_inventory_context())
        return context



class BasePlaybookView(generic.TemplateView):
    template_name = 'controller/playbook.html'
    lock_path = os.path.join(settings.BASE_DIR, 'ansible.lock')
    inventory_path = os.path.join(settings.BASE_DIR, 'inventory')
    locked_message = 'There is a existing process. Wait for it to finish first.'

    def acquire_lock(self):
        open(self.lock_path, 'w').close()

    def release_lock(self):
        os.remove(self.lock_path)

    def is_locked(self):
        return os.path.exists(os.path.join(self.lock_path))

    def get_context_data(self, **kwargs):
        context = super(BasePlaybookView, self).get_context_data(**kwargs)
        context.update(get_inventory_context())
        return context

    def write_inventory(self):
        with open(self.inventory_path, 'w') as fsock:
            template = loader.get_template('controller/inventory.html')
            rendered = template.render(self.get_context_data())
            fsock.write(rendered)

    def run_playbook(self, cmd, callback=None, *args):
        self.acquire_lock()
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for line in iter(process.stdout.readline, ''):
            yield line.rstrip() + '<br/>\n'

        if callback is not None:
            yield callback(*args)

        self.release_lock()


class PlaybookInstallView(BasePlaybookView):

    def post(self, request, *args, **kwargs):
        if self.is_locked():
            return http.HttpResponse(self.locked_message, status=400)

        self.acquire_lock()
        self.write_inventory()

        cmd = "ANSIBLE_HOST_KEY_CHECKING=False " \
              "ansible-playbook -i inventory playbook.yml " \
              "-e 'host_key_checking=False' --skip-tags failover"
        return http.StreamingHttpResponse(streaming_content=self.run_playbook(cmd))


class PlaybookFailoverView(BasePlaybookView):
    def get_context_data(self, **kwargs):
        context = super(PlaybookFailoverView, self).get_context_data(**kwargs)
        context['form'] = FailoverForm()
        return context

    def post_failover(self, primary_host, standby_host):
        primary_host.is_primary = False
        primary_host.save()

        standby_host.is_primary = True
        standby_host.save()

        self.write_inventory()

    def post(self, request, *args, **kwargs):
        form = FailoverForm(request.POST)
        if not form.is_valid():
            return http.HttpResponseBadRequest()

        standby_host = form.cleaned_data.get('host')

        if self.is_locked():
            return http.HttpResponse(self.locked_message, status=400)

        primary_host = Host.objects.filter(is_primary=True).first()
        cmd = "ANSIBLE_HOST_KEY_CHECKING=False " \
              "ansible-playbook -i inventory playbook.yml " \
              "--limit {},{} --tags failover".format(primary_host.fqdn,
                                                     standby_host.fqdn)
        return http.StreamingHttpResponse(streaming_content=self.run_playbook(cmd,
                                                                              self.post_failover,
                                                                              primary_host,
                                                                              standby_host))


class PlaybookAddStandbyView(BasePlaybookView):
    def get_context_data(self, **kwargs):
        context = super(PlaybookAddStandbyView, self).get_context_data(**kwargs)
        context['form'] = StandbyForm()
        return context

    def post(self, request, *args, **kwargs):
        form = StandbyForm(request.POST)
        if not form.is_valid():
            return http.HttpResponseBadRequest()

        standby_host = form.cleaned_data.get('host')

        if self.is_locked():
            return http.HttpResponse(self.locked_message, status=400)

        cmd = "ANSIBLE_HOST_KEY_CHECKING=False " \
              "ansible-playbook -i inventory playbook.yml " \
              "--limit {} --tags standby".format(standby_host.fqdn)
        return http.StreamingHttpResponse(streaming_content=self.run_playbook(cmd))
