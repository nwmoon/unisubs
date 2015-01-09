API Documentation
=================

This is the documentation of v2 of Amara's API. Please contact us
if you’d like to use the Amara API for commercial purposes.

.. note:: The v1 of the API is deprecated, but can still be accessed through
    http://www.amara.org/api/1.0/documentation/ . Users should migrate
    to the v2 of the API. If you're missing a feature on the API, please `let us
    know <https://support.amara.org/>`_ .

Authentication
--------------

Before interacting with the API, you must have an API key. In order to get one,
create a user on the Amara website, then go to the `edit profile
<http://www.amara.org/en/profiles/edit/>`_ page. At the bottom of
the page you will find a "Generate new key" button . Clicking on it will fetch
your user the needed API key.

Every request must have the username and the API keys as headers. For example::

   X-api-username: my_username_here
   X-apikey: my_api_key_here

So a sample request would look like this::

    $ curl -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        https://staging.amara.org/api2/partners/videos/

Data Formats
------------

The API accepts request data and will output the following formats: JSON, XML
and YAML. Unless you have a strong reason not to, we recommend using the JSON
format, as it's the one that gets the most usage (and therefore more testing).

To specify the format, add the ``Accept`` header appropriately, for example::

    Accept: application/json

You can also specify the desired format in the url, sending the request
variable ``format=json``.

API endpoint
------------

The endpoint for the API is the environment base URL +  ``/api2/partners/``.

Possible environments:

* Staging: ``https://staging.amara.org/``
* Production: ``https://www.amara.org/``

Therefore, most clients should be making requests against:
``https://www.amara.org/api2/partners/``

All API requests should go through https. The staging environment might need
HTTP basic auth, please contact us to request credentials.  When basic auth is
needed on staging, you end up with a request like this::

    $ curl -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        --user basic_auth_username:basic_auth_password \
        https://staging.amara.org/api2/partners/videos/

If you're under a partnership, you might have a different base URL. Please
contact us if you're not sure.

API interaction overview
------------------------

All resources share a common structure when it comes to the basic data
operations.

* ``GET`` request is used to viewing data
* ``POST`` request is used for creating new items
* ``PUT`` request is used for updating existing items
* ``DELETE`` request is used for deleting existing items

For example, in order to request a list of teams the user is current on, you
would issue the following request:

.. http:get:: /api2/partners/teams/

To view a detail of the ``test`` team, you could do:

.. http:get:: /api2/partners/teams/test/

Example response

.. code-block:: json

    {
        "created": "2012-04-18T09:26:59",
        "deleted": false,
        "description": "",
        "header_html_text": "",
        "is_moderated": false,
        "is_visible": true,
        "logo": null,
        "max_tasks_per_member": null,
        "membership_policy": "Open",
        "name": "test",
        "projects_enabled": false,
        "resource_uri": "/api2/partners/teams/test/",
        "slug": "test",
        "subtitle_policy": "Anyone",
        "task_assign_policy": "Any team member",
        "task_expiration": null,
        "translate_policy": "Anyone",
        "video_policy": "Any team member",
        "workflow_enabled": false
    }

Many of the available resources will allow you to filter the response by a
certain field.  Filters are specified as GET parameters on the request.  For
example, if you wanted to view all videos belong to a team called
"butterfly-club", you could do:

.. http:get:: /api2/partners/videos?team=butterfly-club

In addition to filters, you can request that the response is ordered in some
way.  To order videos by title, you would do

.. http:get:: /api2/partners/videos?order_by=title

Each resource section will contain a list of relevant options.

Here is an example of creating a new team via ``curl``.

.. code-block:: bash

    curl -i -X POST -H "Accept: application/json" \
        -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        -H "Content-Type: application/json" \
        --data '{"name": "Team name", "slug": "team-name"}' \
        http://host/api2/partners/teams/

You can use the same fields that you get back when requesting a team detail.

To update a team, you could issue a request like this:

