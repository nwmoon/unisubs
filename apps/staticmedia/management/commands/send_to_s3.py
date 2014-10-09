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

from cStringIO import StringIO
import datetime
import email
import gzip
import mimetypes
import time
import optparse
import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from deploy.git_helpers import get_current_commit_hash
from staticmedia import bundles
from staticmedia import oldembedder
from staticmedia import utils

class Command(BaseCommand):
    help = """Upload static media to S3 """

    option_list = BaseCommand.option_list + (
        optparse.make_option('--skip-commit-check', dest='skip_commit_check',
                             action='store_true', default=False,
                             help="Don't check the git commit in commit.py"),
        optparse.make_option('--no-gzip', dest='gzip', action='store_false',
                             default=True, help="Don't gzip files")
    )

    def handle(self, *args, **options):
        self.options = options
        self.setup_s3_subdir()
        self.setup_connection()
        self.build_bundles()
        self.upload_bundles()
        self.upload_static_dir('images')
        self.upload_static_dir('fonts')
        self.upload_static_dir('flowplayer')
        self.upload_app_static_media()
        self.upload_old_embedder()

    def setup_s3_subdir(self):
        self.s3_subdirectory = utils.s3_subdirectory()
        if self.options['skip_commit_check']:
            return
        git_commit = get_current_commit_hash(skip_sanity_checks=True)
        if git_commit != self.s3_subdirectory:
            raise CommandError("The commit in commit.py doesn't match "
                               "the output of git rev-parse HEAD.  "
                               "Run python deploy/create_commit_file.py to "
                               "update commit.py")

    def setup_connection(self):
        self.conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                                 settings.AWS_SECRET_ACCESS_KEY)
        self.bucket = self.conn.get_bucket(settings.STATIC_MEDIA_S3_BUCKET)

    def log_upload(self, key):
        url_base = settings.STATIC_MEDIA_S3_URL_BASE
        if url_base.startswith("//"):
            # add http: for protocol-relative URLs
            url_base = "http:" + url_base
        self.stdout.write("-> %s%s\n" % (url_base, key.name))

    def build_bundles(self):
        self.built_bundles = []
        for bundle_name in settings.MEDIA_BUNDLES.keys():
            bundle = bundles.get_bundle(bundle_name)
            self.stdout.write("building %s\n" % bundle_name)
            self.built_bundles.append((bundle, bundle.build_contents()))

        self.stdout.write("building old embedder\n")
        self.old_embedder_js_code = oldembedder.js_code()

    def upload_bundles(self):
        for bundle, contents in self.built_bundles:
            headers = self.cache_forever_headers()
            headers['Content-Type'] = bundle.mime_type
            upload_path = '%s/%s' % (bundle.bundle_type, bundle.name)
            self.upload_string(upload_path, contents, headers)

    def upload_static_dir(self, subdir):
        directory = os.path.join(settings.STATIC_ROOT, subdir)
        for dirpath, dirs, files in os.walk(directory):
            for filename in files:
                path = os.path.join(dirpath, filename)
                s3_path = os.path.relpath(path, settings.STATIC_ROOT)
                self.upload_file(path, s3_path)

    def upload_app_static_media(self):
        for root_dir in utils.app_static_media_dirs():
            for dirpath, dirs, files in os.walk(root_dir["path"]):
                for filename in files:
                    path = os.path.join(dirpath, filename)
                    s3_path = os.path.join(root_dir["label"], os.path.relpath(path, root_dir["path"]))
                    self.upload_file(path, s3_path)

    def should_gzip(self, content_type):
        if not self.options['gzip']:
            return False
        return (content_type.startswith('text/') or
                content_type == 'application/javascript')

    def compress_string(self, data):
        zbuf = StringIO()
        zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
        zfile.write(data)
        zfile.close()
        return zbuf.getvalue()

    def upload_old_embedder(self):
        # the old embedder is a little different the the others, since we put
        # it in the root directory of our s3 bucket.  This means that we can't
        # cache it forever.  Also we have to pass a slightly weird filename to
        # upload_string()
        headers = self.no_cache_headers()
        self.upload_string("embed.js", self.old_embedder_js_code,
                           self.no_cache_headers(),
                           store_in_s3_subdirectory=False)

    def upload_string(self, filename, content, headers,
                      store_in_s3_subdirectory=True):
        content_type = headers.get('Content-Type', 'application/unknown')
        if self.should_gzip(content_type):
            content = self.compress_string(content)
            headers['Content-Encoding'] = 'gzip'
        key = Key(bucket=self.bucket)
        if store_in_s3_subdirectory:
            key.name = os.path.join(self.s3_subdirectory, filename)
        else:
            key.name = filename
        self.log_upload(key)
        key.set_contents_from_string(content, headers, replace=True,
                                     policy='public-read')

    def upload_file(self, source_file, filename):
        self.upload_string(filename, open(source_file).read(),
                           self.headers_for_file(source_file))

    def http_date(self, time_delta):
        timetuple = (datetime.datetime.now() + time_delta).timetuple()
        return '%s GMT' % email.Utils.formatdate(time.mktime(timetuple))

    def headers_for_file(self, path):
        headers = self.cache_forever_headers()
        content_type, encoding = mimetypes.guess_type(path)
        if content_type is not None:
            headers['Content-Type'] = content_type
        return headers

    def cache_forever_headers(self):
        """Get HTTP headers to cache a resource "forever"

        Note that "forever" doesn't really mean forever, just a very long
        time.  We use the somewhat standard amount of 1-year for this.
        """
        return {
            # HTTP/1.1
            'Cache-Control': 'max-age %d' % (3600 * 24 * 365 * 1),
            # HTTP/1.0
            'Expires': self.http_date(datetime.timedelta(days=365)),
        }

    def no_cache_headers(self):
        """Get HTTP headers to disable caching a resource."""
        return {
            # HTTP/1.1
            'Cache-Control': 'no-store, no-cache, must-revalidate',
            'Pragma': 'no-cache',
            # HTTP/1.0
            'Expires': self.http_date(datetime.timedelta(days=-365)),
        }
