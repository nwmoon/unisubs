# Amara, universalsubtitles.org
#
# Copyright (C) 2015 Participatory Culture Foundation
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
Team Resource
^^^^^^^^^^^^^

Get a list of teams
+++++++++++++++++++

.. http:get:: /api/teams/

    ``paginated``

    :>json name: Name of the team
    :>json slug: Machine name for the team slug (used in URLs)
    :>json description: Team description
    :>json is_visible: Should this team's videos be publicly visible?
    :>json membership_policy: See below for possible values
    :>json video_policy: See below for possible values

Get a list of teams
+++++++++++++++++++
.. http:get:: /api/teams/[team-slug]/

    Returns one entry from the team list resource data.

Updating a team
+++++++++++++++

.. http:put:: /api/teams/[team-slug]:

    :<json name: (required) Name of the team
    :<json slug: (required) Manchine name for the team (used in URLs)
    :<json description: Team description
    :<json is_visible: Should this team be publicly visible?
    :<json membership_policy: See below for possible values
    :<json video_policy: See below for possible values

Policy values
+++++++++++++

Membership policy:

* ``Open``
* ``Application``
* ``Invitation by any team member``
* ``Invitation by manager``
* ``Invitation by admin``

Video policy:

* ``Any team member``
* ``Managers and admins``
* ``Admins only``

Team Member Resource
^^^^^^^^^^^^^^^^^^^^

Get info on a team member
+++++++++++++++++++++++++

.. http:get:: /api/teams/[team-slug]/members/[username]

    :<json username: username
    :<json role: One of: ``owner``, ``admin``, ``manager``, or ``contributor``

Litsing all team members
++++++++++++++++++++++++

.. http:get:: /api/teams/[team-slug]/members/

    Returns a list of team member data.  Each item is the same as above.

Add a new member to a team
++++++++++++++++++++++++++

.. http:post:: /api/teams/[team-slug]/members/

    :>json username: username of the user to add
    :>json role: One of: ``owner``, ``admin``, ``manager``, or ``contributor``


Change a team member's role
+++++++++++++++++++++++++++

.. http:put:: /api/teams/[team-slug]/members/[username]/

    :>json role: One of: ``owner``, ``admin``, ``manager``, or ``contributor``

Removing a user from a team
+++++++++++++++++++++++++++

.. http:delete:: /api/teams/[team-slug]/members/[username]/

Safe Team Member Resource
^^^^^^^^^^^^^^^^^^^^^^^^^

This resource behaves the same as the normal Team Member resource except with
couple differences for the POST action to add members

* An invitation is sent to the user to join the team instead of simply adding
  them
* If no user exists with the username, and an ``email`` field is included in
  the POST data, we will create a user and send an email to the email account.

Project Resource
^^^^^^^^^^^^^^^^

List a team's projects
++++++++++++++++++++++

.. http:get:: /api/teams/[team-slug]/projects/

    :>jsonarr name: project name
    :>jsonarr slug: machine-name for the project
    :>jsonarr description: project description
    :>jsonarr guidelines: Project guidelines for users working on it
    :>jsonarr resource_uri: API URI for project details
    :>jsonarr created: datetime when the project was created
    :>jsonarr modified: datetime when the project was last changed
    :>jsonarr workflow_enabled: Are tasks enabled for this project?

Get details on a project
++++++++++++++++++++++++

.. http:get:: /api/teams/[team-slug]/projects/[project-slug]/

    Returns the same data as the project list resource


Create a new project
++++++++++++++++++++

.. http:post:: /api/teams/[team-slug]/projects/

    :<json name: project name
    :<json slug: machine-name for the project
    :<json description: project description *(optional)*
    :<json guidelines: Project guidelines for users working on it *(optional)*

Updating a project
++++++++++++++++++

.. http:put:: /api/teams/[team-slug]/projects/[project-slug]/

    Inputs the same data is the create project resource

Delete a project
++++++++++++++++

.. http:delete:: /api/teams/[team-slug]/projects/[project-slug]/

Task Resource
^^^^^^^^^^^^^

List all tasks for a given team
+++++++++++++++++++++++++++++++

