from django import forms
from django.contrib.sites.models import Site
from django.core import validators
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat as fs_format
from django.utils.translation import ugettext_lazy as _

from utils import DEFAULT_PROTOCOL
from utils.http import url_exists

class MaxFileSizeValidator(object):
    def __init__(self, max_size, message=_(u'Please keep file size under %(required_size)s. Current file size %(current_size)s')):
        self.max_size = max_size
        self.message = message

    def __call__(self, content):
        if content._size > self.max_size:
            params = dict(required_size=fs_format(self.max_size), current_size=fs_format(content._size))
            raise ValidationError(self.message % params)


class UniSubURLValidator(validators.URLValidator):
    def __init__(self, verify_exists=False, validator_user_agent=validators.URL_VALIDATOR_USER_AGENT):
        self._verify_exists = verify_exists

        super(UniSubURLValidator, self).__init__(verify_exists, validator_user_agent)

        # Never use Django's built-in verify_exists because it's broken on Python 2.6.
        self.verify_exists = False

    @property
    def host(self):
        return Site.objects.get_current().domain

    def __call__(self, value):
        super(UniSubURLValidator, self).__call__(value)

        if self._verify_exists and not value.startswith('%s://%s' %(DEFAULT_PROTOCOL, self.host)):
            if not url_exists(value):
                raise forms.ValidationError(_(u'This URL appears to be a broken link.'))
