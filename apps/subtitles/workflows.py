# Amara, universalsubtitles.org
#
# Copyright (C) 2014 Participatory Culture Foundation
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

"""
Subtitle Workflows
==================

Subtitle workflows control how subtitle sets get edited and published.  In
particular they control:

- Work Modes -- Tweak the subtitle editor behavior (for example review mode)
- Actions -- User actions that can be done to subtitle sets (Publish,
  Approve, Send back, etc).
- Permissions -- Who can edit subtitles, who can view private subtitles

.. autoclass:: Workflow
    :members: get_work_mode, get_actions, action_for_add_subtitles,
        get_editor_notes, extra_tabs, get_add_language_mode,
        user_can_view_video, user_can_edit_subtitles,
        user_can_view_private_subtitles
.. autofunction:: get_workflow(video)

Editor Notes
------------
.. autoclass:: EditorNotes

Work Modes
----------
.. autoclass:: WorkMode

Actions
-------

Actions are things things that users can do to a subtitle set other than
changing the actual subtitles.  They correspond to the buttons in the editor
at the bottom of the workflow session (publish, endorse, send back, etc).
Actions can occur alongside changes to the subtitle lines or independent of
them.

.. autoclass:: Action
   :members:

.. autoclass:: Publish

"""

from collections import namedtuple
from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext as _

from subtitles import signals
from subtitles.exceptions import ActionError
from subtitles.models import SubtitleNote
from utils.behaviors import behavior

class Workflow(object):
    """
    Workflow
    --------

    A workflow class controls the overall workflow for editing and publishing
    subtitles.  Workflows control the work modes, actions, and permissions for
    a set of subtitles.

    By default, we use a workflow that makes sense for public videos -- Anyone
    can edit, the only action is Publish, etc.  However, other components can
    create custom workflows for specific videos by:

    - Creating a Workflow subclass
    - Overriding :func:`get_workflow` and returning a custom workflow object
    """

    def __init__(self, video):
        self.video = video

    def get_work_mode(self, user, language_code):
        """Get the work mode to use for an editing session

        Args:
            user (User): user who is editing
            language_code (str): language being edited

        Returns:
            :class:`WorkMode` object to use
        """
        raise NotImplementedError()

    def get_actions(self, user, language_code):
        """Get available actions for a user

        Args:
            user (User): user who is editing
            language_code (str): language being edited

        Returns:
            list of :class:`Action` objects that are available to the user.
        """
        raise NotImplementedError()

    def action_for_add_subtitles(self, user, language_code, complete):
        """Get an action to use for add_subtitles()

        This is used when pipeline.add_subtitles() is called, but not passed
        an action.  This happens for a couple reasons:

        - User saves a draft (in which case complete will be None)
        - User is adding subtitles via the API (complete can be True, False,
          or None)

        Subclasses can override this method if they want to use different
        actions to handle this case.

        Args:
            user (User): user adding subtitles
            language_code (str): language being edited
            complete (bool or None): complete arg from add_subtitles()

        Returns:
            Action object or None.
        """
        if complete is None:
            return None
        elif complete:
            return APIComplete()
        else:
            return Unpublish()

    def extra_tabs(self, user):
        """Get extra tabs for the videos page

        Returns:
            list of (name, title) tuples.  name is used for the tab id, title
            is a human friendly title.  For each tab name you should create a
            video-<name>.html and video-<name>-tab.html templates.  If you
            need to pass variables to those templates, create a
            setup_tab_<name> method that inputs the same args as the methods
            from VideoPageContext and returns a dict of variables for the
            template.
        """
        return []

    def get_add_language_mode(self, user):
        """Control the add new language section of the video page

        Args:
            user (User): user viewing the page

        Returns:
            - None/False: Don't display anything
            - "<standard>": Use the standard behavior -- a link that opens
              the create subtitles dialog.
            - any other string: Render this in the section.  You probably want
              to send the string through mark_safe() to avoid escaping HTML
              tags.
        """
        return "<standard>"

    def get_editor_notes(self, language_code):
        """Get notes to display in the editor

        Returns:
            :class:`EditorNotes` object
        """
        return EditorNotes(self.video, language_code)

    def lookup_action(self, user, language_code, action_name):
        for action in self.get_actions(user, language_code):
            if action.name == action_name:
                return action
        raise LookupError("No action: %s" % action_name)

    def perform_action(self, user, language_code, action_name):
        """Perform an action on a subtitle set

        This method is used to perform an action by itself, without new
        subtitles being added.
        """
        action = self.lookup_action(user, language_code, action_name)
        subtitle_language = self.video.subtitle_language(language_code)
        action.validate(user, self.video, subtitle_language, None)
        action.update_language(user, self.video, subtitle_language, None)
        action.perform(user, self.video, subtitle_language, None)

    def user_can_view_private_subtitles(self, user, language_code):
        """Check if a user can view private subtitles

        Private subtitles are subtitles with visibility or visibility_override
        set to "private".  A typical use is to limit viewing of the subtitles
        to members of a team.

        Returns:
            True/False
        """
        raise NotImplementedError()

    def user_can_view_video(self, user):
        """Check if a user can view the video

        Returns:
            True/False
        """
        raise NotImplementedError()

    def user_can_edit_subtitles(self, user, language_code):
        """Check if a user can edit subtitles

        Returns:
            True/False
        """
        raise NotImplementedError()

    def editor_data(self, user, language_code):
        """Get data to pass to the editor for this workflow."""
        editor_notes = self.get_editor_notes(language_code)
        return {
            'work_mode': self.get_work_mode(user, language_code).editor_data(),
            'actions': [action.editor_data() for action in
                        self.get_actions(user, language_code)],
            'notesHeading': editor_notes.heading,
            'notes': editor_notes.note_editor_data(),
        }

    def editor_video_urls(self, language_code):
        """Get video URLs to send to the editor."""
        return [v.url for v in self.video.get_video_urls()]

