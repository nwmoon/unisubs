# Amara, universalsubtitles.org
# 
# Copyright (C) 2014 Participatory Culture Foundation
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

"""periodic_task_settings -- settings for celery periodic tasks."""

from datetime import timedelta

from celery.schedules import crontab
from kombu import Exchange, Queue

CELERY_QUEUES = (
    Queue('celery', routing_key='celery'),
    Queue('feeds', routing_key='feeds'),
)

CELERYBEAT_SCHEDULE = {
    'gauge-auth': {
        'schedule': timedelta(seconds=300),
        'task': 'auth.tasks.gauge_auth',
    },
    'gauge-comments': {
        'task': 'comments.tasks.gauge_comments',
        'schedule': timedelta(seconds=300),
    },
    'gauge-statistics': {
        'task': 'statistic.tasks.gauge_statistic',
        'schedule': timedelta(seconds=300),
    },
    'migrate-hit-counts': {
        'task': 'statistic.tasks.migrate_hit_counts',
        'schedule': crontab(hour=1, minute=0),
    },
    'expire-tasks': {
        'task': 'teams.tasks.expire_tasks',
        'schedule': crontab(minute=0, hour=7),
    },
    'add_videos_notification_daily': {
        'task': 'teams.tasks.add_videos_notification_daily',
        'schedule': crontab(minute=0, hour=23),
    },
    'add_videos_notification_hourly': {
        'task': 'teams.tasks.add_videos_notification_hourly',
        'schedule': crontab(minute=0),
    },
    'gauge_teams': {
        'task': 'teams.tasks.gauge_teams',
        'schedule': timedelta(seconds=300),
    },
    'cleanup_videos': {
        'task': 'videos.tasks.cleanup',
        'schedule': crontab(hour=3, day_of_week=1),
    },
    'update_feeds': {
        'task': 'videos.tasks.update_from_feed',
        'schedule': crontab(minute=0),
    },
    'gauge_videos': {
        'task': 'videos.tasks.gauge_videos',
        'schedule': timedelta(seconds=300),
    },
    'gauge_videos_long': {
        'task': 'videos.tasks.gauge_videos_long',
        'schedule': timedelta(days=1),
    },
    'gauge_billing_records': {
        'task': 'videos.tasks.gauge_billing_records',
        'schedule': timedelta(seconds=60),
    },
}

__all__ = ['CELERYBEAT_SCHEDULE', 'CELERY_QUEUES', ]
