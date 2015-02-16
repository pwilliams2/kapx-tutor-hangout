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
var tutorName = '';
var localParticipant;
var count = 0;
var participants_ = null;
var subjects_ = '';


// Post a heartbeat to inform host that this tutor H-O is still available
function heartBeat() {
    httpRequest('GET', SERVER_PATH, 'heartbeat', 'gid=' + gid + '&pid=' + pid + "&count=" + count);
}

function httpRequest(method, server, path, params) {
    console.log('method: ' + method + ' path: ' + path + ' params: ' + params);

    var http = new XMLHttpRequest();

    http.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var jsonResponse = JSON.parse(http.responseText);
        }
        else {
            console.log("readyState: " + this.readyState)
            console.log("status: " + this.status)
            //console.log("statusText: " + http.responseText)
        }
    }
    if (method && method.toUpperCase() == "GET") {
        //e.g. path == "subscribe", params == gid="gasdfsfsfssdfdsfs"
        http.open('GET', server + path + '?' + params);
        http.send();
    }
    else if ((method && method.toUpperCase() == "POST")) {
        http.open('POST', server + path);
        http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        http.send(params);
    }
}

// Publish tutor availability for subject(s)
function publish(subjects) {
    console.log('Selected subject' + subjects);
    subjects_ = subjects;
    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];
    pid = localParticipant.person.id;

    var payload = 'subjects=' + subjects
        + '&gid=' + gid
        + '&pid=' + pid
        + '&pName=' + localParticipant.person.displayName
        + '&count=' + count
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
    + participants.length + ' count == ' + count);

    participants_ = participants;
    for (i = 0; i < participants.length; i++) {
        console.log('part ' + i + ' == ' + participants[i].person.id);
    }

    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];

    if (participants.length > 1 && participants.length > count) {//Add
        var appData = gadgets.views.getParams()['appData'];
        console.log('appData:' + appData);
        console.log('subscribing...');
        $('.clientParticipant').html(participants_[0].person.displayName);

        httpRequest('POST', SERVER_PATH, 'subscribe',
            'tutorId=' + pid
            + '&subjects=' + subjects_
            + '&tutorName=' + tutorName
            + '&gid=' + gid
            + '&studentId=' + participants_[0].person.id
            + '&studentName=' + participants_[0].person.displayName);
    }
    else if (participants.length < count && count > 1) {
        console.log('unsubscribing...');
        $('.clientParticipant').html("");

        httpRequest('POST', SERVER_PATH, 'unsubscribe',
            'studentId=' + participants_[participants_.length - 1].person.id
            + '&tutorId=' + pid
            + '&gid=' + gid
            + '&exit=True');
    }
    count = participants.length; // Update the count
}


function postSurvey() {
    console.log('postSurvey');
    payload = 'student_id=' + localParticipant.person.id
    + '&subjects=' + subjects_
    + '&tutor_name=' + tutorName
    + '&student_name=' + localParticipant.person.displayName
    + '&gid=' + gid
    + '&knowledge=' + $('#spinknow').val()
    + '&communications=' + $('#spincomm').val()
    + '&overall=' + $('#spinall').val()
    + '&comments=' + $('#comments').val();

    try {
        $('#clientMessage').html("");
        httpRequest('POST', SERVER_PATH, 'surveys/data', payload);
        $('#clientMessage').html("Submitted");
    } catch (e) {
        console.log(e);
    }
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

            if (startData && startData.length > 1) {
                $('#tutor-view').removeClass('hidden');
                $('#student-view').addClass('hidden');

                // Start heartbeat, but only run for tutor
                $(function () { //reload page 20 seconds
                    setInterval(function () {
                        heartBeat();
                    }, 20000);
                });
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

$(function () {
    console.log('loading subjects');
    var id = 0,
        getRows = function () {

            var rows = [
                {"subject": "Business"},
                {"subject": "General Math"},
                {"subject": "Calculus"},
                {"subject": "Science"},
                {"subject": "Technology"},
                {"subject": "Writing"}
            ];

            return rows;
        },
    // init table use data
        $table = $('#subjectTable').bootstrapTable({
            data: getRows()
        });

    // $table is defined above
    $('#btn-subjects').click(function () {
        publish(JSON.stringify($table.bootstrapTable('getSelections')));
    });

    $('#btn-survey').click(function () {
        postSurvey();
    });

});

$(function () {
    $('.aSpinEdit').spinedit({
        minimum: 0,
        maximum: 5,
        step: .25,
        numberOfDecimals: 2
    });

});


gadgets.util.registerOnLoadHandler(init);