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

var angular = angular || null;

(function() {
    /*
     * amara.subtitles.models
     *
     * Define model classes that we use for subtitles
     */

    var module = angular.module('amara.SubtitleEditor.subtitles.models', []);

    function emptyDFXP(languageCode) {
        /* Get a DFXP string for an empty subtitle set */
        return '<tt xmlns="http://www.w3.org/ns/ttml" xmlns:tts="http://www.w3.org/ns/ttml#styling" xml:lang="' + languageCode + '">\
    <head>\
        <metadata xmlns:ttm="http://www.w3.org/ns/ttml#metadata">\
            <ttm:title/>\
            <ttm:description/>\
            <ttm:copyright/>\
        </metadata>\
        <styling>\
            <style xml:id="amara-style" tts:color="white" tts:fontFamily="proportionalSansSerif" tts:fontSize="18px" tts:backgroundColor="transparent" tts:textOutline="black 1px 0px" tts:textAlign="center"/>\
        </styling>\
        <layout>\
            <region xml:id="bottom" style="amara-style" tts:extent="100% 20%" tts:origin="0 80%" />\
            <region xml:id="top" style="amara-style" tts:extent="100% 20%" tts:origin="0 0" tts:textAlign="center"/>\
        </layout>\
    </head>\
    <body region="bottom"><div /></body>\
</tt>';
    };

    function Subtitle(startTime, endTime, markdown, startOfParagraph) {
        /* Represents a subtitle in our system
         *
         * Subtitle has the following properties:
         *   - startTime -- start time in seconds
         *   - endTime -- end time in seconds
         *   - markdown -- subtitle content in our markdown-style format
         */
        this.startTime = startTime;
        this.endTime = endTime;
        this.markdown = markdown;
        this.startOfParagraph = startOfParagraph;
    }

    Subtitle.prototype.duration = function() {
        if(this.isSynced()) {
            return this.endTime - this.startTime;
        } else {
            return -1;
        }
    }

    Subtitle.prototype.hasWarning = function(type, data) {
	if ((type == "lines" || type == undefined) && (this.lineCount() > 2))
	    return true;
	if ((type == "characterRate" || type == undefined) && (this.characterRate() > 21))
	    return true;
	if ((type == "timing" || type == undefined) && ((this.startTime > -1) && (this.endTime > -1) && (this.endTime - this.startTime < 700)))
	    return true;
	if (type == "longline" || type == undefined) {
	    if (type == "longline" && (data == undefined) && ((this.characterCountPerLine().length == 1) && (this.characterCountPerLine()[0] > 42)))
		return true;
	    var from = (data == undefined) ? 0 : data;
	    var to = (data == undefined) ? (this.characterCountPerLine().length) : (data + 1);
	    for (var i = from ; i < to ; i++) {
		if (this.characterCountPerLine()[i] > 42)
		    return true;
	    }
	}
	return false;
    }

    Subtitle.prototype.content = function() {
        /* Get the content of this subtitle as HTML */
        return dfxp.markdownToHTML(this.markdown);
    }

    Subtitle.prototype.isEmpty = function() {
        return this.markdown == '';
    }

    Subtitle.prototype.characterCount = function() {
        var rawContent = dfxp.markdownToPlaintext(this.markdown);
        // Newline characters are not counted
        return (rawContent.length - (rawContent.match(/\n/g) || []).length);
    }

    Subtitle.prototype.characterRate = function() {
        if(this.isSynced()) {
            return (this.characterCount() * 1000 / this.duration()).toFixed(1);
        } else {
            return "0.0";
        }
    }

    Subtitle.prototype.lineCount = function() {
        return this.markdown.split("\n").length;
    }

    Subtitle.prototype.characterCountPerLine = function() {
        var lines = this.markdown.split("\n");
        var counts = [];
        for(var i = 0; i < lines.length; i++) {
            counts.push(dfxp.markdownToPlaintext(lines[i]).length);
        }
        return counts;
        
    }

    Subtitle.prototype.isSynced = function() {
        return this.startTime >= 0 && this.endTime >= 0;
    }

    Subtitle.prototype.isAt = function(time) {
        return this.isSynced() && this.startTime <= time && this.endTime > time;
    }

    Subtitle.prototype.startTimeSeconds = function() {
        if(this.startTime >= 0) {
            return this.startTime / 1000;
        } else {
            return -1;
        }
    }

    Subtitle.prototype.endTimeSeconds = function() {
        if(this.endTime >= 0) {
            return this.endTime / 1000;
        } else {
            return -1;
        }
    }

    function StoredSubtitle(parser, node, id) {
        /* Subtitle stored in a SubtitleList
         *
         * You should never change the proporties on a stored subtitle directly.
         * Instead use the updateSubtitleContent() and updateSubtitleTime()
         * methods of SubtitleList.
         *
         * If you want a subtitle object that you can change the times/content
         * without saving them to the DFXP store, use the draftSubtitle() method
         * to get a DraftSubtitle.
         * */
        var text = $(node).text().trim();
        Subtitle.call(this, parser.startTime(node), parser.endTime(node),
                text, parser.startOfParagraph(node));
        this.node = node;
        this.id = id;
    }

    StoredSubtitle.prototype = Object.create(Subtitle.prototype);
    StoredSubtitle.prototype.draftSubtitle = function() {
        return new DraftSubtitle(this);
    }
    StoredSubtitle.prototype.isDraft = false;

    function DraftSubtitle(storedSubtitle) {
        /* Subtitle that we are currently changing */
        Subtitle.call(this, storedSubtitle.startTime, storedSubtitle.endTime,
                storedSubtitle.markdown);
        this.storedSubtitle = storedSubtitle;
    }

    DraftSubtitle.prototype = Object.create(Subtitle.prototype);
    DraftSubtitle.prototype.isDraft = true;

    var SubtitleList = function() {
        /*
         * Manages a list of subtitles.
         *
         * For functions that return subtitle items, each item is a dict with the
         * following properties:
         *   - startTime -- start time in seconds
         *   - endTime -- end time in seconds
         *   - content -- string of html for the subtitle content
         *   - node -- DOM node from the DFXP XML
         *
         */

        this.parser = new AmaraDFXPParser();
        this.idCounter = 0;
        this.subtitles = [];
        this.syncedCount = 0;
        this.changeCallbacks = [];
    }

    SubtitleList.prototype.contentForMarkdown = function(markdown) {
        return dfxp.markdownToHTML(markdown);
    }

    SubtitleList.prototype.loadEmptySubs = function(languageCode) {
        this.loadXML(emptyDFXP(languageCode));
    }

    SubtitleList.prototype.loadXML = function(subtitlesXML) {
        this.parser.init(subtitlesXML);
        var syncedSubs = [];
        var unsyncedSubs = [];
        // Needed because each() changes the value of this
        var self = this;
        this.parser.getSubtitles().each(function(index, node) {
            var subtitle = self.makeItem(node);
            if(subtitle.isSynced()) {
                syncedSubs.push(subtitle);
            } else {
                unsyncedSubs.push(subtitle);
            }
        });
        syncedSubs.sort(function(s1, s2) {
            return s1.startTime - s2.startTime;
        });
        this.syncedCount = syncedSubs.length;
        // Start with synced subs to the list
        this.subtitles = syncedSubs;
        // append all unsynced subs to the list
        this.subtitles.push.apply(this.subtitles, unsyncedSubs);
        this.emitChange('reload', null);
    }

    SubtitleList.prototype.addSubtitlesFromBaseLanguage = function(xml) {
        /*
         * Used when we are translating from one language to another.
         * It loads the latest subtitles for xml and inserts blank subtitles
         * with the same timings and paragraphs into our subtitle list.
         */
        var baseLanguageParser = new AmaraDFXPParser();
        baseLanguageParser.init(xml);
        var baseAttributes = [];
        baseLanguageParser.getSubtitles().each(function(index, node) {
            startTime = baseLanguageParser.startTime(node);
            endTime = baseLanguageParser.endTime(node);
            startOfParagraph = baseLanguageParser.startOfParagraph(node);
            if(startTime >= 0 && endTime >= 0) {
                baseAttributes.push({
                    'startTime': startTime,
                    'endTime': endTime,
                    'startOfParagraph': startOfParagraph
                });
            }
        });
        baseAttributes.sort(function(s1, s2) {
            return s1.startTime - s2.startTime;
        });
        var that = this;
        _.forEach(baseAttributes, function(baseAttribute) {
            var node = that.parser.addSubtitle(null, {
                begin: baseAttribute.startTime,
                end: baseAttribute.endTime,
            });
            that.parser.startOfParagraph(node, baseAttribute.startOfParagraph);
            that.subtitles.push(that.makeItem(node));
            that.syncedCount++;
        });
        this.emitChange('reload', null);
    }

    SubtitleList.prototype.addChangeCallback = function(callback) {
        this.changeCallbacks.push(callback);
    }

    SubtitleList.prototype.removeChangeCallback = function(callback) {
        var pos = this.changeCallbacks.indexOf(callback);
        if(pos >= 0) {
            this.changeCallbacks.splice(pos, 1);
        }
    }

    SubtitleList.prototype.emitChange = function(type, subtitle, extraProps) {
        changeObj = { type: type, subtitle: subtitle };
        if(extraProps) {
            for(key in extraProps) {
                changeObj[key] = extraProps[key];
            }
        }
        for(var i=0; i < this.changeCallbacks.length; i++) {
            this.changeCallbacks[i](changeObj);
        }
    }

    SubtitleList.prototype.makeItem = function(node) {
        var idKey = (this.idCounter++).toString(16);

        return new StoredSubtitle(this.parser, node, idKey);
    }

    SubtitleList.prototype.length = function() {
        return this.subtitles.length;
    }

    SubtitleList.prototype.needsAnyTranscribed = function() {
        for(var i=0; i < this.length(); i++) {
            if(this.subtitles[i].markdown == '') {
                return true;
            }
        }
        return false;
    }

    SubtitleList.prototype.needsAnySynced = function() {
        return this.syncedCount < this.length();
    }

    SubtitleList.prototype.isComplete = function() {
        return (this.length() > 0 &&
                !this.needsAnyTranscribed() &&
                !this.needsAnySynced());
    }

    SubtitleList.prototype.toXMLString = function() {
        return this.parser.xmlToString(true, true);
    }

    SubtitleList.prototype.getIndex = function(subtitle) {
        // Maybe a binary search would be faster, but I think Array.indexOf should
        // be pretty optimized on most browsers.
        return this.subtitles.indexOf(subtitle);
    }

    SubtitleList.prototype.nextSubtitle = function(subtitle) {
        if(subtitle === this.subtitles[this.length() - 1]) {
            return null;
        } else {
            return this.subtitles[this.getIndex(subtitle) + 1];
        }
    }

    SubtitleList.prototype.prevSubtitle = function(subtitle) {
        if(subtitle === this.subtitles[0]) {
            return null;
        } else {
            return this.subtitles[this.getIndex(subtitle) - 1];
        }
    }

    SubtitleList.prototype._updateSubtitleTime = function(subtitle, startTime, endTime) {
        var wasSynced = subtitle.isSynced();
        if(subtitle.startTime != startTime) {
            this.parser.startTime(subtitle.node, startTime);
            subtitle.startTime = startTime;
        }
        if(subtitle.endTime != endTime) {
            this.parser.endTime(subtitle.node, endTime);
            subtitle.endTime = endTime;
        }
        if(subtitle.isSynced() && !wasSynced) {
            this.syncedCount++;
        }
        if(!subtitle.isSynced() && wasSynced) {
            this.syncedCount--;
        }
	
    }

    SubtitleList.prototype.updateSubtitleTime = function(subtitle, startTime, endTime) {
        this._updateSubtitleTime(subtitle, startTime, endTime);
        this.emitChange('update', subtitle);
    }

    SubtitleList.prototype._updateSubtitleContent = function(subtitle, content) {
        /* Update subtilte content
         *
         * content is a string in our markdown-style format.
         */
        this.parser.content(subtitle.node, content);
        subtitle.markdown = content;
    }

    SubtitleList.prototype.updateSubtitleContent = function(subtitle, content) {
        this._updateSubtitleContent(subtitle, content);
        this.emitChange('update', subtitle);
    }

    SubtitleList.prototype._updateSubtitleParagraph = function(subtitle, startOfParagraph) {
        this.parser.startOfParagraph(subtitle.node, startOfParagraph);
    }

    SubtitleList.prototype.updateSubtitleParagraph = function(subtitle, startOfParagraph) {
        // If startOfParagraph is not given, it is toggled
        var newStartOfParagraph = (startOfParagraph == undefined) ? !(this.parser.startOfParagraph(subtitle.node)) : startOfParagraph;
        this._updateSubtitleParagraph(subtitle, newStartOfParagraph);
        subtitle.startOfParagraph = newStartOfParagraph;
        this.emitChange('update', subtitle);
    }

    SubtitleList.prototype.getSubtitleParagraph = function(subtitle) {
	return this.parser.startOfParagraph(subtitle.node);
    }

    SubtitleList.prototype.insertSubtitleBefore = function(otherSubtitle) {
        if(otherSubtitle !== null) {
            var pos = this.getIndex(otherSubtitle);
        } else {
            var pos = this.subtitles.length;
        }
        // We insert the subtitle before the reference point, but AmaraDFXPParser
        // wants to insert it after, so we need to adjust things a bit.
        if(pos > 0) {
            var after = this.subtitles[pos-1].node;
        } else {
            var after = -1;
        }
        if(otherSubtitle && otherSubtitle.isSynced()) {
            // If we are inserting between 2 synced subtitles, then we can set the
            // time
            if(pos > 0) {
                // Inserting a subtitle between two others.  Make it so each
                // subtitle takes up 1/3 of the time available
                var firstSubtitle = this.prevSubtitle(otherSubtitle);
                var totalTime = otherSubtitle.endTime - firstSubtitle.startTime;
                var durationSplit = Math.floor(totalTime / 3);
                var startTime = firstSubtitle.startTime + durationSplit;
                var endTime = startTime + durationSplit;
                this._updateSubtitleTime(firstSubtitle, firstSubtitle.startTime,
                        startTime);
                this._updateSubtitleTime(otherSubtitle, endTime, otherSubtitle.endTime);
            } else {
                // Inserting a subtitle as the start of the list.  position the
                // subtitle to start at time=0 and take up half the space
                // available to the two subtitles
                var startTime = 0;
                var endTime = Math.floor(otherSubtitle.endTime / 2);
                this._updateSubtitleTime(otherSubtitle, endTime, otherSubtitle.endTime);
            }
            attrs = {
                begin: startTime,
                end: endTime,
            }
        } else {
            attrs = {}
        }
        var node = this.parser.addSubtitle(after, attrs);
        var subtitle = this.makeItem(node);
        if(otherSubtitle != null) {
            this.subtitles.splice(pos, 0, subtitle);
        } else {
            this.subtitles.push(subtitle);
        }
        if(subtitle.isSynced()) {
            this.syncedCount++;
        }
        this.emitChange('insert', subtitle, { 'before': otherSubtitle});
        return subtitle;
    }

    SubtitleList.prototype.removeSubtitle = function(subtitle) {
        var pos = this.getIndex(subtitle);
        this.parser.removeSubtitle(subtitle.node);
        this.subtitles.splice(pos, 1);
        if(subtitle.isSynced()) {
            this.syncedCount--;
        }
        this.emitChange('remove', subtitle);
    }

    SubtitleList.prototype.lastSyncedSubtitle = function() {
        if(this.syncedCount > 0) {
            return this.subtitles[this.syncedCount - 1];
        } else {
            return null;
        }
    }

    SubtitleList.prototype.firstUnsyncedSubtitle = function() {
        if(this.syncedCount < this.subtitles.length) {
            return this.subtitles[this.syncedCount];
        } else {
            return null;
        }
    }

    SubtitleList.prototype.secondUnsyncedSubtitle = function() {
        if(this.syncedCount + 1 < this.subtitles.length) {
            return this.subtitles[this.syncedCount + 1];
        } else {
            return null;
        }
    }

    SubtitleList.prototype.indexOfFirstSubtitleAfter = function(time) {
        /* Get the first subtitle whose end is after time
         *
         * returns index of the subtitle, or -1 if none are found.
         */

        // Do a binary search to find the sub
        var left = 0;
        var right = this.syncedCount-1;
        // First check that we are going to find any subtitle
        if(right < 0 || this.subtitles[right].endTime <= time) {
            return -1;
        }
        // Now do the binary search
        while(left < right) {
            var index = Math.floor((left + right) / 2);
            if(this.subtitles[index].endTime > time) {
                right = index;
            } else {
                left = index + 1;
            }
        }
        return left;
    }

    SubtitleList.prototype.firstSubtitle = function() {
        return this.subtitles[this.indexOfFirstSubtitleAfter(-1)] ||
               this.firstUnsyncedSubtitle();
    }

    SubtitleList.prototype.subtitleAt = function(time) {
        /* Find the subtitle that occupies a given time.
         *
         * returns a StoredSubtitle, or null if no subtitle occupies the time.
         */
        var i = this.indexOfFirstSubtitleAfter(time);
        if(i == -1) {
            return null;
        }
        var subtitle = this.subtitles[i];
        if(subtitle.isAt(time)) {
            return subtitle;
        } else {
            return null;
        }
    }

    SubtitleList.prototype.getSubtitlesForTime = function(startTime, endTime) {
        var rv = [];
        var i = this.indexOfFirstSubtitleAfter(startTime);
        if(i == -1) {
            return rv;
        }
        for(; i < this.syncedCount; i++) {
            var subtitle = this.subtitles[i];
            if(subtitle.startTime < endTime) {
                rv.push(subtitle);
            } else {
                break;
            }
        }
        return rv;
    }

    /* CurrentEditManager manages the current in-progress edit
     */
    CurrentEditManager = function() {
        this.draft = null;
        this.LI = null;
    }

    CurrentEditManager.prototype = {
        start: function(subtitle, LI) {
            this.draft = subtitle.draftSubtitle();
            this.LI = LI;
        },
        finish: function(commitChanges, subtitleList) {
            var updateNeeded = (commitChanges && this.changed());
            if(updateNeeded) {
                subtitleList.updateSubtitleContent(this.draft.storedSubtitle,
                        this.currentMarkdown());
            }
            this.draft = this.LI = null;
            return updateNeeded;
        },
        storedSubtitle: function() {
            if(this.draft !== null) {
                return this.draft.storedSubtitle;
            } else {
                return null;
            }
        },
        sourceMarkdown: function() {
            return this.draft.storedSubtitle.markdown;
        },
        currentMarkdown: function() {
            return this.draft.markdown;
        },
        changed: function() {
            return this.sourceMarkdown() != this.currentMarkdown();
        },
         update: function(markdown) {
            if(this.draft !== null) {
                this.draft.markdown = markdown;
            }
         },
         isForSubtitle: function(subtitle) {
            return (this.draft !== null && this.draft.storedSubtitle == subtitle);
         },
         inProgress: function() {
            return this.draft !== null;
         },
         lineCounts: function() {
             if(this.draft === null || this.draft.lineCount() < 2) {
                 // Only show the line counts if there are 2 or more lines
                 return null;
             } else {
                 return this.draft.characterCountPerLine();
             }
         },
    };

    /*
     * SubtitleVersionManager: handle the active subtitle version for the
     * reference and working subs.
     *
     */

    SubtitleVersionManager = function(video, SubtitleStorage) {
        this.video = video;
        this.SubtitleStorage = SubtitleStorage;
        this.subtitleList = new SubtitleList();
        this.versionNumber = null;
        this.language = null;
        this.title = null;
        this.description = null;
        this.state = 'waiting';
        this.metadata = {};
    }

    SubtitleVersionManager.prototype = {
        getSubtitles: function(languageCode, versionNumber) {
            this.setLanguage(languageCode);
            this.versionNumber = versionNumber;
            this.state = 'loading';

            var that = this;

            this.SubtitleStorage.getSubtitles(languageCode, versionNumber,
                    function(subtitleData) {
                that.state = 'loaded';
                that.title = subtitleData.title;
                that.initMetadataFromVideo();
                for(key in subtitleData.metadata) {
                    that.metadata[key] = subtitleData.metadata[key];
                }
                that.description = subtitleData.description;
                that.subtitleList.loadXML(subtitleData.subtitles);
            });
        },
        initEmptySubtitles: function(languageCode, baseLanguage) {
            this.setLanguage(languageCode);
            this.versionNumber = null;
            this.title = '';
            this.description = '';
            this.subtitleList.loadEmptySubs(languageCode);
            this.state = 'loaded';
            this.initMetadataFromVideo();
            if(baseLanguage) {
                this.addSubtitlesFromBaseLanguage(baseLanguage);
            }
        },
        initMetadataFromVideo: function() {
            this.metadata = {};
            for(key in this.video.metadata) {
                this.metadata[key] = '';
            }
        },
        addSubtitlesFromBaseLanguage: function(baseLanguage) {
            var that = this;
            this.SubtitleStorage.getSubtitles(baseLanguage, null,
                    function(subtitleData) {
                that.subtitleList.addSubtitlesFromBaseLanguage(
                    subtitleData.subtitles);
            });
        },
        setLanguage: function(code) {
            this.language = this.SubtitleStorage.getLanguage(code);
        },
        getTitle: function() {
            return this.title || this.video.title;
        },
        getDescription: function() {
            if(!this.language) {
                return '';
            } else if(this.language.isPrimaryAudioLanguage) {
                return this.description || this.video.description;
            } else {
                return this.description;
            }
        },
        getMetadata: function() {
            var metadata = _.clone(this.metadata);
            if(this.language.isPrimaryAudioLanguage) {
                for(key in metadata) {
                    if(!metadata[key]) {
                        metadata[key] = this.video.metadata[key];
                    }
                }
            }
            return metadata;
        }
    };

    /* Export modal classes as values.  This makes testing and dependency
     * injection easier.
     */

    module.value('CurrentEditManager', CurrentEditManager);
    module.value('SubtitleVersionManager', SubtitleVersionManager);
    module.value('SubtitleList', SubtitleList);
}(this));
