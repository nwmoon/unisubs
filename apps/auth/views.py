# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.
import base64
from urllib2 import URLError

import facebook.djangofb as facebook
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_backends, login as stock_login, authenticate,
    logout, login as auth_login
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from oauth import oauth

from auth.forms import CustomUserCreationForm, ChooseUserForm
from auth.models import (
    UserLanguage, EmailConfirmation, LoginToken
)
from auth.providers import get_authentication_provider
from socialauth.models import AuthMeta, OpenidProfile
from socialauth.views import get_url_host
from utils.translation import get_user_languages_from_cookie


def login(request):
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, '')
    return render_login(request, CustomUserCreationForm(label_suffix=""),
                        AuthenticationForm(label_suffix=""), redirect_to)

def confirm_email(request, confirmation_key):
    confirmation_key = confirmation_key.lower()
    user = EmailConfirmation.objects.confirm_email(confirmation_key)
    if not user:
        messages.error(request, _(u'Confirmation key expired.'))
    else:
        messages.success(request, _(u'Email is confirmed.'))

    if request.user.is_authenticated():
        return redirect('profiles:dashboard')

    return redirect('/')

@login_required
def resend_confirmation_email(request):
    user = request.user
    if user.email and not user.valid_email:
        EmailConfirmation.objects.send_confirmation(user)
        messages.success(request, _(u'Confirmation email was sent.'))
    else:
        messages.error(request, _(u'You email is empty or already confirmed.'))
    return redirect(request.META.get('HTTP_REFERER') or request.user)

def create_user(request):
    redirect_to = make_redirect_to(request)
    form = CustomUserCreationForm(request.POST, label_suffix="")
    if form.is_valid():
        new_user = form.save()
        user = authenticate(username=new_user.username,
                            password=form.cleaned_data['password1'])
        langs = get_user_languages_from_cookie(request)
        for l in langs:
            UserLanguage.objects.get_or_create(user=user, language=l)
        auth_login(request, user)
        return HttpResponseRedirect(redirect_to)
    else:
        return render_login(request, form, AuthenticationForm(label_suffix=""), redirect_to)

@login_required
def delete_user(request):
    if request.POST.get('delete'):
        user = request.user

        AuthMeta.objects.filter(user=user).delete()
        OpenidProfile.objects.filter(user=user).delete()
        # TODO: TPA?

        user.team_members.all().delete()

        user.is_active = False
        user.save()
        logout(request)
        messages.success(request, _(u'Your account was deleted.'))
        return HttpResponseRedirect('/')
    return render(request, 'auth/delete_user.html')

def login_post(request):
    redirect_to = make_redirect_to(request)
    form = AuthenticationForm(data=request.POST, label_suffix="")
    try:
        if form.is_valid():
            auth_login(request, form.get_user())
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponseRedirect(redirect_to)
        else:
            return render_login(request, CustomUserCreationForm(label_suffix=""), form, redirect_to)
    except ValueError:
            return render_login(request, CustomUserCreationForm(label_suffix=""), form, redirect_to)


def token_login(request, token):
    """
    Automagically logs a user in from a secret token.
    Will only work for the CustomUser backend, and will not
    let staff or admin users login.
    Receives a '?next=' parameter of where to redirect the user into
    If the token has expired or is not found, a 403 is returned.
    """
    # we return 403 even from not found tokens, just being a bit more
    # strict about not leaking valid tokens
    try:
        lt = LoginToken.objects.get(token=token)
        user = lt.user
        # be paranoid, these users should never be login / staff members
        if  (user.is_staff is False ) and (user.is_superuser is False):
            # this will only work if user has the CustoUser backend
            # not a third party provider
            backend = get_backends()[0]
            user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
            stock_login(request, user)
            next_url = make_redirect_to(request, reverse("profiles:edit"))
            return HttpResponseRedirect(next_url)

    except LoginToken.DoesNotExist:
        pass
    return HttpResponseForbidden("Invalid user token")


@user_passes_test(lambda u: u.is_superuser)
def login_trap(request):
    if request.method == 'POST':
        form = ChooseUserForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['username']
            user.backend = getattr(settings, 'AUTHENTICATION_BACKENDS')[0]
            auth_login(request, user)
            return redirect('/')
    else:
        form = ChooseUserForm()
    return render_to_response('auth/login_trap.html', {
        'form': form
    }, context_instance=RequestContext(request))


# Helpers

def render_login(request, user_creation_form, login_form, redirect_to):
    redirect_to = redirect_to or '/'
    ted_auth = get_authentication_provider('ted')
    stanford_auth = get_authentication_provider('stanford')
    return render_to_response(
        'auth/login.html', {
            'creation_form': user_creation_form,
            'login_form' : login_form,
            'ted_auth': ted_auth,
            'stanford_auth': stanford_auth,
            REDIRECT_FIELD_NAME: redirect_to,
            }, context_instance=RequestContext(request))

def make_redirect_to(request, default=''):
    """Get the URL to redirect to after logging a user in.

    This method has a simply check against open redirects to prevent attackers
    from putting their sites into the next GET param (see 1253)
    """
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, default)
    if not redirect_to or '//' in redirect_to:
        return '/'
    else:
        return redirect_to
