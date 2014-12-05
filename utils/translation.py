# -*- coding: utf-8 -*-
import time

from django.conf import settings
from django.core.cache import cache
from django.utils import simplejson as json
from django.utils.http import cookie_date
from django.utils.translation import (
    get_language, get_language_info, ugettext as _
)
from django.utils.translation.trans_real import parse_accept_lang_header

from unilangs import get_language_name_mapping, LanguageCode

# A set of all language codes we support.
_supported_languages_map = get_language_name_mapping('unisubs')
_all_languages_map = get_language_name_mapping('internal')
SUPPORTED_LANGUAGE_CODES = set(_supported_languages_map.keys())
ALL_LANGUAGE_CODES = set(_all_languages_map.keys())

SUPPORTED_LANGUAGE_CHOICES = list(sorted(_supported_languages_map.items(),
                                         key=lambda c: c[1]))
ALL_LANGUAGE_CHOICES = list(sorted(_all_languages_map.items(),
                                   key=lambda c: c[1]))

def _only_supported_languages(language_codes):
    """Filter the given list of language codes to contain only codes we support."""

    # TODO: Figure out the codec issue here.
    return [code for code in language_codes if code in SUPPORTED_LANGUAGE_CODES]


_get_language_choices_cache = {}
def get_language_choices(with_empty=False, with_any=False):
    """Return a list of language code choices labeled appropriately."""

    language_code = get_language()
    try:
        languages = _get_language_choices_cache[language_code]
    except KeyError:
        languages = [
            (code, _(name))
            for (code, name) in _supported_languages_map.items()
        ]
        languages.sort(key=lambda item: item[1])
        _get_language_choices_cache[language_code] = languages

    # make a copy of languages before we alter it
    languages = list(languages)
    if with_any:
        languages.insert(0, ('', _('--- Any Language ---')))
    if with_empty:
        languages.insert(0, ('', '---------'))
    return languages

def get_language_choices_as_dicts(with_empty=False):
    """Return a list of language code choices labeled appropriately."""
    return [
        {'code': code, 'name': name}
        for (code, name) in get_language_choices(with_empty)
    ]

def get_language_label(code):
    """Return the translated, human-readable label for the given language code."""
    lc = LanguageCode(code, 'internal')
    return u'%s' % _(lc.name())


def get_user_languages_from_request(request, readable=False, guess=True):
    """Return a list of our best guess at languages that request.user speaks."""
    languages = []

    if request.user.is_authenticated():
        languages = request.user.get_languages()

    if guess and not languages:
        languages = languages_from_request(request)

    if readable:
        return map(get_language_label, _only_supported_languages(languages))
    else:
        return _only_supported_languages(languages)

def set_user_languages_to_cookie(response, languages):
    max_age = 60*60*24
    response.set_cookie(
        settings.USER_LANGUAGES_COOKIE_NAME,
        json.dumps(languages),
        max_age=max_age,
        expires=cookie_date(time.time() + max_age))

def get_user_languages_from_cookie(request):
    try:
        langs = json.loads(request.COOKIES.get(settings.USER_LANGUAGES_COOKIE_NAME, '[]'))
        return _only_supported_languages(langs)
    except (TypeError, ValueError):
        return []


def languages_from_request(request):
    languages = []

    for l in get_user_languages_from_cookie(request):
        if not l in languages:
            languages.append(l)

    if not languages:
        trans_lang = get_language()
        if not trans_lang in languages:
            languages.append(trans_lang)

        if hasattr(request, 'session'):
            lang_code = request.session.get('django_language', None)
            if lang_code is not None and not lang_code in languages:
                languages.append(lang_code)

        cookie_lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if cookie_lang_code and not cookie_lang_code in languages:
            languages.append(cookie_lang_code)

        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for lang, val in parse_accept_lang_header(accept):
            if lang and lang != '*' and not lang in languages:
                languages.append(lang)

    return _only_supported_languages(languages)

def languages_with_labels(langs):
    """Return a dict of language codes to language labels for the given seq of codes.

    These codes must be in the internal unisubs format.

    The labels will be in the standard label format.

    """
    return dict([code, get_language_label(code)] for code in langs)

# This handles RTL info for languages where get_language_info() is not correct
_RTL_OVERRIDE_MAP = {
    # there are languages on our system that are not on django.
    'arq': True,
    'pnb': True,
    # Forcing Azerbaijani to be a left-to-right language.
    # For: https://unisubs.sifterapp.com/projects/12298/issues/753035/comments 
    'az': False,
    # Force Urdu to be RTL (see gh-722)
    'ur': True,
    # Force Uyghur to be RTL (see gh-1411)
    'ug': True,
    # Force Aramaic to be RTL (gh-1073)
    'arc': True,
}

def is_rtl(language_code):
    if language_code in _RTL_OVERRIDE_MAP:
        return _RTL_OVERRIDE_MAP[language_code]
    try:
        return get_language_info(language_code)['bidi']
    except KeyError:
        return False