.. code-block:: bash

    curl -i -X PUT -H "Accept: application/json" \
        -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        -H "Content-Type: application/json" \
        --data '{"name": "My team name"}' \
        https://host/api2/partners/teams/test/

.. warning:: The above example only includes the ``name`` field for
    illustration. When sending a ``PUT`` request, always include all fields.
    For a list of all fields, see the response to a ``GET`` request.

Partner video ids
-----------------

If you are a partner, you can set the ``id`` field for a video.  Simply supply
the ``usePartnerId`` parameter in your request and we will use your id for look
ups.  The parameter can be sent as a parameter to any kind of API call.  This
is useful if you already have a database of video ids and don't want to
maintain a mapping between those ids and Amara ids.

For example, let's say you have an Amara video with the id of ``yxsSV807Dcho``.
Your application uses numeric id internally and you would like to tell Amara to
remember that this video has an id of ``12345`` on your system.  You can modify
the video like this:

.. code-block:: bash

    curl -i -X PUT -H "Accept: application/json" \
        -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        -H "Content-Type: application/json" \
        --data '{"usePartnerId": true, "id": "12345"}' \
        https://host/api2/partners/videos/yxsSV807Dcho/

And then, you can start referencing the video by the numeric id when
interacting with the API. For example, the following call will retrieve the
above video.

.. code-block:: bash

    curl -i -X GET -H "Accept: application/json" \
        -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        -H "Content-Type: application/json" \
        https://host/api2/partners/videos/12345/?usePartnerId=true

Available Resources
-------------------

The following resources are available to end users:

Video Resource
~~~~~~~~~~~~~~

Represents a video on Amara.

Listing videos

.. http:get:: /api2/partners/videos/

    :query video_url:  list only videos with the given URL, useful for finding out information about a video already on Amara.
    :query team:       Only show videos that belong to a team identified by ``slug``.
    :query project:    Only show videos that belong to a project with the given slug.
        Passing in ``null`` will return only videos that don't belong to a project.
    :query order_by:   Applies sorting to the video list. Possible values:

        * `title`: ascending
        * `-title`: descending
        * `created`: older videos first
        * `-created` : newer videos

Creating Videos:

