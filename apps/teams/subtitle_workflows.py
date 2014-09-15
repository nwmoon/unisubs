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

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from messages.models import Message
from subtitles import workflows
from subtitles.signals import subtitles_published
from teams.models import Task, TeamSubtitleNote
from teams.permissions import can_create_and_edit_subtitles
from utils import send_templated_email
from utils import translation
from utils.behaviors import DONT_OVERRIDE
from utils.text import fmt
from videos.tasks import video_changed_tasks

class TaskAction(workflows.Action):
    def send_signals(self, subtitle_language, version):
        # If we perform any action and it results in a public version, then we
        # should send the subtitles_published signal.
        if subtitle_language.get_tip(public=True):
            subtitles_published.send(subtitle_language, version=version)

class Complete(TaskAction):
    """Used when the initial transcriber/translator completes their work """
    name = 'complete'
    label = ugettext_lazy('Complete')
    in_progress_text = ugettext_lazy('Saving')
    visual_class = 'endorse'
    complete = True

    def do_perform(self, user, video, subtitle_language, saved_version):
        if saved_version is not None:
            # I think the cleanest way to handle things would be to create the
            # review/approve task now but there is already code in
            # subtitles.pipeline to do that.  It would be nice to move that
            # code out of that app and into here, but maybe we should just
            # leave it and wait to phase the tasks system out
            return
        try:
            task = (video.get_team_video().task_set
                    .incomplete_subtitle_or_translate()
                    .filter(language=subtitle_language.language_code).get())
        except Task.DoesNotExist:
            # post publish edit, no task is available
            return
        else:
            task.complete()

def _complete_task(user, video, subtitle_language, saved_version, approved):
    team_video = video.get_team_video()
    task = (team_video.task_set
            .incomplete_review_or_approve()
            .get(language=subtitle_language.language_code))
    if task.assignee is None:
        task.assignee = user
    elif task.assignee != user:
        raise ValueError("Task not assigned to user")
    task.new_subtitle_version = subtitle_language.get_tip()
    task.approved = approved
    task.complete()
    if saved_version is None:
        if saved_version is None:
            version_id = None
        else:
            version_id = saved_version.id
            video_changed_tasks.delay(team_video.video_id, version_id)

class Approve(TaskAction):
    name = 'approve'
    label = ugettext_lazy('Approve')
    in_progress_text = ugettext_lazy('Approving')
    visual_class = 'endorse'
    complete = True

    def do_perform(self, user, video, subtitle_language, saved_version):
        _complete_task(user, video, subtitle_language, saved_version,
                       Task.APPROVED_IDS['Approved'])

class SendBack(TaskAction):
    name = 'send-back'
    label = ugettext_lazy('Send Back')
    in_progress_text = ugettext_lazy('Sending back')
    visual_class = 'send-back'
    complete = False

    def do_perform(self, user, video, subtitle_language, saved_version):
        _complete_task(user, video, subtitle_language, saved_version,
                       Task.APPROVED_IDS['Rejected'])

class TeamEditorNotes(workflows.EditorNotes):
    def __init__(self, team_video, language_code):
        self.team = team_video.team
        self.video = team_video.video
        self.team_video = team_video
        self.language_code = language_code
        self.heading = _('Team Notes')
        self.notes = list(TeamSubtitleNote.objects
                          .filter(video=self.video, team=self.team,
                                  language_code=language_code)
                          .order_by('created')
                          .select_related('user'))

    def post(self, user, body):
        return TeamSubtitleNote.objects.create(
            team=self.team, video=self.video,
            language_code=self.language_code,
            user=user, body=body)

class TaskTeamEditorNotes(TeamEditorNotes):
    def post(self, user, body):
        note = super(TaskTeamEditorNotes, self).post(user, body)
        email_to = [u for u in self.all_assignees() if u != note.user]
        self.send_messages(note, email_to)
        return note

    def all_assignees(self):
        task_qs = (self.team_video.task_set
                   .filter(assignee__isnull=False)
                   .select_related('assignee'))
        return set(task.assignee for task in task_qs)

    def send_messages(self, note, user_list):
        subject = fmt(
            _(u'%(user)s added a note while editing %(title)s'),
            user=unicode(note.user), title=self.video.title_display())
        tasks_url = "{0}&assignee=anyone&language_code={1}".format(
            self.team_video.get_tasks_page_url(),
            self.language_code)
        data = {
            'note_user': unicode(note.user),
            'body': note.body,
            'tasks_url': tasks_url,
            'video': self.video.title_display(),
            'language': translation.get_language_label(self.language_code),
        }
        email_template = ("messages/email/"
                          "task-team-editor-note-notifiction.html")
        message_template = 'messages/task-team-editor-note.html'

        for user in user_list:
            send_templated_email(user, subject, email_template, data,
                                 fail_silently=not settings.DEBUG)

            Message.objects.create(
                user=user, subject=subject,
                content=render_to_string(message_template, data))

class TeamWorkflow(workflows.DefaultWorkflow):
    def __init__(self, team_video):
        workflows.DefaultWorkflow.__init__(self, team_video.video)
        self.team_video = team_video

    def get_editor_notes(self, language_code):
        return TeamEditorNotes(self.team_video, language_code)

    def user_can_view_private_subtitles(self, user, language_code):
        return self.team_video.team.is_member(user)

    def user_can_edit_subtitles(self, user, language_code):
        return can_create_and_edit_subtitles(user, self.team_video,
                                             language_code)
class TaskTeamWorkflow(TeamWorkflow):
    def get_work_mode(self, user, language_code):
        task = self.team_video.get_task_for_editor(language_code)
        if task is not None:
            if task.is_approve_task():
                heading = _("Approve")
            elif task.is_review_task():
                heading = _("Review")
            else:
                # get_task_for_editor should only return approve/review tasks
                raise ValueError("Wrong task type: %s" % task)
            return workflows.ReviewWorkMode(heading)
        else:
            return workflows.NormalWorkMode()

    def get_actions(self, user, language_code):
        task = self.team_video.get_task_for_editor(language_code)
        if task is not None:
            # review/approve task
            return [SendBack(), Approve()]
        else:
            # subtitle/translate task
            return [Complete()]

    def get_editor_notes(self, language_code):
        return TaskTeamEditorNotes(self.team_video, language_code)

    def get_add_language_mode(self, user):
        if self.team_video.team.is_member(user):
            return mark_safe(
                fmt(_(
                    '<a class="icon" href="%(url)s">'
                    '<img src="%(static_url)simages/edit-subtitles.png"></a>'
                    'View <a href="%(url)s">tasks for this video</a>.'),
                    url=self.team_video.get_tasks_page_url(),
                    static_url=settings.STATIC_URL))
        else:
            return None

    def action_for_add_subtitles(self, user, language_code, complete):
        tasks = self.team_video.task_set
        if (complete == True and
            tasks.incomplete_subtitle_or_translate().exists()):
            return Complete()
        else:
            return super(TaskTeamWorkflow, self).action_for_add_subtitles(
                user, language_code, complete)

@workflows.get_workflow.override
def get_team_workflow(video):
    team_video = video.get_team_video()
    if team_video is None:
        return DONT_OVERRIDE
    if team_video.team.is_tasks_team():
        return TaskTeamWorkflow(team_video)
    else:
        return TeamWorkflow(team_video)
