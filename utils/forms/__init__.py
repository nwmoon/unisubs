import re

from django import forms
from django.core import validators
from django.utils import html
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from utils.forms.recapcha import ReCaptchaField

assert ReCaptchaField # Shut up, Pyflakes.

class AjaxForm(object):
    def get_errors(self):
        output = {}
        for key, value in self.errors.items():
            output[key] = '/n'.join([force_unicode(i) for i in value])
        return output

class StripRegexField(forms.RegexField):
    def to_python(self, value):
        value = super(StripRegexField, self).to_python(value)
        return value.strip()

class UniSubURLField(forms.URLField):

    def to_python(self, value):
        value = super(UniSubURLField, self).to_python(value)
        return value.strip()

class FeedURLValidator(validators.URLValidator):
    regex = re.compile(
        r'^(?:(?:https?)|(?:feed))://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class FeedURLField(forms.URLField):
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        forms.CharField.__init__(self,max_length, min_length, *args,
                                       **kwargs)
        self.validators.append(FeedURLValidator())

    def to_python(self, value):
        value = super(FeedURLField, self).to_python(value)
        return value.strip()

class ListField(forms.RegexField):
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ListField, self).__init__(self.pattern, max_length, min_length, *args, **kwargs)

    def clean(self, value):
        if value:
            value = value and value.endswith(',') and value or value+','
            value = value.replace(' ', '')
        value = super(ListField, self).clean(value)
        return [item for item in value.strip(',').split(',') if item]

email_list_re = re.compile(
    r"""^(([-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*")@(?:[A-Z0-9]+(?:-*[A-Z0-9]+)*\.)+[A-Z]{2,6},)+$""", re.IGNORECASE)

class EmailListField(ListField):
    default_error_messages = {
        'invalid': _(u'Enter valid e-mail addresses separated by commas.')
    }
    pattern = email_list_re

username_list_re = re.compile(r'^([A-Z0-9]+,)+$', re.IGNORECASE)

class UsernameListField(ListField):
    default_error_messages = {
        'invalid': _(u'Enter valid usernames separated by commas. Username can contain only a-z, A-Z and 0-9.')
    }
    pattern = username_list_re


class SubmitButtonWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        final_attrs = self.attrs.copy()
        if attrs is not None:
            final_attrs.update(attrs)
        label = final_attrs.pop('label', _('Submit'))
        final_attrs['name'] = name
        if value is None:
            final_attrs['value'] = '1'
        else:
            final_attrs['value'] = value
        attr_string = ' '.join("%s=%s" % (name, html.escape(value))
                               for name, value in final_attrs.items())
        return mark_safe('<button %s>%s</button>' % (attr_string, label))

class SubmitButtonField(forms.BooleanField):
    widget = SubmitButtonWidget

    def widget_attrs(self, widget):
        attrs = {}
        if isinstance(widget, SubmitButtonWidget):
            attrs['label'] = self.label
        return attrs

class ErrorableModelForm(forms.ModelForm):
    """This class simply adds a single method to the standard one: add_error.

    When performing validation in a clean() method you may want to add an error
    message to a single field, instead of to non_field_errors.  There's a lot of
    silly stuff you need to do to make that happen, so add_error() takes care of
    it for you.

    """
    def add_error(self, message, field_name=None, cleaned_data=None):
        """Add the given error message to the given field.

        If no field is given, a standard forms.ValidationError will be raised.

        If a field is given, the cleaned_data dictionary must also be given to
        keep Django happy.

        If a field is given an exception will NOT be raised, so it's up to you
        to stop processing if appropriate.

        """
        if not field_name:
            raise forms.ValidationError(message)

        if field_name not in self._errors:
            self._errors[field_name] = self.error_class()

        self._errors[field_name].append(message)

        try:
            del cleaned_data[field_name]
        except KeyError:
            pass


def flatten_errorlists(errorlists):
    '''Return a list of the errors (just the text) in any field.'''
    errors = []
    for field, errorlist in errorlists.items():
        label = '' if field == '__all__' else ('%s: ' % field)
        errors += ['%s%s' % (label, error) for error in errorlist]

    return errors