.. http:post:: /api2/partners/videos/

    :form video_url: The url for the video. Any url that Amara accepts will work here. You can send the URL for a file (e.g. http:///www.example.com/my-video.ogv) , or a link to one of our accepted providers (youtube, vimeo, dailymotion, blip.tv)
    :form title: The title for the video :form description: About this video
    :form duration: Duration in seconds
    :form primary_audio_language_code: The language code representing main language spoken  on the video. This helps the UI to show the best title for that video, or set "Subtitle" taks in the right language from the get-go - optional.

When submitting URLs of external providers (i.e. youtube, vimeo), the metadata
(title, description, duration) can be fetched from them. If you're submitting a
link to a file (mp4, flv) then you can make sure those attributes are set with
these parameters. Note that these parameters do override any information from
the original provider.

Information about a specific video can be retrieved from the URL:

Video Detail:

.. http:get:: /api2/partners/videos/[video-id]/

The video listing resource already returns a ``resource_uri`` for each video to
be used when retrieving the details.

Updating a video object:

.. http:put:: /api2/partners/videos/[video-id]/

With the same parameters for creation. Note that through out our system, a
video cannot have it's URLs changed. So you can change other video attributes
(title, description) but the URL sent must be the same original one.

Moving videos between teams and projects
++++++++++++++++++++++++++++++++++++++++

In order to move a video from one team to another, you can make a request to
change the video where you change the ``team`` value in the Video Resource.

In order to move the video from *Team A* to *Team B*, you would make the
following request.

.. code-block:: bash

    curl -i -X PUT -H "Accept: application/json" \
        -H 'X-api-username: my_username_here' -H 'X-apikey: my_api_key_here' \
        -H "Content-Type: application/json" \
        --data '{"team": "team_b"}' \
        https://host/api2/partners/videos/video-id/

Please note that the value that is sent as the ``team`` is the team's slug.
The user making the change must have permission to remove a video from the
originating team and permission to add a video to the target team.

Setting the ``team`` value to ``null`` will remove it from its current team.

A similar mechanism can be used to change what project a given video is filed
under.  The important difference is that when moving a video to different
project, the team must be specified in the payload even if it doesn't change.

.. code-block:: json

    {
        "team:" "team-slug",
        "project": "new-project"
    }

Example response:

.. code-block:: json


    {
        "all_urls": [
            "http://vimeo.com/4951380"
        ],
        "created": "2012-05-15T06:05:14",
        "description": "Concierto Grupo NOMOI \n(Torrevieja 17/05/2009)\nProyecto TRANSMOSFERA\nAcci\u00f3n interactiva de m\u00fasica, teatro e imagen.\nJuan Pablo Zaragoza - V\u00eddeo y Guitarra sintetizada\nJos\u00e9 Mar\u00eda Pastor - Electr\u00f3nica\nRaul Ferrandez - Voz y acci\u00f3n teatral",
        "duration": null,
        "id": "PUuHIcJ5mq5S",
        "languages": [],
        "original_language": null,
        "project": null,
        "resource_uri": "/api2/partners/videos/PUuHIcJ5mq5S/",
        "site_url": "http://unisubs.example.com:8000/videos/PUuHIcJ5mq5S/info/",
        "team": null,
        "thumbnail": "http://b.vimeocdn.com/ts/142/595/14259507_640.jpg",
        "title": "Concierto NOMOI (Torrevieja 17/05/2009)"
    }


Video Language Resource
~~~~~~~~~~~~~~~~~~~~~~~

Represents a language for a given video on Amara.

Listing video languages:

.. http:get:: /api2/partners/videos/[video-id]/languages/

Creating Video Languages:

.. http:post:: /api2/partners/videos/[video-id]/languages/

    :form language_code: The language code (e.g 'en' or 'pt-br') to create.
    :form title: The title for the video localized to this language - optional
    :form description: Localized description for this language - optional.
    :form is_original: Boolean indicating if this is the original language for the video. - optional - defaults to false.
    :form is_original: If set to true, will mark this language as the primary audio language for the video ( see VideoResource) - optional, defaults to false.

.. seealso::  To list available languages, see ``Language Resource``.

Information about a specific video language can be retrieved from the URL:

.. http:get:: /api2/partners/videos/[video-id]/languages/[lang-identifier]/

    :param lang-identifier: language identifier can be the language code (e.g. ``en``) or the
        numeric ID returned from calls to listing languages.

Example response:

.. code-block:: json

    {
        "completion": "100%",
        "created": "2012-05-17T12:25:54",
        "description": "",
        "id": "8",
        "is_original": false,
        "is_translation": false,
        "language_code": "cs",
        "num_versions": 1,
        "original_language_code": "en",
        "percent_done": 0,
        "resource_uri": "/api2/partners/videos/Myn4j5OI7BxL/languages/8/",
        "site_url": "http://unisubs.example.com:8000/videos/Myn4j5OI7BxL/cs/8/",
        "subtitle_count": 11,
        "title": "\"Postcard From 1952\" - Explosions in The Sky",
        "versions": [
            {
                "author": "honza",
                "status": "published",
                "text_change": "1.0",
                "time_change": "1.0",
                "version_no": 0
            }
        ]
    }

Subtitles Resource
~~~~~~~~~~~~~~~~~~

Represents the subtitle set for a given video language.

Fetching subtitles for a given language:

.. http:get:: /api2/partners/videos/[video-id]/languages/[lang-identifier]/subtitles/?format=srt
.. http:get:: /api2/partners/videos/asfssd/languages/en/subtitles/?format=dfxp
.. http:get:: /api2/partners/videos/asfssd/languages/111111/subtitles/?format=ssa

    :query format: The format to return the subtitles in. Supports all the
        formats the regular website does: srt, ssa, txt, dfxp, ttml.
    :query version: the numeric version number to fetch.  Versions are listed in the
        VideoLanguageResouce request.

If no version is specified, the latest public version will be returned. For
videos that are not under moderation it will be the latest one. For videos
under moderation only the latest published version is returned. If no version
has been accepted in review, no subtitles will be returned.

Creating new subtitles for a language:

.. http:post:: /api2/partners/videos/[video-id]/languages/[lang-identifier]/subtitles/
.. http:post:: /api2/partners/videos/asfssd/languages/en/subtitles/

    :query subtitles: The subtitles to submit
    :query sub_format: The format used to parse the subs. The same formats as
        for fetching subtitles are accepted. Optional - defaults to ``srt``.
    :query title: Give a title to the new revision
    :query description: Give a description to the new revision

    :form is_complete: Boolean indicating if the complete subtitling set is available for this language - optional, defaults to false.

This will create a new subtitle version with the new subtitles.

Example response:

.. http:get:: /api2/partners/videos/TRUFD3IyncAt/languages/en/subtitles/

.. code-block:: json

    {
        "description": "Centipede - Knife Party www.knifeparty.com\nFireworks - Pyro Spectaculars by Souza www.pyrospectaculars.com/\n\n( Sittin' On ) The Dock of the Bay - Otis Redding\nLights - Journey\nFrisco Blues - John Lee Hooker\nSan Francisco ( Be Sure to Wear Flowers in Your Hair ) - Scott McKenzie  \nI Left My Heart in San Francisco - Tony Bennett\n\nIf you didn't understand what was happening, you should probably watch it again.\nThis has been a Seventh Movement effort.",
        "note": "",
        "resource_uri": "",
        "site_url": "http://example-host/api2/partners/videos/TRUFD3IyncAt/en/1/",
        "sub_format": "srt",
        "subtitles": [
            {
                "end": 4,
                "id": 1,
                "start": 3,
                "start_of_paragraph": false,
                "text": "This is a cool bridge"
            },
            {
                "end": 5,
                "id": 2,
                "start": 4,
                "start_of_paragraph": false,
                "text": "Really cool"
            },
            {
                "end": 6,
                "id": 3,
                "start": 5,
                "start_of_paragraph": false,
                "text": "I love it"
            }
        ],
        "title": "The Golden Gate Way",
        "version_no": 0,
        "video": "The Golden Gate Way",
        "video_description": "Centipede - Knife Party www.knifeparty.com\nFireworks - Pyro Spectaculars by Souza www.pyrospectaculars.com/\n\n( Sittin' On ) The Dock of the Bay - Otis Redding\nLights - Journey\nFrisco Blues - John Lee Hooker\nSan Francisco ( Be Sure to Wear Flowers in Your Hair ) - Scott McKenzie  \nI Left My Heart in San Francisco - Tony Bennett\n\nIf you didn't understand what was happening, you should probably watch it again.\nThis has been a Seventh Movement effort.",
        "video_title": "The Golden Gate Way"
    }


Language Resource
~~~~~~~~~~~~~~~~~

Represents a listing of all available languages on the Amara
platform.

Listing available languages:

.. http:get:: /api2/partners/languages/

User Resource
~~~~~~~~~~~~~

One can list and create new users through the API.

Listing users:

.. http:get:: /api2/partners/users/

User datail:

.. http:get:: /api2/partners/users/[username]/

Creating Users:

.. http:post:: /api2/partners/users/

    :form username: the username for later login.  30 chars or fewer alphanumeric chars, @, _ and - are accepted.
    :form email: A valid email address
    :form password: any number of chars, all chars allowed.
    :form first_name: Any chars, max 30 chars. Optional.
    :form last_name: Any chars, max 30 chars. Optional.
    :form create_login_token: If sent the response will also include a url that when clicked will login the recently created user. This URL expires in 2 hours

The response also includes the 'api_key' for that user. If clients wish to make
requests on behalf of this newly created user through the api, they must hold
on to this key, since it won't be returned in the detailed view.

Example response:

.. code-block:: json

    {
        "avatar": "http://www.gravatar.com/avatar/947b2f9a76cd39f5c7b7c8ad3a36?s=100&d=mm",
        "biography": "The guy with a boring name.",
        "first_name": "John",
        "full_name": "John Smith",
        "homepage": "http://example.com",
        "last_name": "Smith",
        "num_videos": 8,
        "resource_uri": "/api2/partners/users/jsmith/",
        "username": "jsmith"
    }

Video Url Resource
~~~~~~~~~~~~~~~~~~

One can list, update, delete and add new video urls to an existing video.

Listing video urls

.. http:get:: /api2/partners/videos/[video-id]/urls/

Video URL detail:

.. http:get:: /api2/partners/videos/[video-id]/urls/[url-id]/

Where the url-id can be fetched from the list of urls.

Updating video-urls:

.. http:put:: /api2/partners/videos/[video-id]/urls/[url-id]/

Creating video-urls:

    :form url: Video URL (this must match the current URL)
    :form primary: If True, this URL will be made the primary URL

.. http:post:: /api2/partners/videos/[video-id]/urls/

    :form url: Any URL that works for the regular site (mp4 files, youtube, vimeo,
        etc) can be used. Note that the url cannot be in use by another video.
    :form primary:  A boolean. If true this is the url the will be displayed first
        if multiple are presents. A video must have one primary URL. If you add /
        change the primary status of a url, all other urls for that video will have
        primary set to false. If this is the only url present it will always be set
        to true.
    :form original: If this is the first url for the video.

To delete a url:

.. http:delete:: /api2/partners/videos/[video-id]/urls/[url-id]/

If this is the only URL for a video, the request will fail. A video must have
at least one URL.

Team Resource
~~~~~~~~~~~~~

You can list existing teams:

.. http:get:: /api2/partners/teams/

You can view details for an existing team:

.. http:get:: /api2/partners/teams/[team-slug]/

Creating a team:

.. http:post:: /api2/partners/teams/

    :form name: (required) Name of the team
    :form slug: (required) A unique slug (used in URLs)
    :form description:
    :form is_visible: Should this team be publicly visible?
    :form membership_policy: See below for possible values
    :form video_policy: See below for possible values
    :form task_assign_policy: See below for possible values
    :form max_tasks_per_member: Maximum tasks per member
    :form task_expiration: Task expiration in days

Example payload:

.. code-block:: json

    {
        "name": "Full Team",
        "slug": "full-team",
        "description": "One full team",
        "is_visible": false,
        "membership_policy": "Invitation by any team member",
        "video_policy": "Admins only",
        "task_assign_policy": "Managers and admins",
        "max_tasks_per_member": 3,
        "task_expiration": 14
    }

Updating a team:

.. http:put:: /api2/partners/teams/[team-slug]/

Deleting a team:

.. http:delete:: /api2/partners/teams/[team-slug]/

.. note:: You can only create new teams if you have been granted this
    privilege.  Contact us if you require a partner account.

Policy values
+++++++++++++

Membership policy:

* ``Open``
* ``Application``
* ``Invitation by any team member``
* ``Invitation by manager``
* ``Invitation by admin``

Video policy:

* ``Any team member``
* ``Managers and admins``
* ``Admins only``

Task assign policy:

* ``Any team member``
* ``Managers and admins``
* ``Admins only``

Example response

.. code-block:: json

    {
        "created": "2012-04-18T09:26:59",
        "deleted": false,
        "description": "",
        "header_html_text": "",
        "is_moderated": false,
        "is_visible": true,
        "logo": null,
        "max_tasks_per_member": null,
        "membership_policy": "Open",
        "name": "test",
        "projects_enabled": false,
        "resource_uri": "/api2/partners/teams/test/",
        "slug": "test",
        "subtitle_policy": "Anyone",
        "task_assign_policy": "Any team member",
        "task_expiration": null,
        "translate_policy": "Anyone",
        "video_policy": "Any team member",
        "workflow_enabled": false
    }

Team Member Resource
~~~~~~~~~~~~~~~~~~~~

This resource allows you to change team membership information without the
target user's input.  This resource is only applicable to:

* Teams associated with the partner's account
* Users who are already members of one of the partner's teams

You can list existing members of a team:

.. http:get:: /api2/partners/teams/[team-slug]/members/

Adding a new member to a team:

.. http:post:: /api2/partners/teams/[team-slug]/members/

Updating a team member (e.g. changing their role):

.. http:put:: /api2/partners/teams/[team-slug]/members/[username]/

Removing a user from a team:

.. http:delete:: /api2/partners/teams/[team-slug]/members/[username]/

Example of adding a new user:

.. code-block:: json

    {
        "username": "test-user",
        "role": "manager"
    }

Roles
+++++

* ``owner``
* ``admin``
* ``manager``
* ``contributor``

.. warning:: Changed behavior: the previous functionality was moved the Safe
    Team Member Resource documented below.

Permissions
+++++++++++

If a user belongs to a partner team, any admin or above on any of the partner's
teams can move the user anywhere within the partner's teams.  Moving is done by
first adding the user to the target team and then by removing the user from the
originating team.

Safe Team Member Resource
~~~~~~~~~~~~~~~~~~~~~~~~~

This resource behaves the same as the normal Team Member resource with one
small difference.  When you add a user to a team, we will send an invitation to
the user to join the team.  If the user doesn't exist, we will create it.  The
standard Team Member resource simply adds the user to the team and returns.

Listing:

.. http:get:: /api2/partners/teams/[team-slug]/safe-members/

Adding a new member to a team:

.. http:post:: /api2/partners/teams/[team-slug]/safe-members/

Project Resource
~~~~~~~~~~~~~~~~

List all projects for a given team:

.. http:get:: /api2/partners/teams/[team-slug]/projects/

Project detail:

.. http:get:: /api2/partners/teams/[team-slug]/projects/[project-slug]/

Create a new project:

.. http:post:: /api2/partners/teams/[team-slug]/projects/

Example payload for creating a new project:

.. code-block:: json

    {
        "name": "Project name",
        "slug": "project-slug",
        "description": "This is an example project.",
        "guidelines": "Only post family-friendly videos."
    }

.. note:: You can only create projects for a specific team.

Update an existing project:

.. http:put:: /api2/partners/teams/[team-slug]/projects/[project-slug]/

For example, to change the project's name:

.. code-block:: json

    {
        "name": "Project"
    }

Delete a project:

.. http:delete:: /api2/partners/teams/[team-slug]/projects/[project-slug]/

Task Resource
~~~~~~~~~~~~~

List all tasks for a given team:

.. http:get:: /api2/partners/teams/[team-slug]/tasks/

    :query assignee: Show only tasks assigned to a user identified by their
        ``username``.
    :query priority: Show only tasks with a given priority
    :query type: Show only tasks of a given type
    :query video_id: Show only tasks that pertain to a given video
    :query order_by: Apply sorting to the task list.  Possible values:

        * ``created``   Creation date
        * ``-created``  Creation date (descending)
        * ``priority``  Priority
        * ``-priority`` Priority (descending)
        * ``type``      Task type (details below)
        * ``-type``     Task type (descending)

    :query completed: Show only complete tasks
    :query completed-before: Show only tasks completed before a given date
        (unix timestamp)
    :query completed-after: Show only tasks completed before a given date
        (unix timestamp)
    :query open: Show only incomplete tasks

Task detail:

.. http:get:: /api2/partners/teams/[team-slug]/tasks/[task-id]/

Create a new task:

.. http:post:: /api2/partners/teams/[team-slug]/tasks/

Update an existing task:

.. http:put:: /api2/partners/teams/[team-slug]/tasks/[task-id]/

Delete an existing task:

.. http:delete:: /api2/partners/teams/[team-slug]/tasks/[task-id]/

Fields
++++++

* ``approved`` - If the team supports workflows, you can set the stage in which
  the task finds itself.

    * ``In Progress``
    * ``Approved``
    * ``Rejected``

* ``assignee`` - The username of the user that this task will be assigned to
* ``language``
* ``priority`` - An arbitrary integer denoting priority level; each team can
  set their own policy regarging priority of tasks
* ``video_id`` - The unique identifier of the video this task relates to
* ``type`` - Type of the task

    * ``Subtitle``
    * ``Translate``
    * ``Review``
    * ``Approve``

* ``version_no`` - Subtitle version number (required for ``Approve`` and
  ``Review`` tasks)
* ``completed`` - ``null`` if the task hasn't been completed yet; a datetime
  string it has

An example response:

.. code-block:: json

    {
        "approved": null,
        "assignee": "johnsmith",
        "language": "en",
        "priority": 1,
        "resource_uri": "/api2/partners/teams/all-star/tasks/3/",
        "type": "Subtitle",
        "video_id": "Myn4j5OI7BxL",
        "completed": "2012-07-18T14:08:07"
    }

Activity resource
~~~~~~~~~~~~~~~~~

This resource is read-only.

List activity items:

.. http:get:: /api2/partners/activity/

    :query team: Show only items related to a given team (team slug).
    :query team-activity: If team is given, we normally return activity on the
       team's videos.  If you want to see activity for the team itself (members
       joining/leaving and team video deletions, then add team-activity=1)
    :query video: Show only items related to a given video (video id)
    :query type: Show only items with a given activity type (int, see below)
    :query language: Show only items with a given language (language code)
    :query before: A unix timestamp in seconds
    :query after: A unix timestamp in seconds

