from django import http
from django.core.urlresolvers import reverse
from controller.models import AttributeValue


def checklist_middleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):

        if request.path != "/controller/checklist/":
            if not AttributeValue.objects.select_related('attribute__name')\
                    .only('pk').filter(attribute__name='checklist_completed').exists():
                return http.HttpResponseRedirect(reverse('controller:checklist'))

        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware