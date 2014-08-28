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

from __future__ import absolute_import

from django.test import TestCase
from nose.tools import *
import mock

from subtitles import actions
from subtitles import pipeline
from utils.factories import *

class TestAction(actions.Action):
    def __init__(self, name):
        self.name = self.label = name
        self.complete_handling = actions.Action.COMPLETE_UNSET
        self.handle = mock.Mock()

    def __str__(self):
        return "TestAction: %s" % self.name

    def __repr__(self):
        return "TestAction(%r)" % self.name

class TestActionManager(actions.ActionManager):
    def __init__(self):
        self.actions = []
        self.handle_get_actions = True

    def get_actions(self, user, subtitle_language):
        if self.handle_get_actions:
            return self.actions
        else:
            return None

class ActionsTest(TestCase):
    def setUp(self):
        self.actions = {}
        self.action_manager_list = actions._ActionManagerList()
        self.action_manager_list.default_action_manager = \
                self.make_action_manager(['default'], add_to_list=False)
        self.user = UserFactory()
        self.video = VideoFactory()
        pipeline.add_subtitles(self.video, 'en',
                               SubtitleSetFactory(num_subs=10))
        self.subtitle_language = self.video.subtitle_language('en')

    def make_action_manager(self, action_names, add_to_list=True):
        assert_is_instance(action_names, list)
        action_manager = TestActionManager()
        for name in action_names:
            action = TestAction(name)
            self.actions[name] = action
            action_manager.actions.append(action)
        if add_to_list:
            self.action_manager_list.action_managers.append(action_manager)
        return action_manager

    def run_get_actions(self):
        return self.action_manager_list.get_actions(
            self.user, self.subtitle_language)

    def run_perform_action(self, action_name, saved_version):
        return self.action_manager_list.perform_action(
            self.user, self.subtitle_language, action_name, saved_version)

    def run_can_perform_action(self, action_name, saved_version):
        return self.action_manager_list.can_perform_action(
            self.user, self.subtitle_language, action_name, saved_version)

    def test_get_actions(self):
        # Test that we use the correct ActionManager to get actions
        action_manager1 = self.make_action_manager(['action1'])
        action_manager2 = self.make_action_manager(['action2'])

        # action manager1 is returning a list, we should use that
        action_manager1.handle_get_actions = True
        action_manager2.handle_get_actions = False
        assert_equal(self.run_get_actions(), [self.actions['action1']])

        # action manager2 is returning a list, we should use that
        action_manager1.handle_get_actions = False
        action_manager2.handle_get_actions = True
        assert_equal(self.run_get_actions(), [self.actions['action2']])

        # neither return a list, we should use the default action manager
        action_manager1.handle_get_actions = False
        action_manager2.handle_get_actions = False
        assert_equal(self.run_get_actions(), [self.actions['default']])

    def test_perform_action(self):
        # Test that we use the correct ActionManager to get actions
        action_manager = self.make_action_manager(['action'])
        action_manager.handle_get_actions = True
        self.run_perform_action('action', None)
        self.actions['action'].handle.assert_called_with(
            self.user, self.subtitle_language, None)

    def test_perform_with_invalid_action(self):
        action_manager = self.make_action_manager(['action'])
        action_manager.handle_get_actions = True
        with assert_raises(ValueError):
            self.run_perform_action('other-action', None)

    def test_set_subtitles_complete_flag(self):
        action_manager = self.make_action_manager(['action1', 'action2'])
        self.actions['action1'].complete_handling = actions.Action.COMPLETE_SET
        self.subtitle_language.subtitles_complete = False
        # when we run an action with COMPLETE_SET, it should set
        # subtitles_complete to True
        self.run_perform_action('action1', None)
        assert_equals(self.subtitle_language.subtitles_complete, True)
        # If the action has COMPLETE_UNSET, it should sit it to False
        self.run_perform_action('action2', None)
        assert_equals(self.subtitle_language.subtitles_complete, False)

    def test_complete_set_requires_completed_subs(self):
        # With 0 subtitles, we shouldn't be able to perform an action with
        # COMPLETE_SET
        pipeline.add_subtitles(self.video, 'en',
                               SubtitleSetFactory(num_subs=0))
        action_manager = self.make_action_manager(['action'])
        self.actions['action'].complete_handling = actions.Action.COMPLETE_SET
        with assert_raises(ValueError):
            self.run_perform_action('action', None)
        assert_false(self.run_can_perform_action('action', None))

class DefaultActionsTest(TestCase):
    def setUp(self):
        self.default_action_manager = actions.DefaultActionManager()
        self.user = UserFactory()
        self.video = VideoFactory()
        self.subtitle_language = self.video.subtitle_language('en')

    def test_action_manager_returns_publish(self):
        get_actions_rv = self.default_action_manager.get_actions(
            self.user, self.subtitle_language)
        assert_equals([type(a) for a in get_actions_rv], [actions.Publish])

    def test_publish_completes_subtitles(self):
        assert_equals(actions.Publish.complete_handling,
                      actions.Action.COMPLETE_SET)
