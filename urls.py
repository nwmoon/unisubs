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

from django import http
from django.conf.urls import include, patterns, url
from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.template import RequestContext, loader
from django.views.generic.base import TemplateView, RedirectView
from sitemaps import sitemaps, sitemap_view, sitemap_index
from socialauth.models import AuthMeta, OpenidProfile
from django.views.decorators.clickjacking import xframe_options_exempt

import optionalapps
from utils.genericviews import JSTemplateView

admin.autodiscover()

# these really should be unregistred but while in development the dev server
# might have not registred yet, so we silence this exception
try:
    admin.site.unregister([AuthMeta, OpenidProfile])
except admin.sites.NotRegistered:
    pass

# Monkeypatch the Celery admin to show a column for task run time in the list view.
from djcelery.admin import TaskMonitor
from djcelery.models import TaskState


admin.site.unregister([TaskState])
TaskMonitor.list_display += ('runtime',)
admin.site.register(TaskState, TaskMonitor)

js_info_dict = {
    'packages': ('unisubs'),
}

# run monkey patch django
from utils import urlvalidator
urlpatterns = patterns('',
    url('^500/$', TemplateView.as_view(template_name='500.html')),
    url('^404/$', TemplateView.as_view(template_name='404.html')),
    url('^robots.txt$', TemplateView.as_view(template_name='robots.txt')),
    url(r'^crossdomain.xml$',
        'crossdomain_views.root_crossdomain'),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict,
        name='js_i18n_catalog'),
    url(r'^$',
        'videos.views.index'),
    url(r'^comments/',
        include('comments.urls', namespace='comments')),
    url(r'^messages/',
        include('messages.urls', namespace='messages')),
    # TODO: Not sure what this is.  It's breaking the app under Django 1.4
    # url(r'^pcf-targetter/',
    #     include('targetter.urls', namespace='targetter')),
    url(r'^logout/',
        'django.contrib.auth.views.logout', name='logout'),
    url(r'^admin/billing/$', 'teams.views.billing', name='billing'),
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset',
        name='password_reset'),
    url(r'^password_reset/done/$',
        'django.contrib.auth.views.password_reset_done'),
    url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm'),
    url(r'^reset/done/$',
        'django.contrib.auth.views.password_reset_complete'),
    url(r'^socialauth/',
        include('socialauth.urls')),
    url(r'^admin/',
        include(admin.site.urls)),
    url(r'^subtitles/',
        include('subtitles.urls', namespace='subtitles')),
    url(r'^embed(?P<version_no>\d+)?.js$', 'widget.views.embed',
        name="widget-embed"),
    url(r'^widget_demo/$',
        'widget.views.widget_demo'),
    url(r'^widget_public_demo/$',
        'widget.views.widget_public_demo'),
    url(r'^onsite_widget/$',
        'widget.views.onsite_widget', name='onsite_widget'),
    url(r'^onsite_widget_resume/$', 'widget.views.onsite_widget_resume',
        name='onsite_widget_resume'),
    url(r'^widget/', include('widget.urls', namespace='widget',
        app_name='widget')),
    url(r'^jsdemo/(\w+)',
        'jsdemo.views.jsdemo'),
    url(r'^search/',
        include('search.urls', 'search')),
    url(r'^community$',
        TemplateView.as_view(template_name='community.html'),
        name='community'),
    url(r'^enterprise/[\w-]*$',
        TemplateView.as_view(template_name='enterprise.html'),
        name='enterprise_page'),
    url(r'^dfxp-wrapper-test/$',
        TemplateView.as_view(template_name='dfxp-wrapper-test.html'),
        name='dfxp-wrapper-test'),
    url(r'^embedder/$', TemplateView.as_view(template_name='embedder.html'),
        'embedder_page'),
    url(r'^embedder-iframe/$',
        JSTemplateView.as_view(template_name='embedder-iframe.js'),
        name='embedder_iframe'),
    url(r'^embedder-offsite/$',
        TemplateView.as_view(template_name='embedder-offsite.html'),
        name='embedder_page_offsite'),
    url(r'^embedder-widget-iframe/(?P<analytics>.*)', 'widget.views.embedder_widget', name='embedder_widget'),
    url(r'^streaming-transcript/$',
        TemplateView.as_view(template_name='streaming-transcript.html'),
        name='streaming_transcript_demo'),
    url(r'^w3c/p3p.xml$',
        TemplateView.as_view(template_name='p3p.xml')),
    url(r'^w3c/Policies.xml$',
        TemplateView.as_view(template_name='Policies.xml'),
        name='policy_page'),
    url(r'^about$', TemplateView.as_view(template_name='about.html'),
        name='about_page'),
    url(r'^security', TemplateView.as_view(template_name='security.html'),
        name='security_page'),
    url(r'^get-code/$',
        TemplateView.as_view(template_name='embed_page.html'),
        name='get_code_page'),
    url(r'^dmca$',  TemplateView.as_view(template_name='dmca.html'),
        name='dmca_page'),
    url(r'^faq$',  TemplateView.as_view(template_name='faq.html'),
        name='faq_page'),
    url(r'^terms$', RedirectView.as_view(url='http://about.amara.org/tos/')),
    url(r'^opensubtitles2010$',
        TemplateView.as_view(template_name='opensubtitles2010.html'),
        name='opensubtitles2010_page'),
    url(r'^test-ogg$',
        TemplateView.as_view(template_name='alpha-test01-ogg.htm'),
        name='test-ogg-page'),
    url(r'^test-mp4$',
        TemplateView.as_view(template_name='alpha-test01-mp4.htm'),
        name='test-mp4-page'),
    url(r'^sitemap\.xml$', sitemap_index, {'sitemaps': sitemaps},
        name="sitemap-index"),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_view, {'sitemaps': sitemaps},
        name="sitemap"),
    url(r"helpers/",
        include('testhelpers.urls', namespace='helpers')),
    url(r'^videos/', include('videos.urls', namespace='videos',
        app_name='videos')),
    url(r'^teams/', include('teams.urls', namespace='teams',
        app_name='teams')),
    url(r'^profiles/', include('profiles.urls', namespace='profiles',
        app_name='profiles')),
    url(r'^externalsites/', include('externalsites.urls',
                                    namespace='externalsites',
                                    app_name='externalsites')),
    url(r'^media/', include('staticmedia.urls',
                            namespace='staticmedia',
                            app_name='staticmedia')),
    url(r'^auth/', include('auth.urls', namespace='auth', app_name='auth')),
    url(r'^auth/', include('thirdpartyaccounts.urls', namespace='thirdpartyaccounts', app_name='thirdpartyaccounts')),
    url(r'^api/', include('api.urls', namespace='api')),
    ## Video shortlinks
    url(r'^v/(?P<encoded_pk>\w+)/$', 'videos.views.shortlink', name='shortlink')
)

urlpatterns += optionalapps.get_urlpatterns()

try:
    import debug_toolbar
except ImportError:
    pass
else:
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
        (r'^user-data/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    )

def handler500(request):
    return render(request, '500.html', status=500)

def handler403(request):
    return render(request, '403.html', status=403)
