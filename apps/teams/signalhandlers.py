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

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from auth.models import CustomUser as User
from teams.models import TeamVideo, TeamMember, MembershipNarrowing
from teams.signals import api_teamvideo_new
from videos.signals import feed_imported

@receiver(feed_imported)
def on_feed_imported(signal, sender, new_videos, **kwargs):
    if sender.team is None:
        return
    for video in new_videos:
        tv = TeamVideo.objects.create(
            video=video, team=sender.team, added_by=sender.user,
            description=video.description)
        api_teamvideo_new.send(tv)

@receiver(post_save, sender=TeamMember)
@receiver(post_delete, sender=TeamMember)
def on_team_member_change(sender, instance, **kwargs):
    User.cache.invalidate_by_pk(instance.user_id)

@receiver(post_save, sender=MembershipNarrowing)
@receiver(post_delete, sender=MembershipNarrowing)
def on_membership_narrowing_change(sender, instance, **kwargs):
    try:
        User.cache.invalidate_by_pk(instance.member.user_id)
    except TeamMember.DoesNotExist:
        pass
