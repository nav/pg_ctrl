import os
import time
import subprocess
from cStringIO import StringIO

import sys
from django import http
from django.conf import settings
from django.views import generic
from django.template import loader
from django.core.urlresolvers import reverse
from .models import Host, AttributeValue
from .forms import HostForm, ChecklistForm


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


def get_inventory_contest():
    return dict(hosts=Host.objects.all(),
                private_key='{}/.ssh/pg_ctrl.id_rsa'.format(os.getenv('HOME')),
                python_executable=sys.executable)

class InventoryView(generic.TemplateView):
    template_name = 'controller/inventory_form.html'

    def get_context_data(self, **kwargs):
        context = super(InventoryView, self).get_context_data(**kwargs)
        context.update(get_inventory_contest())
        return context

class PlaybookView(generic.TemplateView):
    template_name = 'controller/playbook.html'
    lock_path = os.path.join(settings.BASE_DIR, 'ansible.lock')

    def generate_response(self):
        # Run the playbook
        cmd = "ANSIBLE_HOST_KEY_CHECKING=False " \
              "ansible-playbook -i inventory playbook.yml -e 'host_key_checking=False'"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)

        for line in iter(process.stdout.readline, ''):
            yield line.rstrip() + '<br/>\n'

        # Release the lock
        os.remove(self.lock_path)

    def get_context_data(self, **kwargs):
        context = super(PlaybookView, self).get_context_data(**kwargs)
        context.update(get_inventory_contest())
        return context

    def post(self, request, *args, **kwargs):
        # Check if lock exists
        if os.path.exists(os.path.join(settings.BASE_DIR, 'ansible.lock')):
            return http.HttpResponse('There is a existing process. Wait for it finish first.',
                                     status=400)

        # Acquire a lock
        open(self.lock_path, 'w').close()

        # Write the inventory file
        with open(os.path.join(settings.BASE_DIR, 'inventory'), 'w') as fsock:
            template = loader.get_template('controller/inventory.html')
            rendered = template.render(self.get_context_data())
            fsock.write(rendered)

        return http.StreamingHttpResponse(streaming_content=self.generate_response())
        # return http.HttpResponse(self.generate_response())




