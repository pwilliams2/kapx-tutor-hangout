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
var gid ='';
var pid = '';
var tutorName='';
var localParticipant;
var count = 0;
var requestedSubject='';
var participants_ = null;

// Publish tutor availability for subject(s)
function publish(subjects) {
    console.log('Selected subject' + subjects);
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
        httpRequest('POST', 'publishsubjects', payload);
        $('#message').html("Submitted");
    }catch (e) {
        console.log(e);
    }

}

function httpRequest(method, path, params)
{
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
        http.open('GET', SERVER_PATH + path + '?' + params );
        http.send();
    }
    else if ((method && method.toUpperCase() == "POST")) {
        http.open('POST', SERVER_PATH + path);
        http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        http.send(params);
    }
    console.log(SERVER_PATH + path + '?' + params);
    
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
    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];

    participants_ = participants;
    if (participants.length > 1 && participants.length > count) {//Add
        console.log('subscribing...');
        $('.clientParticipant').html(participants_[0].person.displayName);

        httpRequest('POST','subscribe',
            'tutorId=' + pid
            + '&tutorName=' + tutorName
            + '&gid=' + gid
            + '&studentId=' + participants_[0].person.id
            + '&studentName=' + participants_[0].person.displayName);
    }
    else if (participants.length < count && count > 1) {
        console.log('unsubscribing...');
         $('.clientParticipant').html("");

         httpRequest('POST','unsubscribe',
            'studentId=' + participants_[0].person.id
            + '&tutorId=' + pid
            + '&gid=' + gid
            + '&exit=True');
    }
    count = participants.length; // Update the count
}



// Post a heartbeat to inform host that this tutor H-O is still available
function heartBeat()
{
    httpRequest('GET', 'heartbeat', 'gid=' + gid + '&pid=' + pid + "&count=" + count);
}

// A function to be run at app initialization time which registers our callbacks
function init() {
    console.log('Init app.');

    var apiReady = function (eventObj) {
        if (eventObj.isApiReady) {
            console.log('API is ready');

            hangoutURL = gapi.hangout.getHangoutUrl();
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

            //requestedSubject = gadgets.views.getParams()['gd'];
            //if (requestedSubject && requestedSubject > 1) {
            //    console.log('requested subject: ' + requestedSubject);
            //}

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


});

$(function () {
	    $('.aSpinEdit').spinedit({
			minimum: 0,
			maximum: 5,
			step:.25,
            numberOfDecimals: 2
	    });


		$('.aSpinEdit').on("valueChanged", function (e) {
			console.log(e.value);
		});
});



gadgets.util.registerOnLoadHandler(init);