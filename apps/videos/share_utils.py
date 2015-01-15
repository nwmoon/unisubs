from django.utils.http import urlencode
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from utils.text import fmt
import widget

def domain():
    return Site.objects.get_current().domain
    
def make_facebook_url(page_url, msg):
    title = u'%s: %s' % (msg, page_url)
    url = "http://www.facebook.com/sharer.php?%s"
    url_param = urlencode({'u': page_url, 't': title})
    return url % url_param

def make_twitter_url(page_url, message):
    url = "http://twitter.com/share/?%s"
    url_param = urlencode({'text': message, 'url': page_url})
    return url % url_param

def make_email_url(message):
    url = reverse('videos:email_friend')
    return "%s?%s" % (url, urlencode({'text': message}))

def share_panel_context(facebook_url, twitter_url, embed_params, email_url,
                         permalink):
    return {
        "share_panel_facebook_url": facebook_url,
        "share_panel_twitter_url": twitter_url,
        "share_panel_email_url": email_url,
        "share_panel_permalink": permalink,
    }

def share_panel_context_for_video(video):
    page_url = reverse('videos:video', kwargs={'video_id':video.video_id})
    abs_page_url = "http://{0}{1}".format(domain(), page_url)
    
    if video.latest_version() is not None:
        msg = _(u"Just found a version of this video with subtitles")
    else:
        msg = _("Check out this video and help make subtitles")

    email_message = _(u"Hey-- check out this video %(video_title)s and help make subtitles: %(url)s")
    email_message = fmt(email_message,
                        video_title=video.title_display(),
                        url=abs_page_url)
        
    return share_panel_context(
        make_facebook_url(abs_page_url, msg),
        make_twitter_url(abs_page_url, msg), 
        { 'video_url': video.get_video_url() },
        make_email_url(email_message),
        abs_page_url
    )

def add_share_panel_context_for_history(context, video, language=None):
    page_url = language.get_absolute_url() if language else video.get_absolute_url()
    abs_page_url = "http://{0}{1}".format(domain(), page_url)
    
    msg = _(u"%(language)s subtitles for %(video)s:") % {
        'language': language,
        'video':video.title_display(),
    }
    
    email_message = _(u"Hey-- just found %(language)s subtitles for %(video_title)s: %(url)s")
    email_message = fmt(email_message,
                        video_title=video.title_display(),
                        language=language,
                        url=abs_page_url)

    if language:
        base_state = {'language': language.language_code}
    else:
        base_state = {}
    
    context.update(share_panel_context(
        make_facebook_url(abs_page_url, msg),
        make_twitter_url(abs_page_url, msg),
        { 'video_url': video.get_video_url(), 'base_state': base_state },
        make_email_url(email_message),
        abs_page_url
    ))
