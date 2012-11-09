# Amara, universalsubtitles.org
#
# Copyright (C) 2012 Participatory Culture Foundation
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
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils import simplejson as json
from django.utils.translation import ugettext_lazy as _, ugettext
from django.views.generic.list_detail import object_list
from django.views.generic.simple import direct_to_template
from tastypie.models import ApiKey

from auth.models import CustomUser as User
from profiles.forms import EditUserForm, SendMessageForm, UserLanguageFormset, EditAvatarForm
from profiles.rpc import ProfileApiClass
from utils.amazon import S3StorageError
from utils.orm import LoadRelatedQuerySet
from utils.rpc import RpcRouter
from videos.models import Action, SubtitleLanguage, VideoUrl


rpc_router = RpcRouter('profiles:rpc_router', {
    'ProfileApi': ProfileApiClass()
})

VIDEOS_ON_PAGE = getattr(settings, 'VIDEOS_ON_PAGE', 30)


class OptimizedQuerySet(LoadRelatedQuerySet):

    def update_result_cache(self):
        videos = dict((v.id, v) for v in self._result_cache if not hasattr(v, 'langs_cache'))

        if videos:
            for v in videos.values():
                v.langs_cache = []

            langs_qs = SubtitleLanguage.objects.select_related('video').filter(video__id__in=videos.keys())

            for l in langs_qs:
                videos[l.video_id].langs_cache.append(l)


def activity(request, user_id=None):

    if user_id:
        try:
            user = User.objects.get(username=user_id)
        except User.DoesNotExist:
            try:
                user = User.objects.get(id=user_id)
            except (User.DoesNotExist, ValueError):
                raise Http404
    else:
        user = request.user

    qs = Action.objects.filter(user=user)

    extra_context = {
        'user_info': user,
        'can_edit': user == request.user
    }

    return object_list(request, queryset=qs, allow_empty=True,
                       paginate_by=settings.ACTIVITIES_ONPAGE,
                       template_name='profiles/view.html',
                       template_object_name='action',
                       extra_context=extra_context)

@login_required
def dashboard(request):
    user = request.user

    tasks = user.open_tasks()

    widget_settings = {}
    from apps.widget.rpc import add_general_settings
    add_general_settings(request, widget_settings)

    # For perform links on tasks
    video_pks = [t.team_video.video_id for t in tasks]
    video_urls = dict([(vu.video_id, vu.effective_url) for vu in
                       VideoUrl.objects.filter(video__in=video_pks, primary=True)])

    for t in tasks:
        t.cached_video_url = video_urls.get(t.team_video.video_id)

    context = {
        'user_info': user,
        'team_activity': Action.objects.for_user_team_activity(user)[:10],
        'video_activity': Action.objects.for_user_video_activity(user)[:10],
        'tasks': tasks,
        'widget_settings': widget_settings,
    }

    return direct_to_template(request, 'profiles/dashboard.html', context)


@login_required
def videos(request):
    user = request.user
    qs = user.videos.order_by('-edited')
    q = request.REQUEST.get('q')

    if q:
        qs = qs.filter(Q(title__icontains=q)|Q(description__icontains=q))
    context = {
        'user_info': user,
        'my_videos': True,
        'query': q
    }
    qs = qs._clone(OptimizedQuerySet)

    return object_list(request, queryset=qs,
                       paginate_by=VIDEOS_ON_PAGE,
                       template_name='profiles/videos.html',
                       extra_context=context,
                       template_object_name='user_video')

@login_required
def edit(request):
    if request.method == 'POST':
        form = EditUserForm(request.POST,
                            instance=request.user,
                            files=request.FILES, label_suffix="")
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated.'))
    else:
        form = EditUserForm(instance=request.user, label_suffix="")

    context = {
        'form': form,
        'user_info': request.user,
        'edit_profile_page': True
    }
    return direct_to_template(request, 'profiles/edit.html', context)

@login_required
def account(request):
    if request.method == 'POST':
        form = EditUserForm(request.POST,
                            instance=request.user,
                            files=request.FILES, label_suffix="")
        if form.is_valid():
            form.save()
            messages.success(request, _('Your account has been updated.'))

    else:
        form = EditUserForm(instance=request.user, label_suffix="")

    context = {
        'form': form,
        'user_info': request.user,
        'edit_profile_page': True
    }

    return direct_to_template(request, 'profiles/account.html', context)

@login_required
def send_message(request):
    output = dict(success=False)
    form = SendMessageForm(request.user, request.POST)
    if form.is_valid():
        form.send()
        output['success'] = True
    else:
        output['errors'] = form.get_errors()
    return HttpResponse(json.dumps(output), "text/javascript")

@login_required
def generate_api_key(request):
    key, created = ApiKey.objects.get_or_create(user=request.user)
    if not created:
        key.key = key.generate_key()
        key.save()
    return HttpResponse(json.dumps({"key":key.key}))

@login_required
def edit_avatar(request):
    form = EditAvatarForm(request.POST, instance=request.user, files=request.FILES)
    if form.is_valid():
        form.save()
    else:
        messages.error(request, _(form.errors['picture']))
    return HttpResponseRedirect('/profiles/profile/' + request.user.username + '/')

@login_required
def remove_avatar(request):
    if request.POST.get('remove'):
        request.user.picture = ''
        request.user.save()
        messages.success(request, _('Your picture has been removed.'))
    return HttpResponseRedirect('/profiles/profile/' + request.user.username + '/')