@behavior
def get_workflow(video):
    """Get the workflow to use for a subtitle set

    This method uses the :doc:`behaviors <behaviors>` module, to allow
    other apps to override this and control the workflow for specific
    subtitles sets.  A typical example is the tasks system which creates a
    custom workflow for videos owned by tasks teams.
    """
    return DefaultWorkflow(video)

class WorkMode(object):
    """
    Work modes are used to change the workflow section of the editor and
    affect the overall feel of the editing session.  Currently we only have 2
    work modes:

    * .. autoclass:: NormalWorkMode
    * .. autoclass:: ReviewWorkMode
    """

    def editor_data(self):
        """Get data to send to the editor for this work mode."""
        raise NotImplementedError()

class NormalWorkMode(object):
    """The usual work mode with typing/syncing/review steps."""

    def editor_data(self):
        return {
            'type': 'normal',
        }

class ReviewWorkMode(object):
    """Review someone else's work (for example a review/approve task)

    Args:
        heading (str): heading to display in the workflow area
    """

    def __init__(self, heading):
        self.heading = heading

    def editor_data(self):
        return {
            'type': 'review',
            'heading': self.heading,
        }

class Action(object):
    """Base class for actions

    Other components can define new actions by subclassing Action, setting the
    class attributes, and optionally implementing perform().

    """

    name = NotImplemented 
    """Machine-friendly name"""

    label = NotImplemented
    """human-friendly label.  Strings should be run through ugettext_lazy()
    """
    in_progress_text = NotImplemented
    """text to display in the editor while this action is being performed.
    Strings should be run through ugettext_lazy()
    """

    visual_class = None
    """
    visual class to render the action with.  This controls things like the
    icon we use in our editor button.  Must be one of the `CLASS_` constants
    """

    complete = None
    """
    complete defines how to handle subtitles_complete. There are 3 options:

        - True -- this action sets subtitles_complete
        - False -- this action unsets subtitles_complete
        - None (default) - this action doesn't change subtitles_complete
    """

    subtitle_visibility = 'public'
    """
    Visibility value for newly created SubtitleVerisons.
    """

    CLASS_ENDORSE = 'endorse'
    """endorse/approve buttons"""
    CLASS_SEND_BACK = 'send-back'
    """reject/send-back buttons"""

    def validate(self, user, video, subtitle_language, saved_version):
        """Check if we can perform this action.

        Args:
            user (User): User performing the action
            video (Video): Video being changed
            subtitle_language (SubtitleLanguage): SubtitleLanguage being
                changed
            saved_version (SubtitleVersion or None): new version that was
                created for subtitle changes that happened alongside this
                action.  Will be None if no changes were made.

        Raises:
            ActionError -- this action can't be performed
        """
        if self.complete:
            if saved_version:
                version = saved_version
            else:
                version = subtitle_language.get_tip()
            if (version is None or not version.has_subtitles
                or not version.is_synced()):
                raise ActionError('Subtitles not complete')

    def perform(self, user, video, subtitle_language, saved_version):
        """Perform this action

        Args:
            user (User): User performing the action
            video (Video): Video being changed
            subtitle_language (SubtitleLanguage): SubtitleLanguage being
                changed
            saved_version (SubtitleVersion or None): new version that was
                created for subtitle changes that happened alongside this
                action.  Will be None if no changes were made.
        """
        pass

    def update_language(self, user, video, subtitle_language, saved_version):
        """Update the subtitle language after adding subtitles

        Args:
            user (User): User performing the action
            video (Video): Video being changed
            subtitle_language (SubtitleLanguage): SubtitleLanguage being
                changed
            saved_version (SubtitleVersion or None): new version that was
                created for subtitle changes that happened alongside this
                action.  Will be None if no changes were made.
        """
        if self.complete is not None:
            subtitle_language.subtitles_complete = self.complete
            subtitle_language.save()

    def editor_data(self):
        """Get a dict of data to pass to the editor for this action."""
        return {
            'name': self.name,
            'label': unicode(self.label),
            'in_progress_text': unicode(self.in_progress_text),
            'class': self.visual_class,
            'complete': self.complete,
        }

