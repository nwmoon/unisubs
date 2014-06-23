Amara embedder
==============

The Amara embedder loads widget inside an iframe on any host page. Therefore, it does not interact and conflict with any JavaScript or CSS on the host page.

There are two main files:

* ``templates/embedder-iframe.js`` that should be loaded by the host page,
* ``media/src/js/embedder/embedder.js`` that includes most of the logic of the actual widget.

Usage
-----

The host page must load ``embedder-iframe.js`` and add a ``div`` element with the ``amara-embed`` class for each widget. Parameters such as the video URL, width and height are given as data attribute.

``embedder-iframe.js`` is responsible for adding the widgets inside the ``div`` element and resize them when needed. It also deals with observing and reacting to new elements added through AJAX.

``embedder-iframe.js``
----------------------

When the host page is fully loaded, it does the following actions:

* Search for the ``div`` elements on the host page with the ``amara-embed`` class.
* Set their size to the one specified as URL parameters.
* Add a spinning loading animated gif inside them.
* add an iframe inside each which points to an HTML file on the same domain. It adds to that URL the necessary parameters and also initializes a message listener. The page loaded in the iframe communicates with the hostapage with message, so they must be served on the same domain.
* When the iframe content is fully loaded, the loading gif is hidden so that the widget can appear.
* While the page is loaded, it constantly listen to messages from the page inside the iframe in order to be resized when needed, namlely when the transcript viewer is expanded.
* It also listen to any added element inside the host page so that it can load an frame inside any dynamically added content during the whole life cycle.

``embedder.js``
----------------------

The iframe added by ``embedder-iframe.js`` loads a web page which basically is populated by ``embedder.js``. It is based on ``backbone`` and ``jQuery``. It includes a video player, managed by ``popcorn.js`` and a custom menu. The menu controls the diplayed languages and is also used to toggle subtiltes and the transcript viewer.
