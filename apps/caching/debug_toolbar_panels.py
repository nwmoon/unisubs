from __future__ import absolute_import

import collections
import contextlib
import functools
import math
import time
import traceback

from debug_toolbar.panels import Panel
from debug_toolbar.utils import (tidy_stacktrace, render_stacktrace,
                                 get_stack)
from django.core.cache import cache
from django.utils.translation import ungettext


CallInfo = collections.namedtuple('CallInfo', 'name keys time stacktrace')

class CachePatcher(object):
    """A small class used to track cache calls."""

    def __init__(self):
        self.active = False
        self.methods_to_patch = [
            'get', 'get_many',
            'set', 'set_many',
            'add',
            'delete', 'delete_many',
            'incr', 'decr',
        ]
        self.orig_methods = {}

    @property
    def call_count(self):
        return len(self.calls)

    def get_counts(self):
        counts = collections.defaultdict(int)
        for call in self.calls:
            counts[call.name] += 1
        return [
            (name, counts[name])
            for name in self.methods_to_patch
        ]

    def start(self):
        if self.active:
            return
        self.calls = []
        self.total_time = 0.0
        for name in self.methods_to_patch:
            if name == 'set_many':
                wrapper = self.wrap_set_many
            elif name.endswith('_many'):
                wrapper = self.wrap_multi_key_method
            else:
                wrapper = self.wrap_single_key_method
            self.orig_methods[name] = getattr(cache, name)
            setattr(cache, name, functools.partial(wrapper, name))
        self.active = True

    def stop(self):
        if not self.active:
            return
        for name in self.methods_to_patch:
            setattr(cache, name, self.orig_methods.pop(name))
        self.active = False

    @contextlib.contextmanager
    def record_call(self, name, keys):
        start = time.time()
        yield
        call_time = time.time() - start
        # trim the stack to remove our wrapper methods
        stack = get_stack()[3:]
        trace = render_stacktrace(tidy_stacktrace(reversed(stack)))
        self.calls.append(CallInfo(name, keys, call_time, trace))
        self.total_time += call_time

    def wrap_single_key_method(self, name, key, *args, **kwargs):
        with self.record_call(name, [key]):
            return self.orig_methods[name](key, *args, **kwargs)

    def wrap_multi_key_method(self, name, keys, *args, **kwargs):
        with self.record_call(name, keys):
            return self.orig_methods[name](keys, *args, **kwargs)


    def wrap_set_many(self, name, data, *args, **kwargs):
        with self.record_call(name, data.keys()):
            return self.orig_methods[name](data, *args, **kwargs)

class CachePanel(Panel):
    """
    Panel that displays the cache statistics.
    """
    template = 'caching/_debug_toolbar_panel.html'

    def __init__(self, *args, **kwargs):
        super(CachePanel, self).__init__(*args, **kwargs)
        self.patcher = CachePatcher()

    # Implement the Panel API

    nav_title = "Cache"

    @property
    def nav_subtitle(self):
        cache_calls = len(self.patcher.calls)
        return ungettext("%(cache_calls)d call in %(time).4fs",
                         "%(cache_calls)d calls in %(time).4fs",
                         cache_calls) % {
                             'cache_calls': self.patcher.call_count,
                             'time': self.patcher.total_time}

    @property
    def title(self):
        return "Cache calls"

    def enable_instrumentation(self):
        self.patcher.start()

    def disable_instrumentation(self):
        self.patcher.stop()

    def process_response(self, request, response):
        self.record_stats({
            'total_calls': self.patcher.call_count,
            'total_time': math.floor(self.patcher.total_time * 1000),
            'calls': self.patcher.calls,
            'counts': self.patcher.get_counts(),
        })
