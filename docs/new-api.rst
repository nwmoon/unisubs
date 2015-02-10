Beta API Documentation
======================

Amara provides a REST API to interactive with the site.  Please contact us if
you’d like to use the Amara API for commercial purposes.

.. note:: This documentation is for the upcoming Amara API.  It is currently
  being actively developed and not yet fully functional. See
  `the API changes blog post <http://about.amara.org/2015/01/20/api-changes/>`_
  for more info.

Authentication
--------------

Before interacting with the API, you must have an API key. In order to get one,
create a user on the Amara website, then go to the `edit profile
<http://www.amara.org/en/profiles/edit/>`_ page. At the bottom of
the page you will find a "Generate new key" button . Clicking on it will fetch
your user the needed API key.

Every request must have the username and the API keys as headers. For example::

   X-api-username: my_username_here
   X-api-key: my_api_key_here

.. note:: You can also use the deprecated X-apikey header to specify your key

So a sample request would look like this:

.. http:get:: amara.org/api/videos/

  :reqheader X-api-username: <Username>
  :reqheader X-api-key: <API key>


.. _api-data-formats:

Data Formats
------------

The API accepts request data in the several formats.  Use the ``Content-Type``
HTTP header to specify the format of your request:

====================  ==================
Format                Content-Type
====================  ==================
JSON *(recommended)*  application/json
XML                   application/xml
YAML                  application/yaml
====================  ==================

In this documentation, we use the term "Request JSON Object" to specify the
fields of the objects sent as the request body.  Replace "JSON" with "XML" or
"YAML" if you are using one of those input formats.

Here's an example of request data formated as JSON:

.. code-block:: json

    {"field1": "value1", "field2": "value2", ... }

By default we will return JSON output.  You can the ``Accept`` header to select
a different output format.  You can also use the ``format`` query param to
select the output formats.  The value is the format name in lower case (for
example ``format=json``).

We also support text/html as an output format and
application/x-www-form-urlencoded and multipart/form-data as input formats.
However, this is only to support browser friendly endpoints.  It should not be
used in API client code.

Browser Friendly Endpoints
--------------------------

All our API endpoints can be viewed in a browser.  This can be very nice for
exploring the API and debugging issues.  To view API endpoints in your
browser simply log in to amara as usual then paste the API URL into your
address bar.

Value Formats
-------------

- Dates/times use ISO 8601 formatting
- Language codes use BCP-47 formatting

Use HTTPS
---------

All API requests should go through https.  This is important since an HTTP
request will send your API key over the wire in plaintext.

The only exception is when exploring the API in a browser.  In this case you
will be using the same session-based authentication as when browsing the site.

API interaction overview
------------------------

All resources share a common structure when it comes to the basic data
operations.

* ``GET`` request is used to viewing data
* ``POST`` request is used for creating new items
* ``PUT`` request is used for updating existing items
* ``DELETE`` request is used for deleting existing items

To view a list of videos on the site you can use

.. http:get:: amara.org/api/videos/

To get info about the video with id "foo" you can use

.. http:get:: amara.org/api/videos/foo

Many of the available resources will allow you to filter the response by a
certain field.  Filters are specified as GET parameters on the request.  For
example, if you wanted to view all videos belong to a team called
"butterfly-club", you could do:

.. http:get:: amara.org/api/videos/?team=butterfly-club

In addition to filters, you can request that the response is ordered in some
way.  To order videos by title, you would do

.. http:get:: amara.org/api/videos/?order_by=title

To create a video you can use

.. http:post:: amara.org/api/videos/

To update the video with video id `foo` use:

.. http:put:: amara.org/api/videos/foo

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

.. http:put:: amara.org/api/videos/yxsSV807Dcho

  :reqjson usePartnerId: true
  :reqjson id: 12345

And then, you can start referencing the video by the numeric id when
interacting with the API. For example, the following call will retrieve the
above video.

.. http:get:: amara.org/api/videos/12345?usePartnerId=true

Available Resources
-------------------

The following resources are available to end users:

.. automodule:: api.views.videos
