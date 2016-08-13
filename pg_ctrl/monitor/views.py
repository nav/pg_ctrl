import os

from django.http import JsonResponse
from django.views import generic

import paramiko


def check_connection(host, username):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=username, key_filename='{}/.ssh/pg_ctrl.id_rsa'.format(os.getenv('HOME')))
    except Exception as e:
        return dict(status='error', message=str(e))
    else:
        stdin, stdout, stderr = ssh.exec_command("whoami")
        response = stdout.read()
        if username.strip() == response.strip():
            return dict(status='ok', message="connection ok")

    return dict(status='error', message="unknown error")


class JSONResponseMixin(object):
    def render_to_json_response(self, context, **response_kwargs):
        return JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        del context['view']
        return context


class CheckConnectionView(JSONResponseMixin, generic.TemplateView):
    def get_context_data(self, **kwargs):
        context = super(CheckConnectionView, self).get_context_data(**kwargs)
        host = self.request.GET.get('host')
        username = self.request.GET.get('username')
        context['response'] = check_connection(host, username)
        return context

    def render_to_response(self, context, **response_kwargs):
        status = 200
        if context['response']['status'] != 'ok':
            status = 400
        return self.render_to_json_response(context, status=status, **response_kwargs)
