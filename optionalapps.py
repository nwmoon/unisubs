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

"""
Optional Apps
=============
Amara.org uses several apps/packages that are stored in private github
repositories that add extra functionality for paid partnerships.  These apps
are optional -- the amara codebase runs fine without them.

The coding issue is how to make amara work without these repositories, but
automatically pull them in if they are present.  Here's how we do it:

* For each repository we create a file inside the optional/ directory:

  * The filename is the name of the repository
  * The contents are the git commit ID that we want to use

* To enable a repository, it must be checked out in the amara root directory,
  using the same name as the git repository.

* The optionalapps module handles figuring out which repositories are present
  and how we should modify things at runtime

.. autofunction:: get_repository_paths
.. autofunction:: get_apps
.. autofunction:: get_urlpatterns
.. autofunction:: add_extra_settings

"""

import os

from django.conf.urls import patterns, include, url

project_root = os.path.abspath(os.path.dirname(__file__))

def _repositories_present():
    """Get a list of optional repositories that are present."""
    for name in os.listdir(os.path.join(project_root, 'optional')):
        # exclude names that don't look like repositories
        if name.startswith('.'):
            continue
        if os.path.exists(os.path.join(project_root, name)):
            yield name

def get_repository_paths():
    """Get paths to optional repositories that are present

    Returns:
        list of paths to our optional repositories.  We should add these to
        sys.path so that we can import the apps.
    """
    return [os.path.join(project_root, repo)
            for repo in _repositories_present()]

def get_apps():
    """Get a list of optional apps

    Returns:
        list of app names from our optional repositories to add to
        INSTALLED_APPS.
    """
    apps = []
    for directory in get_repository_paths():
        for potential_app in os.listdir(directory):
            appdir = os.path.join(directory, potential_app)
            if os.path.exists(os.path.join(appdir, 'models.py')):
                apps.append(potential_app)
    return tuple(apps)

def get_urlpatterns():
    """Get Django urlpatterns for URLs from our optional apps.

    This function finds urlpatterns inside the urls module for each optional
    app.  In addition a module variable can define a variable called PREFIX to
    add a prefix to the urlpatterns.

    Returns:
        url patterns containing urls for our optional apps to add to our root
        urlpatterns
    """
    urlpatterns = patterns('')

    for app_name in get_apps():
        try:
            app_module = __import__('{0}.urls'.format(app_name))
            url_module = app_module.urls
        except ImportError:
            continue
        try:
            prefix = url_module.PREFIX
        except AttributeError:
            prefix = ''
        urls_module = '{0}.urls'.format(app_name)
        urlpatterns += patterns('', url(prefix, include(urls_module,
                                                        namespace=app_name)))

    return urlpatterns

def add_extra_settings(globals, locals):
    """Add extra values to the settings module.

    This function looks for files named settings_extra.py in each optional
    repository.  If that exists, then we call execfile() to run the code using
    the settings globals/locals.  This simulates that code being inside the
    settings module.
    """
    for directory in get_repository_paths():
        settings_extra = os.path.join(directory, 'settings_extra.py')
        if os.path.exists(settings_extra):
            execfile(settings_extra, globals, locals)
