describe('The playback mode controller', function() {
    var $scope;
    var VideoPlayer;
    var $timeout;
    var $rootScope;

    beforeEach(function() {
        module('amara.SubtitleEditor.mocks');
        module('amara.SubtitleEditor.video.controllers');
    });

    beforeEach(inject(function($controller, $injector) {
        VideoPlayer = $injector.get('VideoPlayer');
        $timeout = $injector.get('$timeout');
        $rootScope = $injector.get('$rootScope');
        $scope = $rootScope.$new();
        $scope.workflow = { stage: 'type' };
        $controller('PlaybackModeController', {
            $scope: $scope
        });
        var oldCancel = $scope.playbackTimer.cancel;
        spyOn($scope, 'playbackTimer').andCallThrough();
        $scope.playbackTimer.cancel = oldCancel;
        $scope.$digest();
        VideoPlayer.reset();
    }));

    function invokePlaybackTimerCallback() {
        if($scope.playbackTimer.callCount > 0) {
            var callback = $scope.playbackTimer.mostRecentCall.args[0];
            $scope.playbackTimer.reset();
            callback();
        } else {
            throw Error("no call to playbackTimer()");
        }
    }

    it('pauses when playback mode is switched', function() {
        $scope.playbackMode = 'magic';
        $scope.$digest();
        expect(VideoPlayer.pause).toHaveBeenCalled();
    });

    it('switches to standard mode when we are not in the typing stage', function() {
        $scope.workflow.stage = 'review';
        $scope.$digest();
        expect($scope.currentModeHandler.name).toEqual('standard');
    });

    it('stays in standard mode when not in the typing stage', function() {
        $scope.workflow.stage = 'review';
        $scope.$digest();
        expect($scope.currentModeHandler.name).toEqual('standard');

        $scope.playbackMode = 'magic';
        $scope.$digest();
        expect($scope.currentModeHandler.name).toEqual('standard');
    });


    it('reactivates the old mode if we switch back to the typing stage', function() {
        $scope.playbackMode = 'magic';
        $scope.$digest();
        VideoPlayer.pause.reset();

        $scope.workflow.stage = 'review';
        $scope.$digest();
        expect($scope.currentModeHandler.name).toEqual('standard');

        $scope.workflow.stage = 'type';
        $scope.$digest();
        expect($scope.currentModeHandler.name).toEqual('magic');
    });

    describe('playback mode timer', function() {
        it('uses $timeout to call the timeout function', function() {
            var callback = jasmine.createSpy('callback');
            $scope.playbackTimer(callback, 100);
            expect($timeout).toHaveBeenCalledWith(jasmine.any(Function), 100);

            // Check thet our callback is called once the timeout function is
            // called.
            $timeout.lastCallback();
            expect(callback).toHaveBeenCalled();
        });

        it('cancels the timeout if video is paused', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');

            var callback = jasmine.createSpy('callback');
            $scope.playbackTimer(callback, 100);

            VideoPlayer.pause();
            $rootScope.$emit('video-update');

            expect($timeout.cancel).toHaveBeenCalledWith(
                $timeout.lastPromiseReturned);
        });

        it('cancels the timeout if video is played', function() {
            var callback = jasmine.createSpy('callback');
            $scope.playbackTimer(callback, 100);

            VideoPlayer.play();
            $rootScope.$emit('video-update');

            expect($timeout.cancel).toHaveBeenCalledWith(
                $timeout.lastPromiseReturned);
        });

        it('does not cancel the timeout if the video continously plays', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');

            var callback = jasmine.createSpy('callback');
            $scope.playbackTimer(callback, 100);

            // Emit video-update a couple times.  Since playing hasn't
            // changed, we shouldn't cancel the timeout.
            $rootScope.$emit('video-update');

            expect($timeout.cancel).not.toHaveBeenCalled();
        });

        it('cancels the timeout if the mode is switched', function() {
            var callback = jasmine.createSpy('callback');
            $scope.playbackTimer(callback, 100);

            $scope.playbackMode = 'magic';
            $scope.$digest();

            expect($timeout.cancel).toHaveBeenCalledWith(
                $timeout.lastPromiseReturned);
        });

        it('invokes the error handler on timeout cancel', function() {
            var callback = jasmine.createSpy('callback');
            var errback = jasmine.createSpy('errback');
            $scope.playbackTimer(callback, 100).then(null, errback);

            $scope.playbackMode = 'magic';
            $scope.$digest();

            expect($timeout.cancel).toHaveBeenCalledWith(
                $timeout.lastPromiseReturned);
            expect(errback).toHaveBeenCalled();
        });

        it('only cancels the timeout once', function() {
            var callback = jasmine.createSpy('callback');
            $scope.playbackTimer(callback, 100);

            VideoPlayer.pause();
            $rootScope.$emit('video-update');
            $rootScope.$emit('video-update');
            $scope.playbackMode = 'magic';
            $scope.$digest();

            expect($timeout.cancel.callCount).toEqual(1);
        });

        it('can manually cancel the timeout', function() {
            var callback = jasmine.createSpy('callback');
            var promise = $scope.playbackTimer(callback, 100);

            $scope.playbackTimer.cancel(promise);
            expect($timeout.cancel).toHaveBeenCalledWith($timeout.lastPromiseReturned);
            // check that we don't also automatically cancel the timeout
            $scope.playbackMode = 'magic';
            $scope.$digest();
            expect($timeout.cancel.callCount).toEqual(1);
        });

        it('handles multiple timers at once', function() {
            // create 2 timers
            var callback1 = jasmine.createSpy('callback1');
            var callback2 = jasmine.createSpy('callback2');
            $scope.playbackTimer(callback1, 100);
            var timeoutCallback1 = $timeout.lastCallback;
            $scope.playbackTimer(callback2, 200);
            var timeoutCallback2 = $timeout.lastCallback;
            // fire the first timeout
            timeoutCallback1();
            // make the second one get canceled
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            // Check that the correct callbacks were called
            expect(callback1).toHaveBeenCalled();
            expect(callback2).not.toHaveBeenCalled();
            expect($timeout.cancel).toHaveBeenCalledWith(
                $timeout.lastPromiseReturned);
        });
    });

    describe('beginner mode', function() {
        beforeEach(function() {
            $scope.playbackMode = 'beginner';
            $scope.$digest();
        });

        it('pauses after 4 seconds of playback', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 4000);

            invokePlaybackTimerCallback();
            expect(VideoPlayer.pause).toHaveBeenCalled();

            // check what happens once the video start playing again
            $scope.playbackTimer.reset();
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 4000);
        });

        it('re-schedules the timeout after play/pause/play', function() {
            // This is testing a corner case.  If user plays, pauses, then
            // re-plays the video without timeout ever firing, we should still
            // schedule a second timeout.
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 4000);
            $scope.playbackTimer.reset();

            VideoPlayer.pause();
            $rootScope.$emit('video-update');
            expect($timeout.cancel).toHaveBeenCalledWith($timeout.lastPromiseReturned);
            $rootScope.$digest();
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 4000);
        });

        it('only schedules the timeout once', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            $rootScope.$emit('video-update');
            expect($scope.playbackTimer.callCount).toEqual(1);
        });
    });

    describe('magic mode', function() {
        var initialTime;

        beforeEach(function() {
            $scope.playbackMode = 'magic';
            $scope.$digest();
            VideoPlayer.pause.reset();
            initialTime = VideoPlayer.time;
        });

        it('pauses playback after 4 seconds of typing', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            // once the video start playing, we should schedule a timeout for
            // one second.
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 1000);
            // If the user has typed a key before the timeout, then we should
            // schedule another one.  We shouldn't pause the playback yet
            $rootScope.$emit('subtitle-edit-key-press');
            invokePlaybackTimerCallback();
            expect(VideoPlayer.pause).not.toHaveBeenCalled();
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 1000);

            // We should repeat that 2 more times
            $rootScope.$emit('subtitle-edit-key-press');
            invokePlaybackTimerCallback();
            expect(VideoPlayer.pause).not.toHaveBeenCalled();
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 1000);

            $rootScope.$emit('subtitle-edit-key-press');
            invokePlaybackTimerCallback();
            expect(VideoPlayer.pause).not.toHaveBeenCalled();
            expect($scope.playbackTimer)
                .toHaveBeenCalledWith(jasmine.any(Function), 1000);

            // The next time is the 4th timeout.  We should pause the video if
            // the key pressing continues

            $rootScope.$emit('subtitle-edit-key-press');
            invokePlaybackTimerCallback();
            expect(VideoPlayer.pause).toHaveBeenCalled();
            expect(VideoPlayer.seek).toHaveBeenCalledWith(initialTime - 3000);
        });

        it('does not pauses without 4 seconds of typing', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            // simulate 3 seconds of typing
            for(var i=0; i < 3; i++) {
                expect($scope.playbackTimer)
                    .toHaveBeenCalledWith(jasmine.any(Function), 1000);
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
            }
            // On the first timeout, don't emit the subtitle-edit-key-press
            // signal.  This means the user has stopped typing, so we
            // shouldn't pause
            invokePlaybackTimerCallback();
            expect(VideoPlayer.pause).not.toHaveBeenCalled();
        });

        it('pauses playback after intermittent typing, then 4 seconds of straight typing', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            // For the first 10 seconds, we have key presses only sometimes
            for(var i=0; i < 10; i++) {
                if(i % 2 == 0) {
                    $rootScope.$emit('subtitle-edit-key-press');
                }
                invokePlaybackTimerCallback();
                expect(VideoPlayer.pause).not.toHaveBeenCalled();
            }
            // The next 4 seconds have continous key presses
            for(var i=0; i < 4; i++) {
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
            }
            expect(VideoPlayer.pause).toHaveBeenCalled();
        });

        it('seeks back 3 seconds and restarts playback once typing stops after a magic pause', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            VideoPlayer.play.reset();
            for(var i=0; i < 4; i++) {
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
            }
            expect(VideoPlayer.pause).toHaveBeenCalled();
            $rootScope.$emit('video-update');
            // Similuate typing for a few more seconds
            for(var i=0; i < 2; i++) {
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
                expect(VideoPlayer.play).not.toHaveBeenCalled();
            }
            // Now simulate stopping typing for 1 second
            invokePlaybackTimerCallback();
            expect(VideoPlayer.play).toHaveBeenCalled();
        });

        it('does not seek back before time=0', function() {
            VideoPlayer.time = 2000;
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            for(var i=0; i < 4; i++) {
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
            }
            expect(VideoPlayer.seek).toHaveBeenCalledWith(0);
        });

        it('does not restart on manual pauses', function() {
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            $rootScope.$emit('subtitle-edit-key-press');
            invokePlaybackTimerCallback();
            // If the user manually pauses the video, we shouldn't schedule a
            // callback to play it again.
            $scope.playbackTimer.reset();
            VideoPlayer.pause();
            $rootScope.$emit('video-update');
            expect($scope.playbackTimer).not.toHaveBeenCalled();
        });

        it('reschedules a timeout after manual play/pause/play', function() {
            // This is testing a corner case of the user playing video, then
            // pausing, and replaying it before any timeout gets called.  We
            // should still reschedule a timeout to pause the video.
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            VideoPlayer.pause();
            $rootScope.$emit('video-update');
            $scope.$digest();
            $scope.playbackTimer.reset();
            VideoPlayer.play();
            $rootScope.$emit('video-update');

            expect($scope.playbackTimer).toHaveBeenCalled();
        });

        it('keeps pausing/restarting as the user types', function() {
            // This method tests going through multiple cycles of the
            // play/pause workflow
            VideoPlayer.play();
            $rootScope.$emit('video-update');
            // User types for 4 seconds straight, we should pause
            for(var i=0; i < 4; i++) {
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
            }
            expect(VideoPlayer.pause).toHaveBeenCalled();
            VideoPlayer.pause.reset();
            $rootScope.$emit('video-update');
            // User stops typing for a second, we should play
            invokePlaybackTimerCallback();
            expect(VideoPlayer.play).toHaveBeenCalled();
            $rootScope.$emit('video-update');
            VideoPlayer.play.reset();
            // User types for 4 seconds straight, we should pause again
            for(var i=0; i < 4; i++) {
                $rootScope.$emit('subtitle-edit-key-press');
                invokePlaybackTimerCallback();
            }
            expect(VideoPlayer.pause).toHaveBeenCalled();
            $rootScope.$emit('video-update');
            VideoPlayer.pause.reset();
            // User stops typing for a second, we should play again
            invokePlaybackTimerCallback();
            expect(VideoPlayer.play).toHaveBeenCalled();
            VideoPlayer.play.reset();
        });
    });
});
