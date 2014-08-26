# -*- coding: utf-8 -*-
# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program.  If not, see http://www.gnu.org/licenses/agpl-3.0.html.

import simplejson as json

import babelsubs
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, Http404
from django.db.models import Count
from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import urlize, linebreaks, force_escape
from django.views.decorators.clickjacking import xframe_options_exempt

from subtitles import shims
from subtitles.models import SubtitleLanguage, SubtitleVersion
from subtitles.templatetags.new_subtitles_tags import visibility
from subtitles.forms import SubtitlesUploadForm
from teams.models import Task
from teams.permissions import can_add_version, can_assign_task
from utils.text import fmt
from videos.models import Video

def _version_data(version):
    '''
    Creates a dict with version info, suitable for encoding
    into json and bootstrapping the editor.
    '''
    return {
        'metadata': version.get_metadata(),
        'subtitles': version.get_subtitles().to_xml(),
        'title': version.title,
        'description': version.description,
    }

def _language_data(language, editing_version, translated_from_version,
                   base_language):
    '''
    Creates a dict with language info, suitable for encoding
    into json and bootstrapping the editor. Includes
    the version data for the version being edited and the
    original translation source, if any.
    '''
    versions_data = []

    versions = list(language.subtitleversion_set.full())
    for i, version in enumerate(versions):
        version_data = {
            'version_no':version.version_number,
            'visibility': visibility(version),
        }
        if editing_version == version:
            version_data.update(_version_data(version))
        elif translated_from_version == version:
            version_data.update(_version_data(version))
        elif (language.language_code == base_language and
              i == len(versions) - 1):
            version_data.update(_version_data(version))

        versions_data.append(version_data)


    subtitle_language = editing_version.subtitle_language if editing_version else ''

    return {
        'translatedFrom': translated_from_version and {
            'language_code': translated_from_version.subtitle_language.language_code,
            'version_number': translated_from_version.version_number,
        },
        'editingLanguage': language == subtitle_language,
        'language_code': language.language_code,
        'name': language.get_language_code_display(),
        'pk': language.pk,
        'numVersions': language.num_versions,
        'versions': versions_data,
        'subtitles_complete': language.subtitles_complete,
        'is_rtl': language.is_rtl(),
        'is_original': language.is_primary_audio_language()
    }

def regain_lock(request, video_id, language_code):
    video = get_object_or_404(Video, video_id=video_id)
    language = video.subtitle_language(language_code)

    if not language.can_writelock(request.browser_id):
        return HttpResponse(json.dumps({'ok': False}))

    language.writelock(request.user, request.browser_id, save=True)
    return HttpResponse(json.dumps({'ok': True}))

@login_required
@require_POST
def release_lock(request, video_id, language_code):
    video = get_object_or_404(Video, video_id=video_id)
    language = video.subtitle_language(language_code)

    if language.can_writelock(request.browser_id):
        language.release_writelock()

    return HttpResponse(json.dumps({'url': reverse('videos:video', args=(video_id,))}))

def assign_task_for_editor(video, language_code, user):
    team_video = video.get_team_video()
    if team_video is None:
        return None
    task_set = team_video.task_set.incomplete().filter(language=language_code)
    tasks = list(task_set[:1])
    if tasks:
        task = tasks[0]
        if task.assignee is None and can_assign_task(task, user):
            task.assignee = user
            task.set_expiration()
            task.save()

        if task.assignee != user:
            return fmt(_("Another user is currently performing "
                         "the %(task_type)s task for these subtitles"),
                       task_type=task.get_type_display())

def get_team_attributes_for_editor(video):
    team_video = video.get_team_video()
    if team_video:
        team = team_video.team
        return dict([('teamName', team.name), ('guidelines', dict(
            [(s.key_name.split('_', 1)[-1],
              linebreaks(urlize(force_escape(s.data))))
             for s in team.settings.guidelines()
             if s.data.strip()]))])
    else:
        return None

def get_task_for_editor(video, language_code):
    team_video = video.get_team_video()
    if team_video is None:
        return None
    task_set = team_video.task_set.incomplete().filter(language=language_code)
    # 2533: We can get 2 review tasks if we include translate/transcribe tasks
    # in the results.  This is because when we have a task id and the user
    # clicks endorse, we do the following:
    #    - save the subtitles
    #    - save the task, setting subtitle_version to the version that we just
    #    saved
    #
    # However, the task code creates a task on both of those steps.  I'm not
    # sure exactly what the old editor does to make this not happen, but it's
    # safest to just not send task_id in that case
    task_set = task_set.filter(type__in=(Task.TYPE_IDS['Review'],
                                         Task.TYPE_IDS['Approve']))
    # This assumes there is only 1 incomplete tasks at once, hopefully that's
    # a good enough assumption to hold until we dump tasks for the collae
    # model.
    tasks = list(task_set[:1])
    if tasks:
        return tasks[0]
    else:
        return None

def old_editor(request, video_id, language_code):
    video = get_object_or_404(Video, video_id=video_id)
    language = get_object_or_404(SubtitleLanguage, video=video,
                                 language_code=language_code)
    url_path = shims.get_widget_url(language,
                                    request.GET.get('mode'),
                                    request.GET.get('task_id'))
    return redirect("http://%s%s" % (request.get_host(), url_path))