Activity types:

1.  Add video
2.  Change title
3.  Comment
4.  Add version
5.  Add video URL
6.  Add translation
7.  Subtitle request
8.  Approve version
9.  Member joined
10. Reject version
11. Member left
12. Review version
13. Accept version
14. Decline version
15. Delete video

Activity item detail:

.. http:get:: /api2/partners/activity/[activity-id]/

Example response:

.. code-block:: json

    {
        "type": 1,
        "comment": null,
        "created": "2012-07-12T07:02:19",
        "id": "1339",
        "language": "en",
        "new_video_title": "",
        "resource_uri": "/api2/partners/activity/1339/",
        "user": "test-user"
    }

Message Resource
~~~~~~~~~~~~~~~~

The message resource allows you to send messages to user and teams.

.. http:post:: /api2/partners/message/

    :form subject: Subject of the message
    :form content: Content of the message
    :form user: Recipient's username
    :form team: Team's slug

You can only send the ``user`` parameter or the ``team`` parameter at once.



Application resource
~~~~~~~~~~~~~~~~~~~~

For teams with membership by application only.

List application items:

.. http:get:: /api2/partners/teams/[team-slug]/applications

    :query status: What status the application is at, possible values are 'Denied', 'Approved', 'Pending', 'Member Removed' and 'Member Left'
    :query before: A unix timestamp in seconds
    :query after: A unix timestamp in seconds
    :query user: The username applying for the team

Application item detail:

.. http:get:: /api2/partners/teams/[team-slug]/applications/[application-id]/

Example response:

.. code-block:: json

    {
       "created": "2012-08-09T17:48:48",
       "id": "12",
       "modified": null,
       "note": "",
       "resource_uri": "/api2/partners/teams/test-team/applications/12/",
       "status": "Pending",
       "user": "youtube-anonymous"

    }   

To delete an Application:

.. http:delete:: /api2/partners/teams/[team-slug]/applications/[application-id]/

Applications can have their statuses updated:

.. http:put:: /api2/partners/teams/[team-slug]/applications/[application-id]/

    :query status: What status the application is at, possible values are 'Denied', 'Approved', 'Pending', 'Member Removed' and 'Member Left'

Note that if an application is pending (has the status='Pending'), the API can
set it to whatever new status. Else, if the application has already been
approved or denied, you won't be able to set the new status. For cases were an
approval was wrongly issues, you'd want to remove the team member. Otherwise
you'd want to invite the user to the team.
