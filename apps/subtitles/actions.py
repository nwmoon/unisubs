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

"""Extensible user actions for subtitle sets

Actions are things things that users can do to a subtitle set other than
changing the actual subtitles.  They roughly correspond to the buttons in the
editor at the bottom of the workflow session (publish, endorse, send back,
etc).  Actions can occur alongside subtitle changes, or independent of them.

This module defines the default actions for all videos and provides a
mechanism for other apps to override the actions for specific videos.
This is used by components like the tasks system or the collab system to
create actions specific to their workflows.

To extend the actions system, components must:

    * create one or more Action subclasess
    * create an ActionManager subclass
    * call register_action_manager() with the ActionManager subclass
"""

from django.utils.translation import ugettext_lazy

class Action(object):
    """Action -- base class for actions.  """
    name = NotImplemented #: Machine-friendly name
    #: human-friendly label.  Strings should be run through ugettext_lazy()
    label = NotImplemented
    #: visual class to render the action with.  This controls things like the
    #: icon we use in our editor button.  Must be one of the `CLASS_` constants
    visual_class = None
    #: complete_handling defines how to handle subtitles_complete, must be one
    #: of the COMPLETE_ constants or None (the default)
    complete_handling = None

    #: This action signifies that the subtitles are complete.  When this action
    #: is performed, we set subtitles_complete to True.
    #: This means this action is not valid if there are no subtitles or some
    #: subtitles don't have timings and we should prevent it from happening.
    COMPLETE_SET = 'complete-set'
    #: This action signifies that the subtitles are not complete.  When this
    #: action is performed, we set subtitles_complete to False
    COMPLETE_UNSET = 'complete-unset'

    #: endorse/approve buttons
    CLASS_ENDORSE = 'endorse'
    #: reject/send-back buttons
    CLASS_SEND_BACK = 'send-back'

    def handle(self, user, subtitle_language, saved_version):
        """Handle this action being performed.

        :param user: User performing the action
        :param subtitle_language: SubtitleLanguage being changed
        :param saved_version: new version that was created for subtitle
            changes that happened alongside this action.  Will be None if no
            changes were made.
        """
        raise NotImplementedError()

class ActionManager(object):
    """Generate actions for videos"""

    def get_actions(self, user, subtitle_language):
        """Get actions for a video

        :returns: list of :class:`Action` objects for this video, or None if
            this class doesn't want to handle actions for this video
        """
        raise NotImplementedError()

class Publish(Action):
    """Defines the publish action

    Publish simply sets the subtitles_complete flag to True
    """
    name = 'publish'
    label = ugettext_lazy('Publish')
    complete_handling = Action.COMPLETE_SET

    def handle(self, user, subtitle_language, saved_version):
        pass

class DefaultActionManager(Action):
    """Handle default actions for videos """
    def get_actions(self, user, subtitle_language):
        return [Publish()]

class _ActionManagerList(object):
    """Stores a list of ActionManagers

    This class is used to handle the various module functions like
    register_action_manager(), get_actions(), and perform_action()
    """
    def __init__(self):
        self.action_managers = []
        self.default_action_manager = DefaultActionManager()

    def get_actions(self, user, subtitle_language):
        for action_manager in self.action_managers:
            actions = action_manager.get_actions(user, subtitle_language)
            if actions is not None:
                return actions
        return self.default_action_manager.get_actions(
            user, subtitle_language)

    def _lookup_action(self, user, subtitle_language, action_name,
                       saved_version):
        actions = self.get_actions(user, subtitle_language)
        for action in actions:
            if action.name == action_name:
                return action
        raise ValueError("No action: %s" % action_name)

    def _check_can_perform(self, action, subtitle_language):
        """Check if we can perform an action.

        :returns: None if the user can perform the action, otherwise a string
        that explains why not
        """
        if action.complete_handling == Action.COMPLETE_SET:
            tip = subtitle_language.get_tip()
            if tip is None or not tip.has_subtitles or not tip.is_synced():
                return 'Subtitles not complete'

    def perform_action(self, user, subtitle_language, action_name,
                       saved_version):
        action = self._lookup_action(user, subtitle_language, action_name,
                                     saved_version)
        cant_perform_reason = self._check_can_perform(
            action, subtitle_language)
        if cant_perform_reason is not None:
            raise ValueError(cant_perform_reason)

        self.update_subtitles_complete(subtitle_language, action)
        action.handle(user, subtitle_language, saved_version)

    def can_perform_action(self, user, subtitle_language, action_name,
                       saved_version):
        action = self._lookup_action(user, subtitle_language, action_name,
                                     saved_version)
        return self._check_can_perform(action, subtitle_language) is None

    def update_subtitles_complete(self, subtitle_language, action):
        if (action.complete_handling == Action.COMPLETE_SET and
            not subtitle_language.subtitles_complete):
            subtitle_language.subtitles_complete = True
            subtitle_language.save()
        elif (action.complete_handling == Action.COMPLETE_UNSET and
            subtitle_language.subtitles_complete):
            subtitle_language.subtitles_complete = False
            subtitle_language.save()

_action_manager_list = _ActionManagerList()

def register_action_manager(action_manager):
    """Register a new :class:`ActionManager`

    Other apps that want to change the available actions for certain videos
    should implement their own ActionManager subclass and pass it in.
    """
    if isinstance(action_manager, type):
        action_manager = action_manager()
    _action_manager_list.action_managers.append(action_manager)

def get_actions(user, subtitle_language):
    """Get a list of available actions for a video/language

    :returns: list of :class:`Action` objects
    """
    return _action_manager_list.get_actions(user, subtitle_language)

def perform_action(user, subtitle_language, action, saved_version):
    """Perform an action on a video/language.  """
    _action_manager_list.perform_action(user, subtitle_language, action,
                                        saved_version)
