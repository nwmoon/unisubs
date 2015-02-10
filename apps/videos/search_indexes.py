import datetime

from django.conf import settings
from django.template import loader, Context
from haystack import site
from haystack.indexes import *
from haystack.models import SearchResult
from haystack.query import SearchQuerySet
from haystack.exceptions import AlreadyRegistered

from subtitles.models import SubtitleLanguage
from utils.celery_search_index import CelerySearchIndex
from videos.models import Video


class VideoIndex(CelerySearchIndex):
    text = CharField(document=True)
    title = CharField(boost=2)
    languages = MultiValueField(faceted=True)
    video_language = CharField(faceted=True)
    languages_count = IntegerField()
    video_id = CharField(model_attr='video_id', indexed=False)
    thumbnail_url = CharField(model_attr='get_thumbnail', indexed=False)
    small_thumbnail = CharField(model_attr='get_small_thumbnail', indexed=False)
    created = DateTimeField(model_attr='created')
    edited = DateTimeField(model_attr='edited')
    subtitles_fetched_count = IntegerField()
    widget_views_count = IntegerField()
    comments_count = IntegerField()

    contributors_count = IntegerField()
    activity_count = IntegerField()
    featured = DateTimeField(model_attr='featured', null=True)

    today_views = IntegerField()
    week_views = IntegerField()
    month_views = IntegerField()
    year_views = IntegerField()
    total_views = IntegerField()

    # non public videos won't show up in any of the site's listing
    # not even for the owner
    is_public = BooleanField()

    IN_ROW = getattr(settings, 'VIDEO_IN_ROW', 6)

    def prepare_text(self, obj):
        t = loader.get_template('search/indexes/videos/video_text.txt')
        return t.render(Context({'object': obj}))

    def prepare_title_display(self, obj):
        return obj.title_display

    def prepare_activity_count(self, obj):
        return obj.action_set.count()

    def prepare(self, obj):
        obj.prefetch_languages(with_public_tips=True, with_private_tips=True)
        self.prepared_data = super(VideoIndex, self).prepare(obj)

        languages = [l for l in obj.all_subtitle_languages()
                     if l.get_tip() is not None]
        followers = obj.newsubtitlelanguage_set.all().values("followers").distinct().count()

        self.prepared_data['languages_count'] = len(languages)
        self.prepared_data['video_language'] = obj.primary_audio_language_code
        self.prepared_data['languages'] = [language.language_code for language in languages]
        self.prepared_data['contributors_count'] = followers
        self.prepared_data['title'] = obj.title_display().strip()
        self.prepared_data['is_public'] = obj.is_public

        return self.prepared_data

    def _setup_save(self, model):
        pass

    def _teardown_save(self, model):
        pass

    def index_queryset(self):
        return self.model.objects.order_by('-id')

    @classmethod
    def public(self):
        """
        All regular queries should go through this method, as it makes
        sure we never display videos that should be hidden
        """
        return SearchQuerySet().result_class(VideoSearchResult) \
            .models(Video).filter(is_public=True)

    @classmethod
    def get_featured_videos(cls):
        return  VideoIndex.public().filter(featured__gt=datetime.datetime(datetime.MINYEAR, 1, 1)) \
            .order_by('-featured')

    @classmethod
    def get_popular_videos(cls, sort='-week_views'):
        return  VideoIndex.public().order_by(sort)

    @classmethod
    def get_latest_videos(cls):
        return VideoIndex.public().order_by('-created')

class VideoSearchResult(SearchResult):
    title_for_url = Video.__dict__['title_for_url']
    get_absolute_url = Video.__dict__['_get_absolute_url']

    def __unicode__(self):
        title = self.title

        if len(title) > 60:
            title = title[:60]+'...'

        return title

try:
    site.register(Video, VideoIndex)
except AlreadyRegistered:
    # i hate python imports with all my will.
    # i hope they die.
    pass
