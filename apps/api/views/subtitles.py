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

from __future__ import absolute_import

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from videos.models import Video
from subtitles import workflows
from subtitles.exceptions import ActionError

class ActionsSerializer(serializers.Serializer):
    action = serializers.CharField(source='name')
    label = serializers.CharField(read_only=True)
    complete = serializers.BooleanField(read_only=True)

class Actions(APIView):
    def get_serializer(self, **kwargs):
        return ActionsSerializer(**kwargs)

    def get(self, request, video_id, language_code, format=None):
        video = get_object_or_404(Video, video_id=video_id)
        workflow = workflows.get_workflow(video)
        action_list = workflow.get_actions(request.user, language_code)
        serializer = ActionsSerializer(action_list, many=True)
        return Response(serializer.data)

    def post(self, request, video_id, language_code, format=None):
        try:
            action = request.DATA['action']
        except KeyError:
            return Response('no action', status=status.HTTP_400_BAD_REQUEST)
        video = get_object_or_404(Video, video_id=video_id)
        workflow = workflows.get_workflow(video)
        try:
            workflow.perform_action(request.user, language_code, action)
        except (ActionError, LookupError), e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response('')

class NotesSerializer(serializers.Serializer):
    user = serializers.CharField(source='user.username', read_only=True)
    created = serializers.DateTimeField(read_only=True)
    body = serializers.CharField()

    def create(self, validated_data):
        return self.context['editor_notes'].post(
            self.context['user'], validated_data['body'])

class NotesList(generics.ListCreateAPIView):
    serializer_class = NotesSerializer

    @csrf_exempt
    def dispatch(self, request, **kwargs):
        self.editor_notes = self.get_editor_notes(**kwargs)
        return generics.ListCreateAPIView.dispatch(self, request, **kwargs)

    def get_editor_notes(self, **kwargs):
        video = get_object_or_404(Video, video_id=kwargs['video_id'])
        workflow = workflows.get_workflow(video)
        return workflow.get_editor_notes(kwargs['language_code'])

    def get_queryset(self):
        return self.editor_notes.notes

    def get_serializer_context(self):
        return {
            'editor_notes': self.editor_notes,
            'user': self.request.user,
        }