@xframe_options_exempt
@login_required
def subtitle_editor(request, video_id, language_code):
    '''
    Renders the subtitle-editor page, with all data neeeded for the UI
    as a json object on the html document.
    If the language does not exist, it will create one and lock it.
    Also decides what source version should be shown initially (if
    it is a translation).
    '''
    # FIXME: permissions
    video = get_object_or_404(Video, video_id=video_id)

    if (video.primary_audio_language_code and 
        SubtitleVersion.objects.extant().filter(
            video=video, language_code=video.primary_audio_language_code)
        .exists()):
        base_language = video.primary_audio_language_code
    else:
        base_language = None

    try:
        editing_language = video.newsubtitlelanguage_set.get(language_code=language_code)
    except SubtitleLanguage.DoesNotExist:
        editing_language = SubtitleLanguage(video=video,language_code=language_code)

    if not editing_language.can_writelock(request.browser_id):
        messages.error(request, _("You can't edit this subtitle because it's locked"))
        return redirect(video)

    error_message = assign_task_for_editor(video, language_code, request.user)
    if error_message:
        messages.error(request, error_message)
        return redirect(video)
    task = get_task_for_editor(video, language_code)
    check_result = can_add_version(request.user, video, language_code)
    if not check_result:
        messages.error(request, check_result.message)
        return redirect(video)

    editing_language.writelock(request.user, request.browser_id, save=True)

    # if this language is a translation, show both
    editing_version = editing_language.get_tip(public=False)
    # we ignore forking because even if it *is* a fork, we still want to show
    # the user the rererence languages:
    translated_from_version = editing_language.\
        get_translation_source_version(ignore_forking=True)

    languages = video.newsubtitlelanguage_set.annotate(
        num_versions=Count('subtitleversion'))

    video_urls = []
    for v in video.get_video_urls():
        video_urls.append(v.url)


    editor_data = {
        'canSync': bool(request.GET.get('canSync', True)),
        'canAddAndRemove': bool(request.GET.get('canAddAndRemove', True)),
        # front end needs this to be able to set the correct
        # api headers for saving subs
        'authHeaders': {
            'x-api-username': request.user.username,
            'x-apikey': request.user.get_api_key()
        },
        'video': {
            'id': video.video_id,
            'title': video.title,
            'description': video.description,
            'primaryVideoURL': video.get_video_url(),
            'videoURLs': video_urls,
            'metadata': video.get_metadata(),
        },
        'editingVersion': {
            'languageCode': editing_language.language_code,
            'versionNumber': (editing_version.version_number
                              if editing_version else None),
        },
        'baseLanguage': base_language,
        'languages': [_language_data(lang, editing_version,
                                     translated_from_version, base_language)
                      for lang in languages],
        'languageCode': request.LANGUAGE_CODE,
        'oldEditorURL': reverse('subtitles:old-editor', kwargs={
            'video_id': video.video_id,
            'language_code': editing_language.language_code,
        }),
        'staticURL': settings.STATIC_URL,
    }

    if task:
        editor_data['task_id'] = task.id
        editor_data['savedNotes'] = task.body
        editor_data['task_needs_pane'] = task.get_type_display() in ('Review', 'Approve')
        editor_data['team_slug'] = task.team.slug
        editor_data['oldEditorURL'] += '?' + urlencode({
            'mode': Task.TYPE_NAMES[task.type].lower(),
            'task_id': task.id,
        })

    team_attributes = get_team_attributes_for_editor(video)
    if team_attributes:
        editor_data['teamAttributes'] = team_attributes

    return render_to_response("subtitles/subtitle-editor.html", {
        'video': video,
        'DEBUG': settings.DEBUG,
        'language': editing_language,
        'other_languages': languages,
        'version': editing_version,
        'translated_from_version': translated_from_version,
        'task': task,
        'editor_data': json.dumps(editor_data, indent=4),
        'upload_subtitles_form': SubtitlesUploadForm(request.user, video,
                                                     initial={'language_code': editing_language.language_code})
    }, context_instance=RequestContext(request))

def download(request, video_id, language_code, filename, format,
             version_number=None):

    video = get_object_or_404(Video, video_id=video_id)

    language = video.subtitle_language(language_code)
    if language is None:
        raise Http404()

    team_video = video.get_team_video()

    if team_video and not team_video.team.user_is_member(request.user):
        # Non-members can only see public versions
        version = language.version(public_only=True,
                                   version_number=version_number)
    else:
        version = language.version(public_only=False,
                                   version_number=version_number)

    if not version:
        raise Http404()
    if not format in babelsubs.get_available_formats():
        raise HttpResponseServerError("Format not found")

    subs_text = babelsubs.to(version.get_subtitles(), format,
                             language=version.language_code)
    # since this is a downlaod, we can afford not to escape tags, specially
    # true since speaker change is denoted by '>>' and that would get entirely
    # stripped out
    response = HttpResponse(subs_text, mimetype="text/plain")
    response['Content-Disposition'] = 'attachment'
    return response


def download_all(request, video_id, filename):
    video = get_object_or_404(Video, video_id=video_id)
    merged_dfxp = video.get_merged_dfxp()

    if merged_dfxp is None:
        raise Http404()

    response = HttpResponse(merged_dfxp, mimetype="text/plain")
    response['Content-Disposition'] = 'attachment'
    return response
