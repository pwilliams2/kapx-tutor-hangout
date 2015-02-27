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
var gid = 'gxx5k3fvmhehr5y2jy3utw2lmma';
var pid = '106169527894682623483';
var student_id = '112559088293509078499';
var tutorName = '';
var localParticipant;
var count = 0;
var participants_ = null;
var subjects_ = '';

// Publish tutor availability for subject(s)
function publish(subjects) {

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
            console.log("statusText: " + http.responseText)
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
    console.log(server + path + '?' + params);
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

// Post a heartbeat to inform host that this tutor H-O is still available
function heartBeat() {
    httpRequest('GET', SERVER_PATH, 'heartbeat', 'gid=' + gid + '&pid=' + pid + "&count=" + count);
}

function postSurvey() {
    console.log('postSurvey');

    console.log('know: ' + $('#spinknow').val());
    console.log('comm: ' + $('#spincomm').val());
    console.log('overall : ' + $('#spinall').val());
    console.log('comments: ' + $('#comments').val());

    //payload = 'student_id=' + student_id
    //+ '&subjects=' + subjects_
    //+ '&tutorName=' + tutorName
    //+ '&gid=' + gid
    //+ '&knowledge=' + $('#spinknow').html()
    //+ '&communications=' + $('#spincomm').text()
    //+ '&overall=' + $('#spinall').text()
    //+ '&comments=' + $('#comments').text();
    //
    //try {
    //    $('#clientMessage').html("");
    //    httpRequest('POST', SERVER_PATH, 'surveys', payload);
    //    $('#clientMessage').html("Submitted");
    //} catch (e) {
    //    console.log(e);
    //}
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
        var subjects = $table.bootstrapTable('getSelections');
        console.log(subjects[0].subject);
        $('#subject').html(subjects[0].subject)
        publish(JSON.stringify($table.bootstrapTable('getSelections')));
    });

    $('#btn-survey').click(function () {
        postSurvey();
    });

     $('#btn-calendar').click(function () {
        $('#app-calendar').toggleClass('hidden');
         $('#app-calculator').addClass('hidden');
    });

      $('#btn-calculator').click(function () {
        $('#app-calculator').toggleClass('hidden');
        $('#app-calendar').addClass('hidden');
    });

    $('.today').html(getDate());

    webix.ui({
				container:"app-calendar",
				weekHeader:true,
				view:"calendar",
				events:webix.Date.isHoliday,
				timepicker:true,
                width:240
			});

});



//gadgets.util.registerOnLoadHandler(init);