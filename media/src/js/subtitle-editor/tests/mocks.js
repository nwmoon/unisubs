(function() {

    var module = angular.module('amara.SubtitleEditor.mocks', []);

    module.factory('VideoPlayer', function() {
        var mockMethods = [
            'init',
            'play',
            'pause',
            'seek',
            'togglePlay',
            'currentTime',
            'duration',
            'isPlaying',
            'getVolume',
            'setVolume',
            'playChunk',
        ];
        var MockVideoPlayer = jasmine.createSpyObj('VideoPlayer',
            mockMethods);
        MockVideoPlayer.playing = false;
        MockVideoPlayer.time = 10000; // 10 seconds
        MockVideoPlayer.isPlaying.andCallFake(function() {
            return MockVideoPlayer.playing;
        });
        MockVideoPlayer.currentTime.andCallFake(function() {
            return MockVideoPlayer.time;
        });
        MockVideoPlayer.seek.andCallFake(function(newTime) {
            MockVideoPlayer.time = newTime;
        });
        MockVideoPlayer.play.andCallFake(function() {
            MockVideoPlayer.playing = true;
        });
        MockVideoPlayer.pause.andCallFake(function() {
            MockVideoPlayer.playing = false;
        });
        MockVideoPlayer.reset = function() {
            var that = this;
            _.each(mockMethods, function(methodName) {
                that[methodName].reset();
            });
        }
        return MockVideoPlayer;
    });

    module.factory('SubtitleStorage', function($q) {
        var methodNames = [
            'approveTask',
            'updateTaskNotes',
            'getLanguages',
            'getLanguage',
            'getSubtitles',
            'sendBackTask',
            'saveSubtitles',
        ];
        var SubtitleStorage = {
            deferreds: {},
        };
        _.each(methodNames, function(methodName) {
            var deferred = $q.defer();
            SubtitleStorage[methodName] = jasmine.createSpy(methodName).andReturn(deferred.promise);
            SubtitleStorage.deferreds[methodName] = deferred;
        });
        return SubtitleStorage;
    });

    module.factory('DomWindow', function() {
        var mockObject = jasmine.createSpyObj('DomWindow', [
            'onDocumentEvent',
            'offDocumentEvent'
        ]);
        mockObject.caretPos = jasmine.createSpy('caretPos').andReturn(0);
        return mockObject;
    });

    module.factory('MockEvents', function() {
        function makeEvent(type, attrs) {
            evt = {
                type: type,
                preventDefault: jasmine.createSpy(),
                stopPropagation: jasmine.createSpy(),
            }
            return overrideEventAttributes(evt, attrs);
        }
        function overrideEventAttributes(evt, attrs) {
            if(attrs !== undefined) {
                for(key in attrs) {
                    evt[key] = attrs[key];
                }
            }
            return evt;
        }
        return {
            keydown: function(keyCode, attrs) {
                var evt = makeEvent('keydown');
                evt.keyCode = keyCode;
                evt.shiftKey = false;
                evt.ctrlKey = false;
                evt.altKey = false;
                evt.target = { type: 'div' };
                return overrideEventAttributes(evt, attrs);
            },
            click: function(attrs) {
                return makeEvent('click', attrs);
            },
        }
    });

    module.factory('EditorData', function() {
        return {
            "canSync": true,
            "canAddAndRemove": true,
            "languageCode": "en",
            "editingVersion": {
                "languageCode": "en",
                "versionNumber": null,
            },
            "video": {
                "id": "4oqOXzpPk5rU",
                "videoURLs": [
                    "http://vimeo.com/25082970"
                ],
                "primaryVideoURL": "http://vimeo.com/25082970"
            },
            "oldEditorURL": '/old-editor/test-url/',
            "languages": [
                {
                    "is_rtl": false,
                    "numVersions": 0,
                    "editingLanguage": true,
                    "language_code": "en",
                    "pk": 23,
                    "versions": [],
                    "is_primary_audio_language": true,
                    "name": "English"
                },
            ],
            'staticURL': 'http://example.com/'
        };
    });

    module.factory('$timeout', function($q) {
        var deferreds = [];

        var mockTimeout = jasmine.createSpy('$timeout')
                            .andCallFake(function(callback) {
            var deferred = $q.defer();
            var promise = deferred.promise;
            deferreds.push(deferred);
            promise.number = deferreds.length - 1;
            mockTimeout.promisesReturned.push(promise);
            mockTimeout.lastPromiseReturned = promise;
            mockTimeout.lastCallback = callback;
            return promise;
        });
        mockTimeout.promisesReturned = [];
        mockTimeout.lastPromiseReturned = null;
        mockTimeout.lastCallback = null;
        mockTimeout.cancel = jasmine.createSpy('cancel')
            .andCallFake(function(promise) {
                deferreds[promise.number].reject("timeout canceled");
        });
        return mockTimeout;
    });
}).call(this);
