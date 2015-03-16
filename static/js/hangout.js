/**
 * Created by admin on 1/13/15.
 */
/*
 * Copyright (c) 2011 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */
var SERVER_PATH = '//kx-tutor-hangout-app.appspot.com/';
var MAX_COUNT = 2;
var hangoutURL = '';
var gid = '';
var pid = '';
var studentId = '';
var tutorName = '';
var localParticipant;
var participant_count = 0;
var participants_ = null;
var subjects_ = '';
var jsonSubjects_ = null;


// Post a heartbeat to inform host that this tutor H-O is still available
function heartBeat() {
    httpRequest('GET', SERVER_PATH, 'heartbeat', 'gid=' + gid + '&pid=' + pid + "&count=" + participant_count);
}


// Publish tutor availability for subject(s)
function publish(subjects) {
    jsonSubjects_ = subjects[0].subject;  // Used in updateParticipantsUi to display subject
    subjects_ = JSON.stringify(subjects);
    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];
    pid = localParticipant.person.id;

    var payload = 'subjects=' + subjects_
        + '&gid=' + gid
        + '&pid=' + pid
        + '&pName=' + localParticipant.person.displayName
        + '&count=' + participant_count
        + '&maxParticipants=' + MAX_COUNT;

    try {
        $('#message').html("");
        httpRequest('POST', SERVER_PATH, 'publishsubjects', payload);
        $('#message').html("Submitted");
    } catch (e) {
        console.log(e);
    }

}

function updateStateUi(state) {
    var countElement = document.getElementById('count');
    var stateCount = state['count'];
    if (!stateCount) {
        console.log('probably 0');
    } else {
        console.log(stateCount.toString());
    }
}


function updateParticipantsUi(participants) {
    console.log('updateParticipants: Participants length == '
    + participants.length + ' count == ' + participant_count);

    participants_ = participants;
    for (i = 0; i < participants.length; i++) {
        console.log('part ' + i + ' == ' + participants[i].person.id);
    }

    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];

    if (participants.length > 1 && participants.length > participant_count) {//Add
        var appData = gadgets.views.getParams()['appData'];
        console.log('appData:' + appData);
        console.log('subscribing...');
        console.log('subject: ' + jsonSubjects_);
        $('.subject').html(jsonSubjects_);
        $('.clientParticipant').html(participants_[participants.length - 1].person.displayName);

        studentId = participants_[0].person.id;
        httpRequest('POST', SERVER_PATH, 'subscribe',
            'tutorId=' + pid
            + '&subjects=' + subjects_
            + '&tutorName=' + tutorName
            + '&gid=' + gid
            + '&studentId=' + studentId
            + '&studentName=' + participants_[0].person.displayName);
    }
    else if (participants.length < participant_count && participant_count > 1) {
        console.log('unsubscribing...');
        $('.clientParticipant').html("");

        httpRequest('POST', SERVER_PATH, 'unsubscribe',
            'studentId=' + studentId
            + '&tutorId=' + pid
            + '&gid=' + gid
            + '&exit=True');
    }
    participant_count = participants.length; // Update the count
}

// A function to be run at app initialization time which registers our callbacks
function init() {
    console.log('Init app.');

    var apiReady = function (eventObj) {
        if (eventObj.isApiReady) {
            console.log('API is ready');

            hangoutURL = gapi.hangout.getHangoutUrl();
            var arr = hangoutURL.split('/');
            gid = arr[arr.length - 1];
            console.log('hangoutUrl: ' + hangoutURL);

            localParticipant = gapi.hangout.getLocalParticipant();  //TutorSubjects
            tutorName = localParticipant.person.displayName
            $('.instructor').html(tutorName);

            var startData = gapi.hangout.getStartData();
            console.log('start_data: ' + startData);

            if (startData && startData.length > 1 && startData.toLowerCase() == 'tutor') {
                $('#tutor-view').removeClass('hidden');
                $('#student-view').addClass('hidden');

                // Start heartbeat, but only run for tutor
                $(function () { //reload page 20 seconds
                    setInterval(function () {
                        heartBeat();
                    }, 60000);
                });
            }

            try {
                if (gapi.hangout.av.hasCamera())
                    gapi.hangout.av.setCameraMute(1);
            } catch (e) {
                console.log('camera: ' + e.message);
            }

            gapi.hangout.data.onStateChanged.add(function (eventObj) {
                updateStateUi(eventObj.state);
            });

            gapi.hangout.onParticipantsChanged.add(function (eventObj) {
                updateParticipantsUi(eventObj.participants);
            });

            gapi.hangout.onApiReady.remove(apiReady);
        }
    };

    gapi.hangout.onApiReady.add(apiReady);
}

gadgets.util.registerOnLoadHandler(init);