.. http:get:: /api/teams/[team-slug]/tasks/

    :query assignee: Show only tasks assigned to a username
    :query priority: Show only tasks with a given priority
    :query type: Show only tasks of a given type
    :query video_id: Show only tasks that pertain to a given video
    :query order_by: Apply sorting to the task list.  Possible values:

        * ``created``   Creation date
        * ``-created``  Creation date (descending)
        * ``priority``  Priority
        * ``-priority`` Priority (descending)
        * ``type``      Task type (details below)
        * ``-type``     Task type (descending)

    :query completed: Show only complete tasks
    :query completed-before: Show only tasks completed before a given date
        (unix timestamp)
    :query completed-after: Show only tasks completed before a given date
        (unix timestamp)
    :query open: Show only incomplete tasks

    :>jsonarr video_id: ID of the video being worked on
    :>jsonarr language: Language code being worked on
    :>jsonarr id: ID for the task
    :>jsonarr type: type of task.  One of ``Subtitle``, ``Translate``,
         ``Review``, or ``Approve``
    :>jsonarr assignee: username of the task assignee (or null)
    :>jsonarr priority: Integer priority for the task
    :>jsonarr completed: Date/time when the task was completed (or null)
    :>jsonarr approved: Approval status of the task.  One of ``In Progress``,
        ``Approved``, or ``Rejected``
    :>jsonarr resource_uri: API URL for the task

Task detail
+++++++++++

.. http:get:: /api/teams/[team-slug]/tasks/[task-id]/

    Returns the same data as the task list API

Create a new task
+++++++++++++++++

.. http:post:: /api/teams/[team-slug]/tasks/

    :<json video_id: Video ID
    :<json language: language code
    :<json type: task type to create.  Must be ``Subtitle`` or ``Translate``
    :<json assignee: Username of the task assignee *(optional)*
    :<json priority: Priority for the task *(optional)*

Update an existing task
+++++++++++++++++++++++

.. http:put:: /api/teams/[team-slug]/tasks/[task-id]/

    :<json assignee: Username of the task assignee or null to unassign
    :<json priority: priority of the task
    :<json send_back: send a truthy value to send the back back *(optional)*
    :<json complete: send a truthy value to complete/approve the task
        *(optional)*
    :<json version_number: Specify the version number of the subtitles that
        were created for this task *(optional)*

.. note::

    If both send_back and approved are specified, then send_back will take
    preference.

Delete an existing task
+++++++++++++++++++++++

.. http:delete:: /api/teams/[team-slug]/tasks/[task-id]/

Team Applications resource
^^^^^^^^^^^^^^^^^^^^^^^^^^

For teams with membership by application only.

List applications
+++++++++++++++++

.. http:get:: /api/teams/[team-slug]/applications

    ``paginated``

    :query status: Include only applications with this status
    :query timestamp integer before: Include only applications submitted before
        this time.
    :query timestamp after: Include only applications submitted after this
        time.
    :query username user: Include only applications from this user
    :>jsonarr user: Username of the applicant
    :>jsonarr note: note given by the applicant
    :>jsonarr status: status value.  Possible values are ``Denied``,
        ``Approved``, ``Pending``, ``Member Removed`` and ``Member Left``
    :>jsonarr id: application ID
    :>jsonarr created: creation date/time
    :>jsonarr modified: last modified date/time
    :>jsonarr resource_uri: API URI for the application

Get details on a single application
+++++++++++++++++++++++++++++++++++

.. http:get:: /api/teams/[team-slug]/applications/[application-id]/:

    Returns the same data as one entry from the listing endpoint.

Approve/Deny an application
+++++++++++++++++++++++++++

.. http:put:: /api/teams/[team-slug]/applications/[application-id]/

    :<json status: ``Denied`` to deny the application and ``Approved`` to
        approve it.
