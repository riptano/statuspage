from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import Authorization
from tastypie.resources import NamespacedModelResource, fields, ALL, ALL_WITH_RELATIONS
from django.contrib.auth.models import User #BUG: Import the correct user object from settings.py

from .models import Incident, IncidentUpdate, Status

import logging
logger = logging.getLogger(__name__)


class ReadOnlyFieldNamespacedModelResource(NamespacedModelResource):
    """ Allows you to add a 'readonly_fields' setting on a ModelResource """
    def __init__(self, **kwargs):
        super(ReadOnlyFieldNamespacedModelResource, self).__init__(**kwargs)
        for fld in getattr(self.Meta, 'readonly_fields', []):
            self.fields[fld].readonly = True


class StatusResource(ReadOnlyFieldNamespacedModelResource):
    class Meta:
        detail_uri_name = 'name'
        queryset = Status.objects.all()
        allowed_methods = ['get']
        resource_name = 'status'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()


class IncidentResource(ReadOnlyFieldNamespacedModelResource):
    updates = fields.ToManyField('status.api.IncidentUpdateResource', 'incidentupdate_set', full=True, null=True, blank=True, related_name='incident')

    def dehydrate(self, bundle):
        bundle.data['user'] = bundle.obj.user.username
        last_update = bundle.obj.get_latest_update()
        if last_update:
            bundle.data['status'] = last_update.status.name
        else:
            bundle.data['status'] = None
        return bundle

    def hydrate(self, bundle):
        u = User.objects.get(id=bundle.request.user.id)
        bundle.obj.user = u

        return bundle

    class Meta:
        readonly_fields = ['created', 'updated']
        queryset = Incident.objects.all()
        allowed_methods = ['get', 'post', 'delete']
        resource_name = 'incident'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
        filtering = {
            'created': ALL,
            'updates': ALL_WITH_RELATIONS,
            'status': ALL_WITH_RELATIONS,
            'updated': ALL,
        }


class IncidentUpdateResource(NamespacedModelResource):
    status = fields.ForeignKey(StatusResource, 'status', full=True)
    incident = fields.ForeignKey(IncidentResource, 'incident', null=True, blank=True, related_name='updates')

    def hydrate(self, bundle):
        # Force API to not blank out created field
        if 'id' in bundle.data:
            bundle.data['created'] = IncidentUpdate.objects.get(id=bundle.data['id']).created

        u = User.objects.get(id=bundle.request.user.id)
        bundle.obj.user = u

        return bundle

    class Meta:
        queryset = IncidentUpdate.objects.all()
        allowed_methods = ['get', 'post', 'delete']
        resource_name = 'incidentupdate'
        authentication = ApiKeyAuthentication()
        authorization = Authorization()
        always_return_data = True
        filtering = {
            'created': ALL,
            'updated': ALL,
            'status': ALL_WITH_RELATIONS,
            'incident': ALL_WITH_RELATIONS,
        }
