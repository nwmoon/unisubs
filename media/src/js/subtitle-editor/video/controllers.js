// Amara, universalsubtitles.org
//
// Copyright (C) 2013 Participatory Culture Foundation
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see
// http://www.gnu.org/licenses/agpl-3.0.html.

(function() {

    var module = angular.module('amara.SubtitleEditor.video.controllers', []);

    module.controller('VideoController', ['$scope', '$sce', 'VideoPlayer', function($scope, $sce, VideoPlayer) {
        $scope.overlayText = null;
        $scope.showOverlay = false;

        $scope.videoState = {
            loaded: false,
            playing: false,
            currentTime: null,
            duration: null,
            volumeBarVisible: false,
            volume: 0.0,
        }

        $scope.$root.$on("video-update", function() {
            $scope.videoState.loaded = true;
            $scope.videoState.playing = VideoPlayer.isPlaying();
            $scope.videoState.currentTime = VideoPlayer.currentTime();
            $scope.videoState.duration = VideoPlayer.duration();
            $scope.videoState.volume = VideoPlayer.getVolume();
        });
        $scope.$root.$on("video-time-update", function(evt, currentTime) {
            $scope.videoState.currentTime = currentTime;
        });
        $scope.$root.$on("video-volume-update", function(evt, volume) {
            $scope.videoState.volume = volume;
        });

        $scope.playPauseClicked = function(event) {
            VideoPlayer.togglePlay();
            event.preventDefault();
        };

        $scope.volumeToggleClicked = function(event) {
            $scope.volumeBarVisible = !$scope.volumeBarVisible;
            event.preventDefault();
        };

        $scope.$watch('currentEdit.draft.content()', function(newValue) {
            if(newValue !== null && newValue !== undefined) {
                $scope.overlayText = $sce.trustAsHtml(newValue);
                $scope.showOverlay = true;
            } else if($scope.timeline.shownSubtitle !== null) {
                $scope.overlayText = $sce.trustAsHtml($scope.timeline.shownSubtitle.content());
                $scope.showOverlay = true;
            } else {
                $scope.showOverlay = false;
            }
        });
        $scope.$root.$on('subtitle-selected', function($event, scope) {
            if(scope.subtitle.isSynced()) {
                VideoPlayer.playChunk(scope.startTime, scope.duration());
            }
            $scope.overlayText = $sce.trustAsHtml(scope.subtitle.content());
            $scope.showOverlay = true;
        });
        $scope.$watch('timeline.shownSubtitle', function(subtitle) {
            if(subtitle !== null) {
                $scope.overlayText = $sce.trustAsHtml(subtitle.content());
                $scope.showOverlay = true;
            } else {
                $scope.showOverlay = false;
            }
        });

        // use evalAsync so that the video player gets loaded after we've
        // rendered all of the subtitles.
        $scope.$evalAsync(function() {
              VideoPlayer.init();
        });

    }]);

    module.controller('PlaybackModeController', function($scope, $log, $timeout, VideoPlayer) {
        $scope.playbackMode = 'standard';

        // The playbackTimer is used by both magic and beginner modes to
        // schedule timeouts.  It automatically cancels the timeout if
        // playback is started or paused or if the mode is switched.

        var playbackTimerPromises = [];

        $scope.playbackTimer = function(callback, delay) {
            var promise = $timeout(function() {
                removePlaybackTimerPromise(promise);
                callback();
            }, delay);
            playbackTimerPromises.push(promise);
            return promise;
        }

        function removePlaybackTimerPromise(promise) {
            playbackTimerPromises = _.filter(playbackTimerPromises,
                function(other) {
                return other !== promise;
            });
        }

        $scope.playbackTimer.cancel = function(promise) {
            removePlaybackTimerPromise(promise);
            $timeout.cancel(promise);
        };

        function cancelPlaybackTimers() {
            var oldPromises = playbackTimerPromises;
            playbackTimerPromises = [];
            _.each(oldPromises, function(promise) {
                $timeout.cancel(promise);
            });
        }

        // Define objects to handle the various modes
        function ModeHandler() {};
        ModeHandler.prototype = {
            // name for the mode.  subclasses should override this
            name: 'base',
            activate: function() {
                // Called when the mode is switched to
            },
            deactivate: function() {
                // Called when the mode is switched away from
            },
            onVideoUpdate: function() {
            },
            onSubtitleEditKeyPress: function(evt) {
            }
        };

        function StandardModeHandler() {};
        StandardModeHandler.prototype = Object.create(ModeHandler.prototype);
        _.extend(StandardModeHandler.prototype, { name: 'standard' });

        function BeginnerModeHandler() {};
        BeginnerModeHandler.prototype = Object.create(ModeHandler.prototype);
        _.extend(BeginnerModeHandler.prototype, {
            name: 'beginner',
            timeoutScheduled: false,
            onVideoUpdate: function() {
                var that = this;

                if(VideoPlayer.isPlaying() && !this.timeoutScheduled) {
                    var promise = $scope.playbackTimer(function() {
                        VideoPlayer.pause();
                        that.timeoutScheduled = false;
                    }, 4000).then(null, function() {
                        that.timeoutScheduled = false;
                    });
                    that.timeoutScheduled = true;
                }
            },
        });

        function MagicModeHandler() {};
        MagicModeHandler.prototype = Object.create(ModeHandler.prototype);
        _.extend(MagicModeHandler.prototype, {
            name: 'magic',
            timeoutScheduled: false,
            sawKeyPress: false,
            autopaused: false,
            scheduleTimeout: function(callback, delay) {
                if(this.timeoutScheduled) {
                    $log.warn("timeout already scheduled");
                    return;
                }

                var that = this;
                $scope.playbackTimer(function() {
                    that.timeoutScheduled = false;
                    callback();
                }, delay).then(null, function onCancel() {
                    that.timeoutScheduled = false;
                });
                this.timeoutScheduled = true;
                this.sawKeyPress = false;
            },
            onSubtitleEditKeyPress: function(evt) {
                this.sawKeyPress = true;
            },
            onVideoUpdate: function() {
                if(VideoPlayer.isPlaying() && !this.timeoutScheduled) {
                    this.schedulePauseTimeout(0);
                } else if(!VideoPlayer.isPlaying()) {
                    if(this.autopaused) {
                        this.schedulePlayTimeout();
                        this.autopaused = false;
                    }
                }
            },
            schedulePauseTimeout: function(count) {
                var that = this;

                this.scheduleTimeout(function() {
                    if(that.sawKeyPress) {
                        if(count < 3) {
                            that.schedulePauseTimeout(count+1);
                        } else {
                            VideoPlayer.pause();
                            that.seekBackwards();
                            that.autopaused = true;
                        }
                    } else {
                        that.schedulePauseTimeout(0);
                    }
                }, 1000);
            },
            schedulePlayTimeout: function() {
                var that = this;
                this.scheduleTimeout(function() {
                    if(that.sawKeyPress) {
                        that.schedulePlayTimeout();
                    } else {
                        VideoPlayer.play();
                    }
                }, 1000);
            },
            seekBackwards: function() {
                var currentTime = VideoPlayer.currentTime();
                if(currentTime) {
                    var newTime = VideoPlayer.currentTime() - 3000;
                    VideoPlayer.seek(Math.max(0, newTime));
                }
            }
        });

        var modeHandlers = {
            standard: new StandardModeHandler(),
            beginner: new BeginnerModeHandler(),
            magic: new MagicModeHandler()
        };

        $scope.currentModeHandler = modeHandlers.standard;

        function updateModeHandler() {
            if($scope.workflow.stage == 'type') {
                var newModeHandler = modeHandlers[$scope.playbackMode];
            } else {
                var newModeHandler = modeHandlers['standard'];
            }
            if(newModeHandler !== $scope.currentModeHandler) {
                VideoPlayer.pause();
                cancelPlaybackTimers();
                $scope.currentModeHandler.deactivate();
                $scope.currentModeHandler = newModeHandler;
                $scope.currentModeHandler.activate();
            }
        }

        $scope.$watch('playbackMode', updateModeHandler);

        $scope.$watch('workflow.stage', updateModeHandler);

        var videoWasPlaying = VideoPlayer.isPlaying();
        $scope.$root.$on('video-update', function() {
            var videoIsPlaying = VideoPlayer.isPlaying();
            if(videoIsPlaying != videoWasPlaying) {
                cancelPlaybackTimers();
                videoWasPlaying = videoIsPlaying;
            }
            $scope.currentModeHandler.onVideoUpdate();
        });

        $scope.$root.$on('subtitle-edit-key-press', function(evt) {
            $scope.currentModeHandler.onSubtitleEditKeyPress(evt);
        });
    });
}).call(this);