"""

from __future__ import absolute_import
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework import serializers
from rest_framework import status
from rest_framework import viewsets
from rest_framework.reverse import reverse

from api.pagination import AmaraPaginationMixin
from auth.models import CustomUser as User
from teams.models import (Team, TeamMember, Project, Task, TeamVideo,
                          Application)
import messages.tasks
import teams.permissions as team_permissions
import videos.tasks

def timestamp_to_datetime(timestamp):
    return datetime.fromtimestamp(int(timestamp))

class MappedChoiceField(serializers.ChoiceField):
    """Choice field that maps internal values to choices."""

    default_error_messages = {
        'unknown-choice': "Unknown choice: {choice}",
    }

    def __init__(self, choices, *args, **kwargs):
        self.map = dict((value, choice) for value, choice in choices)
        self.rmap = dict((choice, value) for value, choice in choices)
        super(MappedChoiceField, self).__init__(self.rmap.keys(), *args,
                                                **kwargs)

    def to_internal_value(self, choice):
        try:
            return self.rmap[choice]
        except KeyError:
            self.fail('unknown-choice', choice=choice)

    def to_representation(self, value):
        return self.map[value]

class TeamSerializer(serializers.ModelSerializer):
    # Handle mapping internal values for membership/video policy to the values
    # we use in the api (currently the english display name)
    MEMBERSHIP_POLICY_CHOICES = (
        (Team.OPEN, u'Open'),
        (Team.APPLICATION, u'Application'),
        (Team.INVITATION_BY_ALL, u'Invitation by any team member'),
        (Team.INVITATION_BY_MANAGER, u'Invitation by manager'),
        (Team.INVITATION_BY_ADMIN, u'Invitation by admin'),
    )
    VIDEO_POLICY_CHOICES = (
        (Team.VP_MEMBER, u'Any team member'),
        (Team.VP_MANAGER, u'Managers and admins'),
        (Team.VP_ADMIN, u'Admins only'),
    )
    membership_policy = MappedChoiceField(
        MEMBERSHIP_POLICY_CHOICES, required=False,
        default=Team._meta.get_field('membership_policy').get_default())
    video_policy = MappedChoiceField(
        VIDEO_POLICY_CHOICES, required=False,
        default=Team._meta.get_field('video_policy').get_default())

    class Meta:
        model = Team
        fields = ('name', 'slug', 'description', 'is_visible',
                  'membership_policy', 'video_policy')

class TeamUpdateSerializer(TeamSerializer):
    name = serializers.CharField(required=False)
    slug = serializers.SlugField(required=False)

class TeamViewSet(AmaraPaginationMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    lookup_field = 'slug'
    paginate_by = 20

    def get_queryset(self):
        return Team.objects.for_user(self.request.user)

    def get_serializer_class(self):
        if 'slug' in self.kwargs:
            return TeamUpdateSerializer
        else:
            return TeamSerializer

    def perform_create(self, serializer):
        if not team_permissions.can_create_team(self.request.user):
            raise PermissionDenied()
        serializer.save()

    def perform_update(self, serializer):
        if not team_permissions.can_change_team_settings(serializer.instance,
                                                         self.request.user):
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if not team_permissions.can_delete_team(instance, self.request.user):
            raise PermissionDenied()
        instance.delete()

class TeamMemberSerializer(serializers.Serializer):
    default_error_messages = {
        'user-does-not-exist': "User does not exist: {username}",
        'user-already-member': "User is already a team member",
    }

    ROLE_CHOICES = (
         TeamMember.ROLE_OWNER,
         TeamMember.ROLE_ADMIN,
         TeamMember.ROLE_MANAGER,
         TeamMember.ROLE_CONTRIBUTOR,
    )

    username = serializers.CharField(source='user.username')
    role = serializers.ChoiceField(ROLE_CHOICES)

    def validate_username(self, username):
        try:
            self.user = User.objects.get(username=username)
            return username
        except User.DoesNotExist:
            self.fail('user-does-not-exist', username=username)

    def create(self, validated_data):
        try:
            return self.context['team'].members.create(
                user=self.user,
                role=validated_data['role'],
            )
        except IntegrityError:
            self.fail('user-already-member')

class TeamMemberUpdateSerializer(TeamMemberSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    def update(self, instance, validated_data):
        instance.role = validated_data['role']
        instance.save()
        return instance

class TeamSubviewMixin(object):
    def initial(self, request, *args, **kwargs):
        super(TeamSubviewMixin, self).initial(request, *args, **kwargs)
        try:
            self.team = Team.objects.get(slug=kwargs['team_slug'])
        except Team.DoesNotExist:
            self.team = None
            raise Http404

    def get_serializer_context(self):
        return {
            'team': self.team,
            'user': self.request.user,
            'request': self.request,
        }

class TeamSubview(TeamSubviewMixin, viewsets.ModelViewSet):
    pass

class TeamMemberViewSet(TeamSubview):
    lookup_field = 'username'

    def get_serializer_class(self):
        if 'username' in self.kwargs:
            return TeamMemberUpdateSerializer
        else:
            return TeamMemberSerializer

    def get_queryset(self):
        if not self.team.user_is_member(self.request.user):
            raise PermissionDenied()
        return self.team.members.all().select_related("user")

    def get_object(self):
        if not self.team.user_is_member(self.request.user):
            raise PermissionDenied()
        member = get_object_or_404(self.team.members,
                                   user__username=self.kwargs['username'])
        return member

    def perform_create(self, serializer):
        if not team_permissions.can_add_member(self.team, self.request.user):
            raise PermissionDenied()
        serializer.save()

    def perform_update(self, serializer):
        if not team_permissions.can_assign_role(
            self.team, self.request.user, serializer.validated_data['role'],
            serializer.instance.user):
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, member):
        if not team_permissions.can_remove_member(self.team,
                                                  self.request.user):
            raise PermissionDenied()
        if member.role == TeamMember.ROLE_OWNER:
            raise serializers.ValidationError("Can't remove team owner")
        member.delete()

class SafeTeamMemberSerializer(TeamMemberSerializer):
    email = serializers.EmailField(required=False, write_only=True)

    default_error_messages = {
        'email-required': "Email required to create user",
    }

    def validate_username(self, username):
        return username

    def validate(self, attrs):
        try:
            self.user = User.objects.get(username=attrs['user']['username'])
        except User.DoesNotExist:
            if 'email' not in attrs:
                self.fail('email-required')
            self.user = User.objects.create(
                username=attrs['user']['username'],
                email=attrs['email'])
        return attrs

    def create(self, validated_data):
        team = self.context['team']
        if team.members.filter(user=self.user).exists():
            self.fail('user-already-member')
        invite = team.invitations.create(user=self.user,
                                         author=self.context['user'],
                                         role=validated_data['role'])
        messages.tasks.team_invitation_sent.delay(invite.id)
        # return an unsaved TeamMember for serialization purposes
        return TeamMember(user=self.user, team=team,
                          role=validated_data['role'])

class SafeTeamMemberViewSet(TeamMemberViewSet):
    def get_serializer_class(self):
        if 'username' in self.kwargs:
            return TeamMemberUpdateSerializer
        else:
            return SafeTeamMemberSerializer

    def create(self, request, *args, **kwargs):
        response = super(SafeTeamMemberViewSet, self).create(request, *args,
                                                             **kwargs)
        # use 202 status code since we invited the user instead of created a
        # membership
        response.status_code = status.HTTP_202_ACCEPTED
        return response

class ProjectSerializer(serializers.ModelSerializer):
    resource_uri = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ('name', 'slug', 'description', 'guidelines',
                  'modified', 'created', 'workflow_enabled', 'resource_uri')
        # Based on the model code, slug can be blank, but this seems bad to
        # allow for API requests
        read_only_fields = ('modified', 'created')
        extra_kwargs = {
            'slug': { 'required': True },
        }

    def get_resource_uri(self, project):
        return reverse('api:projects-detail', kwargs={
            'team_slug': self.context['team'].slug,
            'slug': project.slug,
        }, request=self.context['request'])

    def create(self, validated_data):
        return Project.objects.create(team=self.context['team'],
                                      **validated_data)

class ProjectUpdateSerializer(ProjectSerializer):
    class Meta(ProjectSerializer.Meta):
        extra_kwargs = {
            'name': { 'required': False },
            'slug': { 'required': False },
        }

class ProjectViewSet(TeamSubview):
    lookup_field = 'slug'

    def get_queryset(self):
        if not self.team.user_is_member(self.request.user):
            raise PermissionDenied()
        return Project.objects.for_team(self.team)

    def get_serializer_class(self):
        if 'slug' in self.kwargs:
            return ProjectUpdateSerializer
        else:
            return ProjectSerializer

    def get_object(self):
        if not self.team.user_is_member(self.request.user):
            raise PermissionDenied()
        return super(ProjectViewSet, self).get_object()

    def perform_create(self, serializer):
        if not team_permissions.can_create_project(
            self.request.user, self.team):
            raise PermissionDenied()
        serializer.save()

    def perform_update(self, serializer):
        if not team_permissions.can_edit_project(
            self.team, self.request.user, serializer.instance):
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, project):
        if not team_permissions.can_delete_project(
            self.request.user, self.team, project):
            raise PermissionDenied()
        project.delete()

class TeamVideoField(serializers.Field):
    default_error_messages = {
        'unknown-video': "Unknown video: {video_id}",
    }

    def to_internal_value(self, video_id):
        team = self.context['team']
        try:
            return team.teamvideo_set.get(video__video_id=video_id)
        except TeamVideo.DoesNotExist:
            self.fail('unknown-video', video_id=video_id)

    def to_representation(self, team_video):
        return team_video.video.video_id

class TeamMemberField(serializers.Field):
    default_error_messages = {
        'unknown-member': "Unknown member: {username}",
    }

    def to_internal_value(self, username):
        team = self.context['team']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.fail('unknown-member', username=username)
        if not team.user_is_member(user):
            self.fail('unknown-member', username=username)
        return user

    def to_representation(self, user):
        return user.username

class TaskSerializer(serializers.ModelSerializer):
    resource_uri = serializers.SerializerMethodField()
    video_id = TeamVideoField(source='team_video')
    assignee = TeamMemberField(required=False)
    type = MappedChoiceField(Task.TYPE_CHOICES)
    approved = MappedChoiceField(
        Task.APPROVED_CHOICES, required=False,
        default=Task._meta.get_field('approved').get_default(),
    )

    class Meta:
        model = Task
        fields = (
            'id', 'video_id', 'language', 'type', 'assignee', 'priority',
            'completed', 'approved', 'resource_uri',
        )
        read_only_fields = (
            'completed',
        )

    def get_resource_uri(self, task):
        return reverse('api:tasks-detail', kwargs={
            'team_slug': self.context['team'].slug,
            'id': task.id,
        }, request=self.context['request'])

    def create(self, validated_data):
        validated_data['team'] = self.context['team']
        return super(TaskSerializer, self).create(validated_data)

class TaskUpdateSerializer(TaskSerializer):
    video_id = TeamVideoField(source='team_video', required=False,
                              read_only=True)
    type = MappedChoiceField(Task.TYPE_CHOICES, required=False,
                             read_only=True)
    complete = serializers.BooleanField(required=False)
    send_back = serializers.BooleanField(required=False)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + (
            'complete', 'send_back',
        )

    def update(self, task, validated_data):
        send_back = validated_data.pop('send_back', False)
        complete = validated_data.pop('complete', False)
        self.check_max_tasks(task, validated_data.get('assignee'))
        task = super(TaskUpdateSerializer, self).update(task, validated_data)
        if send_back:
            task.approved = Task.APPROVED_IDS['Rejected']
            self._complete_task(task)
        elif complete:
            task.approved = Task.APPROVED_IDS['Approved']
            self._complete_task(task)
        return task

    def check_max_tasks(self, task, assignee):
        if not assignee:
            return
        member = self.context['team'].get_member(assignee)
        if member.has_max_tasks() and task.assignee != assignee:
            raise PermissionDenied()

    def _complete_task(self, task):
        if task.assignee is None:
            task.assignee = self.context['user']
        task.complete()

class TaskViewSet(TeamSubview):
    lookup_field = 'id'

    def get_queryset(self):
        if not self.team.user_is_member(self.request.user):
            raise PermissionDenied()
        return (self.order_queryset(self.team.task_set.all())
                .select_related('team_video__video', 'assignee'))

    def order_queryset(self, qs):
        valid_orderings = set(['created', 'priority', 'type'])
        reverse_orderings = set('-' + o for o in valid_orderings)
        order_by = self.request.query_params.get('order_by')
        if order_by in valid_orderings.union(reverse_orderings):
            return qs.order_by(order_by)
        else:
            return qs

    def filter_queryset(self, qs):
        params = self.request.query_params
        if 'assignee' in params:
            qs = qs.filter(assignee__username=params['assignee'])
        if 'priority' in params:
            qs = qs.filter(priority=params['priority'])
        if 'language' in params:
            qs = qs.filter(language=params['language'])
        if 'type' in params:
            try:
                qs = qs.filter(type=Task.TYPE_IDS[params['type']])
            except KeyError:
                qs = qs.none()
        if 'video_id' in params:
            qs = qs.filter(team_video__video__video_id=params['video_id'])
        if 'completed' in params:
            qs = qs.filter(completed__isnull=False)
        if 'completed-after' in params:
            try:
                qs = qs.filter(completed__gte=timestamp_to_datetime(
                    params['completed-after']))
            except (TypeError, ValueError):
                qs = qs.none()
        if 'completed-before' in params:
            try:
                qs = qs.filter(completed__lt=timestamp_to_datetime(
                    params['completed-before']))
            except (TypeError, ValueError):
                qs = qs.none()
        if 'open' in params:
            qs = qs.filter(completed__isnull=True)
        return qs

    def get_serializer_class(self):
        if 'id' not in self.kwargs:
            return TaskSerializer
        else:
            return TaskUpdateSerializer

    def perform_create(self, serializer):
        team_video = serializer.validated_data['team_video']
        if not team_permissions.can_assign_tasks(
            self.team, self.request.user, team_video.project):
            raise PermissionDenied()
        self.task_was_assigned = False
        task = serializer.save()
        self._post_save(task)

    def perform_update(self, serializer):
        team_video = serializer.instance.team_video
        if not team_permissions.can_assign_tasks(
            self.team, self.request.user, team_video.project):
            raise PermissionDenied()
        self.task_was_assigned = serializer.instance.assignee is not None
        task = serializer.save()
        self._post_save(task)

    def perform_destroy(self, instance):
        if not team_permissions.can_delete_tasks(
            self.team, self.request.user, instance.team_video.project,
            instance.language):
            raise PermissionDenied()
        instance.delete()

    def _post_save(self, task):
        if task.assignee and not self.task_was_assigned:
            messages.tasks.team_task_assigned.delay(task.id)
            task.set_expiration()
            task.save()
        videos.tasks.video_changed_tasks.delay(task.team_video.video_id)

class ApplicationSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    status = MappedChoiceField(
        Application.STATUSES,
        default=Application._meta.get_field('status').get_default())
    resource_uri = serializers.SerializerMethodField()

    default_error_messages = {
        'invalid-status-choice': "Unknown status: {status}",
        'not-pending': "Application not pending",
    }

    def get_resource_uri(self, application):
        return reverse('api:team-application-detail', kwargs={
            'team_slug': self.context['team'].slug,
            'id': application.id,
        }, request=self.context['request'])

    class Meta:
        model = Application
        fields = (
            'id', 'status', 'user', 'note', 'created', 'modified',
            'resource_uri',
        )
        read_only_fields = (
            'id', 'note', 'created', 'modified',
        )

    def validate_status(self, status):
        if status not in (Application.STATUS_APPROVED,
                          Application.STATUS_DENIED):
            self.fail('invalid-status-choice', status=status)
        return status

    def update(self, instance, validated_data):
        if instance.status != Application.STATUS_PENDING:
            self.fail('not-pending')
        if validated_data['status'] == Application.STATUS_APPROVED:
            instance.approve(self.context['user'], 'API')
        elif validated_data['status'] == Application.STATUS_DENIED:
            instance.deny(self.context['user'], 'API')
        return instance

class TeamApplicationViewSet(TeamSubviewMixin,
                             AmaraPaginationMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    serializer_class = ApplicationSerializer
    lookup_field = 'id'
    paginate_by = 20

    def get_queryset(self):
        self.check_read_permission()
        if self.team.membership_policy != Team.APPLICATION:
            return self.team.applications.none()
        return self.team.applications.all().select_related('user')

    def get_object(self):
        self.check_read_permission()
        return super(TeamApplicationViewSet, self).get_object()

    def check_read_permission(self):
        if not team_permissions.can_invite(self.team, self.request.user):
            raise PermissionDenied()

    def filter_queryset(self, qs):
        params = self.request.query_params
        if 'user' in params:
            qs = qs.filter(user__username=params['user'])
        if 'status' in params:
            try:
                status_id = Application.STATUSES_IDS[params['status']]
                qs = qs.filter(status=status_id)
            except KeyError:
                qs = qs.none()
        if 'after' in params:
            qs = qs.filter(created__gte=timestamp_to_datetime(params['after']))
        if 'before' in params:
            qs = qs.filter(created__lt=timestamp_to_datetime(params['before']))
        return qs