class Publish(Action):
    """Publish action

    Publish sets the subtitles_complete flag to True
    """
    name = 'publish'
    label = ugettext_lazy('Publish')
    in_progress_text = ugettext_lazy('Saving')
    visual_class = 'endorse'
    complete = True

    def perform(self, user, video, subtitle_language, saved_version):
        signals.subtitles_published.send(subtitle_language,
                                         version=saved_version)

class Unpublish(Action):
    """Unpublish action

    Unpublish sets the subtitles_complete flag to False
    """
    name = 'unpublish'
    label = ugettext_lazy('Unpublish')
    in_progress_text = ugettext_lazy('Saving')
    visual_class = 'send-back'
    complete = False

class SaveDraft(Action):
    name = 'save-draft'
    label = ugettext_lazy('Save Draft')
    in_progress_text = ugettext_lazy('Saving')
    complete = None

class APIComplete(Action):
    """Action that handles complete=True from the API

    We have some strange rules here to maintain API compatibility:
        - If the subtitle set is synced or there are no subtitles, then we set
          subtitles_complete=True
        - If not, we set to to False
    """
    name = 'api-complete'
    label = ugettext_lazy('API Complete')
    in_progress_text = ugettext_lazy('Saving')
    visual_class = 'endorse'
    complete = None

    def update_language(self, user, video, subtitle_language, saved_version):
        subtitle_language.subtitles_complete = saved_version.is_synced()
        subtitle_language.save()

    def perform(self, user, video, subtitle_language, saved_version):
        if subtitle_language.subtitles_complete:
            signals.subtitles_published.send(subtitle_language,
                                             version=saved_version)

class EditorNotes(object):
    """Manage notes for the subtitle editor.

    EditorNotes handles fetching notes for the editor and posting new ones.

    Attributes:
        heading: heading for the editor section
        notes: list of SubtitleNotes for the editor (or any model that
            inherits from SubtitleNoteBase)

    .. automethod:: post
    """

    def __init__(self, video, language_code):
        self.video = video
        self.language_code = language_code
        self.heading = _('Notes')
        self.notes = list(SubtitleNote.objects
                          .filter(video=video, language_code=language_code)
                          .order_by('created')
                          .select_related('user'))

    def post(self, user, body):
        """Add a new note.

        Args:
            user (CustomUser): user adding the note
            body (unicode): note text
        """
        return SubtitleNote.objects.create(video=self.video,
                                           language_code=self.language_code,
                                           user=user, body=body)

    def format_created(self, created, now):
        if created > now - timedelta(hours=12):
            format_str = '{d:%l}:{d.minute:02} {d:%p}'
        elif created > now - timedelta(days=6):
            format_str = '{d:%a}, {d:%l}:{d.minute:02} {d:%p}'
        else:
            format_str = ('{d:%b} {d.day} {d.year}, '
                          '{d:%l}:{d.minute:02} {d:%p}')
        return format_str.format(d=created)

    def note_editor_data(self):
        now = datetime.now()
        return [
            dict(user=note.get_username(),
                 created=self.format_created(note.created, now),
                 body=note.body)
            for note in self.notes
        ]

class DefaultWorkflow(Workflow):
    def get_work_mode(self, user, language_code):
        return NormalWorkMode()

    def get_actions(self, user, language_code):
        return [SaveDraft(), Publish()]

    def user_can_view_private_subtitles(self, user, language_code):
        return user.is_staff

    def user_can_view_video(self, user):
        return True

    def user_can_edit_subtitles(self, user, language_code):
        return True
