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
import datetime
import re

from auth.models import CustomUser as User
from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from subtitles.forms import SubtitlesUploadForm
from teams.models import (
    Team, TeamMember, TeamVideo, Task, Project, Workflow, Invite, BillingReport
)
from teams.permissions import (
    roles_user_can_invite, can_delete_task, can_add_video, can_perform_task,
    can_assign_task, can_delete_language, can_remove_video,
    can_add_video_somewhere
)
from teams.permissions_const import ROLE_NAMES
from teams.workflows import TeamWorkflow
from videos.forms import (AddFromFeedForm, language_choices_with_empty,
                               CreateSubtitlesForm,
                               MultiVideoCreateSubtitlesForm)
from videos.models import (
        VideoMetadata, VIDEO_META_TYPE_IDS, Video, VideoFeed,
)
from videos.search_indexes import VideoIndex
from videos.tasks import import_videos_from_feed
from utils.forms import ErrorableModelForm
from utils.forms.unisub_video_form import UniSubBoundVideoField
from utils.translation import get_language_choices
from utils.text import fmt
from utils.validators import MaxFileSizeValidator

class EditTeamVideoForm(forms.ModelForm):
    author = forms.CharField(max_length=255, required=False)
    creation_date = forms.DateField(required=False, input_formats=['%Y-%m-%d'],
                                    help_text="Format: YYYY-MM-DD")

    project = forms.ModelChoiceField(
        label=_(u'Project'),
        queryset = Project.objects.none(),
        required=True,
        empty_label=None,
        help_text=_(u"Let's keep things tidy, shall we?")
    )

    class Meta:
        model = TeamVideo
        fields = ('description', 'thumbnail', 'project',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")

        super(EditTeamVideoForm, self).__init__(*args, **kwargs)

        self.fields['project'].queryset = self.instance.team.project_set.all()

    def clean(self, *args, **kwargs):
        super(EditTeamVideoForm, self).clean(*args, **kwargs)

        return self.cleaned_data

    def save(self, *args, **kwargs):
        obj = super(EditTeamVideoForm, self).save(*args, **kwargs)

        video = obj.video

        author = self.cleaned_data['author'].strip()
        creation_date = VideoMetadata.date_to_string(self.cleaned_data['creation_date'])

        self._save_metadata(video, 'Author', author)
        self._save_metadata(video, 'Creation Date', creation_date)
        # store the uploaded thumb on the video itself
        # TODO: simply remove the teamvideo.thumbnail image
        if obj.thumbnail:
            content = ContentFile(obj.thumbnail.read())
            name = obj.thumbnail.url.split('/')[-1]
            video.s3_thumbnail.save(name, content)
            VideoIndex(Video).update_object(video)

    def _save_metadata(self, video, meta, data):
        '''Save a single piece of metadata for the given video.

        The metadata is only saved if necessary (i.e. it's not blank OR it's blank
        but there's already other data that needs to be overwritten).

        '''
        meta_type_id = VIDEO_META_TYPE_IDS[meta]

        try:
            meta = VideoMetadata.objects.get(video=video, key=meta_type_id)
            meta.data = data
            meta.save()
        except VideoMetadata.DoesNotExist:
            if data:
                VideoMetadata(video=video, key=meta_type_id, data=data).save()

class MoveTeamVideoForm(forms.Form):
    team_video = forms.ModelChoiceField(queryset=TeamVideo.objects.all(),
                                        required=True)
    team = forms.ModelChoiceField(queryset=Team.objects.all(),
                                  required=True)

    project = forms.ModelChoiceField(queryset=Project.objects.all(),
                                     required=False)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(MoveTeamVideoForm, self).__init__(*args, **kwargs)

    def clean(self):
        team_video = self.cleaned_data.get('team_video')
        team = self.cleaned_data.get('team')
        project = self.cleaned_data.get('project')

        if not team_video or not team:
            return

        if project and project.team != team:
            raise forms.ValidationError(u"That project does not belong to that team.")

        if team_video.team.pk == team.pk:
            raise forms.ValidationError(u"That video is already in that team.")

        if not can_add_video(team, self.user):
            raise forms.ValidationError(u"You can't add videos to that team.")

        if not can_remove_video(team_video, self.user):
            raise forms.ValidationError(u"You can't remove that video from its team.")

        return self.cleaned_data

class BaseVideoBoundForm(forms.ModelForm):
    video_url = UniSubBoundVideoField(label=_('Video URL'),
        help_text=_("Enter the URL of any compatible video or any video on our site. You can also browse the site and use the 'Add Video to Team' menu."))

    def __init__(self, *args, **kwargs):
        super(BaseVideoBoundForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'user'):
            self.fields['video_url'].user = self.user

class AddVideoToTeamForm(forms.Form):
    """Used to add a non-team video to one of the user's managed teams."""

    team = forms.ChoiceField()

    def __init__(self, user, data=None, **kwargs):
        super(AddVideoToTeamForm, self).__init__(data, **kwargs)
        team_qs = (Team.objects
                   .filter(users=user)
                   .prefetch_related('project_set'))
        self.fields['team'].choices = [
            (team.id, unicode(team)) for team in team_qs
            if can_add_video_somewhere(team, user)
        ]

class AddTeamVideoForm(BaseVideoBoundForm):
    language = forms.ChoiceField(label=_(u'Video language'), choices=(),
                                 required=False,
                                 help_text=_(u'It will be saved only if video does not exist in our database.'))

    project = forms.ModelChoiceField(
        label=_(u'Project'),
        queryset = Project.objects.none(),
        required=True,
        empty_label=None,
        help_text=_(u"Let's keep things tidy, shall we?")
    )

    class Meta:
        model = TeamVideo
        fields = ('video_url', 'language', 'description', 'thumbnail', 'project',)

    def __init__(self, team, user, *args, **kwargs):
        self.team = team
        self.user = user
        super(AddTeamVideoForm, self).__init__(*args, **kwargs)


        projects = self.team.project_set.all()

        if len(projects) > 1:
            projects = projects.exclude(slug='_root')

        self.fields['project'].queryset = projects

        ordered_projects = ([p for p in projects if p.is_default_project] +
                            [p for p in projects if not p.is_default_project])
        ordered_projects = [p for p in ordered_projects if can_add_video(team, user, p)]

        self.fields['project'].choices = [(p.pk, p) for p in ordered_projects]

        writable_langs = team.get_writable_langs()
        self.fields['language'].choices = [c for c in get_language_choices(True)
                                           if c[0] in writable_langs]

    def clean_video_url(self):
        video_url = self.cleaned_data['video_url']
        video = self.fields['video_url'].video
        try:
            tv = TeamVideo.objects.get(team=self.team, video=video)
            raise forms.ValidationError(mark_safe(u'Team has this <a href="%s">video</a>' % tv.get_absolute_url()))
        except TeamVideo.DoesNotExist:
            pass

        return video_url

    def clean(self):
        language = self.cleaned_data.get('language')
        video = self.fields['video_url'].video

        if video:
            team_video = video.get_team_video()
            if team_video and not team_video.team.deleted:
                team = team_video.team
                if team.user_can_view_videos(self.user):
                    link = '<a href="{}">{}</a>'.format(
                            team_video.team.get_absolute_url(),
                            team_video.team.name)
                    msg = mark_safe(
                        fmt(_(u'This video already belongs to the '
                              '%(team_link)s team.'),
                            team_link=link))
                else:
                    msg = _(u'This video already belongs to a team.')
                self._errors['video_url'] = self.error_class([msg])

            original_sl = video.subtitle_language()

            if (original_sl and not original_sl.language_code) and not language:
                msg = _(u'Set original language for this video.')
                self._errors['language'] = self.error_class([msg])

        return self.cleaned_data

    def success_message(self):
        return 'Video successfully added to team.'

    def save(self, commit=True):
        video = self.fields['video_url'].video

        obj = super(AddTeamVideoForm, self).save(False)

        obj.video = video
        obj.team = self.team
        commit and obj.save()
        return obj

class AddTeamVideosFromFeedForm(AddFromFeedForm):
    VIDEOS_LIMIT = None

    def __init__(self, team, user, *args, **kwargs):
        if not can_add_video(team, user):
            raise ValueError("%s can't add videos to %s" % (user, team))
        self.team = team
        super(AddTeamVideosFromFeedForm, self).__init__(user, *args, **kwargs)

    def make_feed(self, url):
        return VideoFeed.objects.create(team=self.team, user=self.user,
                                        url=url)

class CreateTeamForm(BaseVideoBoundForm):
    logo = forms.ImageField(validators=[MaxFileSizeValidator(settings.AVATAR_MAX_SIZE)], required=False)
    workflow_type = forms.ChoiceField(choices=(), initial="O")

    class Meta:
        model = Team
        fields = ('name', 'slug', 'description', 'logo', 'workflow_type',
                  'is_visible', 'video_url')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(CreateTeamForm, self).__init__(*args, **kwargs)
        self.fields['workflow_type'].choices = TeamWorkflow.get_choices()
        self.fields['video_url'].label = _(u'Team intro video URL')
        self.fields['video_url'].required = False
        self.fields['video_url'].help_text = _(u'''You can put an optional video
on your team homepage that explains what your team is about, to attract volunteers.
Enter a link to any compatible video, or to any video page on our site.''')
        self.fields['is_visible'].widget.attrs['class'] = 'checkbox'
        self.fields['slug'].label = _(u'Team URL: http://universalsubtitles.org/teams/')

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if re.match('^\d+$', slug):
            raise forms.ValidationError('Field can\'t contains only numbers')
        return slug

    def save(self, user):
        team = super(CreateTeamForm, self).save(False)
        video = self.fields['video_url'].video
        if video:
            team.video = video
        team.save()
        TeamMember.objects.create_first_member(team=team, user=user)
        return team

class TaskCreateForm(ErrorableModelForm):
    choices = [(10, 'Transcribe'), Task.TYPE_CHOICES[1]]
    type = forms.TypedChoiceField(choices=choices, coerce=int)
    language = forms.ChoiceField(choices=(), required=False)
    assignee = forms.ModelChoiceField(queryset=User.objects.none(), required=False)

    def __init__(self, user, team, team_video, *args, **kwargs):
        self.non_display_form = False
        if kwargs.get('non_display_form'):
            self.non_display_form = kwargs.pop('non_display_form')
        super(TaskCreateForm, self).__init__(*args, **kwargs)

        self.user = user
        self.team_video = team_video

        # TODO: This is bad for teams with 10k members.
        team_user_ids = team.members.values_list('user', flat=True)

        langs = [l for l in get_language_choices(with_empty=True)
                 if l[0] in team.get_writable_langs()]
        self.fields['language'].choices = langs
        self.fields['assignee'].queryset = User.objects.filter(pk__in=team_user_ids)

        if self.non_display_form:
            self.fields['type'].choices = Task.TYPE_CHOICES

    def _check_task_creation_subtitle(self, tasks, cleaned_data):
        if self.team_video.subtitles_finished():
            self.add_error(_(u"This video has already been transcribed."),
                           'type', cleaned_data)
            return

    def _check_task_creation_translate(self, tasks, cleaned_data):
        if not self.team_video.subtitles_finished():
            self.add_error(_(u"No one has transcribed this video yet, so it can't be translated."),
                           'type', cleaned_data)
            return

        sl = self.team_video.video.subtitle_language(cleaned_data['language'])

        if sl and sl.is_complete_and_synced():
            self.add_error(_(u"This language already has a complete set of subtitles."),
                           'language', cleaned_data)

    def _check_task_creation_review_approve(self, tasks, cleaned_data):
        if not self.non_display_form:
            return

        lang = cleaned_data['language']
        video = self.team_video.video
        subtitle_language = video.subtitle_language(lang)

        if not subtitle_language or not subtitle_language.get_tip():
            self.add_error(_(
                u"This language for this video does not exist or doesn't have a version."
            ), 'language', cleaned_data)

    def clean(self):
        cd = self.cleaned_data

        type = cd['type']
        lang = cd['language']

        team_video = self.team_video
        project, team = team_video.project, team_video.team

        # TODO: Manager method?
        existing_tasks = list(Task.objects.filter(deleted=False, language=lang,
                                                  team_video=team_video))

        if any(not t.completed for t in existing_tasks):
            self.add_error(_(u"There is already a task in progress for that video/language."))

        type_name = Task.TYPE_NAMES[type]

        # TODO: Move into _check_task_creation_translate()?
        if type_name != 'Subtitle' and not lang:
            self.add_error(fmt(_(u"You must select a language for a "
                                 "%(task_type)s task."),
                               task_type=type_name))

        {'Subtitle': self._check_task_creation_subtitle,
         'Translate': self._check_task_creation_translate,
         'Review': self._check_task_creation_review_approve,
         'Approve': self._check_task_creation_review_approve
        }[type_name](existing_tasks, cd)

        return cd


    class Meta:
        model = Task
        fields = ('type', 'language', 'assignee')

class TaskAssignForm(forms.Form):
    task = forms.ModelChoiceField(queryset=Task.objects.none())
    assignee = forms.ModelChoiceField(queryset=User.objects.none(), required=False)

    def __init__(self, team, user, *args, **kwargs):
        super(TaskAssignForm, self).__init__(*args, **kwargs)

        self.team = team
        self.user = user
        self.fields['assignee'].queryset = User.objects.filter(team_members__team=team)
        self.fields['task'].queryset = team.task_set.incomplete()


    def clean_assignee(self):
        assignee = self.cleaned_data['assignee']

        if assignee:
            member = self.team.members.get(user=assignee)
            if member.has_max_tasks():
                raise forms.ValidationError(_(
                    u'That user has already been assigned the maximum number of tasks.'))

        return assignee

    def clean(self):
        task = self.cleaned_data['task']
        assignee = self.cleaned_data.get('assignee', -1)

        if assignee != -1:
            # There are a bunch of edge cases here that we need to check.
            unassigning_from_self      = (not assignee) and task.assignee and task.assignee.id == self.user.id
            assigning_to_self          = assignee and self.user.id == assignee.id
            can_assign_to_other_people = can_assign_task(task, self.user)

            # Users can always unassign a task from themselves.
            if not unassigning_from_self:
                # They can also assign a task TO themselves, assuming they can
                # perform it (which is checked further down).
                if not assigning_to_self:
                    # Otherwise they must have assign permissions in the team.
                    if not can_assign_to_other_people:
                        raise forms.ValidationError(_(
                            u'You do not have permission to assign this task.'))

            if assignee is None:
                return self.cleaned_data
            else:
                if not can_perform_task(assignee, task):
                    raise forms.ValidationError(_(
                        u'This user cannot perform that task.'))

        return self.cleaned_data

class TaskDeleteForm(forms.Form):
    task = forms.ModelChoiceField(queryset=Task.objects.all())
    discard_subs = forms.BooleanField(required=False)

    def __init__(self, team, user, *args, **kwargs):
        super(TaskDeleteForm, self).__init__(*args, **kwargs)

        self.user = user

        self.fields['task'].queryset = team.task_set.incomplete()


    def clean_task(self):
        task = self.cleaned_data['task']

        if not can_delete_task(task, self.user):
            raise forms.ValidationError(_(
                u'You do not have permission to delete this task.'))

        return task

class MessageTextField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(MessageTextField, self).__init__(
            max_length=4000, required=False, widget=forms.Textarea,
            *args, **kwargs)

class GuidelinesMessagesForm(forms.Form):
    pagetext_welcome_heading = MessageTextField()
    pagetext_welcome_heading2 = MessageTextField()

    messages_invite = MessageTextField()
    messages_manager = MessageTextField()
    messages_admin = MessageTextField()
    messages_application = MessageTextField()
    messages_joins = MessageTextField()

    guidelines_subtitle = MessageTextField()
    guidelines_translate = MessageTextField()
    guidelines_review = MessageTextField()

class RenameableSettingsForm(forms.ModelForm):
    logo = forms.ImageField(
        validators=[MaxFileSizeValidator(settings.AVATAR_MAX_SIZE)],
        required=False)
    square_logo = forms.ImageField(
        validators=[MaxFileSizeValidator(settings.AVATAR_MAX_SIZE)],
        required=False)

    class Meta:
        model = Team
        fields = ('name', 'description', 'logo', 'square_logo', 'is_visible')

class SettingsForm(forms.ModelForm):
    logo = forms.ImageField(
        validators=[MaxFileSizeValidator(settings.AVATAR_MAX_SIZE)],
        required=False)
    square_logo = forms.ImageField(
        validators=[MaxFileSizeValidator(settings.AVATAR_MAX_SIZE)],
        required=False)

    class Meta:
        model = Team
        fields = ('description', 'logo', 'square_logo', 'is_visible')

class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ('autocreate_subtitle', 'autocreate_translate',
                  'review_allowed', 'approve_allowed')

class PermissionsForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('membership_policy', 'video_policy', 'subtitle_policy',
                  'translate_policy', 'task_assign_policy', 'workflow_enabled',
                  'max_tasks_per_member', 'task_expiration',)

class LanguagesForm(forms.Form):
    preferred = forms.MultipleChoiceField(required=False, choices=())
    blacklisted = forms.MultipleChoiceField(required=False, choices=())

    def __init__(self, team, *args, **kwargs):
        super(LanguagesForm, self).__init__(*args, **kwargs)

        self.team = team
        self.fields['preferred'].choices = get_language_choices()
        self.fields['blacklisted'].choices = get_language_choices()

    def clean(self):
        preferred = set(self.cleaned_data['preferred'])
        blacklisted = set(self.cleaned_data['blacklisted'])

        if len(preferred & blacklisted):
            raise forms.ValidationError(_(u'You cannot blacklist a preferred language.'))

        return self.cleaned_data

class InviteForm(forms.Form):
    user_id = forms.CharField(required=False, widget=forms.Select)
    message = forms.CharField(required=False, widget=forms.Textarea)
    role = forms.ChoiceField(choices=TeamMember.ROLES[1:][::-1], initial='contributor')

    def __init__(self, team, user, *args, **kwargs):
        super(InviteForm, self).__init__(*args, **kwargs)
        self.team = team
        self.user = user
        self.fields['role'].choices = [(r, ROLE_NAMES[r])
                                       for r in roles_user_can_invite(team, user)]

    def clean_user_id(self):
        user_id = self.cleaned_data['user_id']

        try:
            invited_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise forms.ValidationError(_(u'User does not exist!'))
        except ValueError:
            raise forms.ValidationError(_(u'User does not exist!'))

        try:
            self.team.members.get(user__id=user_id)
        except TeamMember.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(_(u'User is already a member of this team!'))

        self.user_id = user_id
        # check if there is already an invite pending for this user:
        if Invite.objects.pending_for(team=self.team, user=invited_user).exists():
                raise forms.ValidationError(_(u'User has already been invited and has not replied yet.'))
        return user_id

    def save(self):
        from messages import tasks as notifier
        user = User.objects.get(id=self.user_id)
        invite = Invite.objects.create(
            team=self.team, user=user, author=self.user,
            role= self.cleaned_data['role'],
            note = self.cleaned_data['message'])
        invite.save()
        notifier.team_invitation_sent.delay(invite.pk)
        return invite


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name', 'description', 'workflow_enabled')

class DeleteLanguageVerifyField(forms.CharField):
    def __init__(self):
        help_text=_('Type "Yes I want to delete this language" if you are '
                    'sure you wish to continue')
        forms.CharField.__init__(self, label=_(u'Are you sure?'),
                                 help_text=help_text)

    def clean(self, value):
        # check text against a translated version of the confirmation string,
        # so when help_text gets translated things still work.
        if value != _(u'Yes I want to delete this language'):
            raise forms.ValidationError(_(u"Confirmation text doesn't match"))

class DeleteLanguageForm(forms.Form):
    verify_text = DeleteLanguageVerifyField()

    def __init__(self, user, team, language, *args, **kwargs):
        super(DeleteLanguageForm, self).__init__(*args, **kwargs)

        self.user = user
        self.team = team
        self.language = language

        # generate boolean fields for deleting languages (rather than forking
        # them).
        for sublanguage in self.language.get_dependent_subtitle_languages():
            key = self.key_for_sublanguage_delete(sublanguage)
            label = sublanguage.get_language_code_display()
            field = forms.BooleanField(label=label, required=False)
            field.widget.attrs['class'] = 'checkbox'
            self.fields[key] = field

    def clean(self):
        team_video = self.language.video.get_team_video()

        if not team_video:
            raise forms.ValidationError(_(
                u"These subtitles are not under a team's control."))

        if not can_delete_language(team_video.team, self.user):
            raise forms.ValidationError(_(
                u'You do not have permission to delete this language.'))

        return self.cleaned_data

    def key_for_sublanguage_delete(self, sublanguage):
        return 'delete_' + sublanguage.language_code

    def sublanguage_fields(self):
        return [self[key] for key in self.fields.keys()
                if key.startswith('delete_')]

    def languages_to_fork(self):
        assert self.is_bound
        rv = []
        for sublanguage in self.language.get_dependent_subtitle_languages():
            key = self.key_for_sublanguage_delete(sublanguage)
            if not self.cleaned_data.get(key):
                rv.append(sublanguage)
        return rv

class TaskUploadForm(SubtitlesUploadForm):
    task = forms.ModelChoiceField(Task.objects, required=True)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        video = kwargs.pop('video')
        super(TaskUploadForm, self).__init__(user, video, False,
                                             *args, **kwargs)

    def clean_task(self):
        task = self.cleaned_data['task']

        if not can_perform_task(self.user, task):
            raise forms.ValidationError(_(u'You cannot perform that task.'))

        if task.team_video.video_id != self.video.id:
            raise forms.ValidationError(_(u'Mismatched video and task!'))

        return task

    def clean(self):
        super(TaskUploadForm, self).clean()

        try:
            task = self.cleaned_data['task']
        except KeyError:
            raise forms.ValidationError(_(u'Task has been deleted'))
        language_code = self.cleaned_data['language_code']
        from_language_code = self.cleaned_data['from_language_code']

        if task.language and task.language != language_code:
            raise forms.ValidationError(_(
                'The selected language does not match the task.'))

        current_version = task.get_subtitle_version()
        if current_version:
            current_sl = current_version.subtitle_language
            current_source_lc = current_sl.get_translation_source_language_code()
            if current_source_lc and current_source_lc != from_language_code:
                raise forms.ValidationError(fmt(_(
                    "The selected source language %(from_code)s "
                    "does not match the existing source language "
                    "%(cur_code)s for that task."),
                      from_code=from_language_code,
                      cur_code=current_source_lc,
                ))
        return self.cleaned_data

    def save(self, *args, **kwargs):
        task = self.cleaned_data['task']
        language_code = self.cleaned_data['language_code']

        version = super(TaskUploadForm, self).save(*args, **kwargs)

        if not task.assignee:
            task.assignee = self.user
            task.set_expiration()

        task.new_subtitle_version = version
        task.language = language_code

        task.save()

        return version

def make_billing_report_form():
    """Factory function to create a billing report form """
    class BillingReportForm(forms.Form):
        teams = forms.ModelMultipleChoiceField(
            required=True,
            queryset=(Team.objects.with_recent_billing_record(40)
                      .order_by('name')),
            widget=forms.CheckboxSelectMultiple)
        start_date = forms.DateField(required=True, help_text='YYYY-MM-DD')
        end_date = forms.DateField(required=True, help_text='YYYY-MM-DD')
        type = forms.ChoiceField(required=True,
                                 choices=BillingReport.TYPE_CHOICES,
                                 initial=BillingReport.TYPE_BILLING_RECORD)
    return BillingReportForm

class TaskCreateSubtitlesForm(CreateSubtitlesForm):
    """CreateSubtitlesForm that also sets the language for task."""

    def __init__(self, request, task, data=None):
        CreateSubtitlesForm.__init__(self, request, task.team_video.video,
                                     data)
        self.task = task

    def handle_post(self):
        self.task.language = self.cleaned_data['subtitle_language_code']
        self.task.save()
        return CreateSubtitlesForm.handle_post(self)

class TeamMultiVideoCreateSubtitlesForm(MultiVideoCreateSubtitlesForm):
    """MultiVideoCreateSubtitlesForm that is task-aware."""

    def __init__(self, request, team, data=None):
        MultiVideoCreateSubtitlesForm.__init__(self, request, team.videos,
                                               data)
        self.team = team

    def handle_post(self):
        if self.team.workflow_enabled:
            # set the language for the task being performed (if needed)
            language = self.cleaned_data['subtitle_language_code']
            tasks = self.get_video().get_team_video().task_set
            (tasks.incomplete_subtitle().filter(language='')
             .update(language=language))
        return MultiVideoCreateSubtitlesForm.handle_post(self)

class MoveVideosForm(forms.Form):
    team = forms.ModelChoiceField(queryset=Team.objects.none(),
                                  required=True,
                                  empty_label=None)

    class Meta:
        fields = ('team')

    def __init__(self, user,  *args, **kwargs):
        super(MoveVideosForm, self).__init__(*args, **kwargs)
        self.fields['team'].queryset = user.managed_teams(include_manager=False)
