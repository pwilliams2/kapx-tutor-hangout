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
var hangoutURL = '';
var gid ='';
var localParticipant;

// The functions triggered by the buttons on the Hangout App
function countButtonClick() {
    // Note that if you click the button several times in succession,
    // if the state update hasn't gone through, it will submit the same
    // delta again.  The hangout data state only remembers the most-recent
    // update.
    console.log('Button clicked.');
    var value = 0;
    var count = gapi.hangout.data.getState()['count'];
    if (count) {
        value = parseInt(count);
    }

    console.log('New count is ' + value);
    // Send update to shared state.
    // NOTE:  Only ever send strings as values in the key-value pairs
    gapi.hangout.data.submitDelta({'count': '' + (value + 1)});
}

function resetButtonClick() {
    console.log('Resetting count to 0');
    gapi.hangout.data.submitDelta({'count': '0'});
}

var forbiddenCharacters = /[^a-zA-Z!0-9_\- ]/;
function setText(element, text) {
    element.innerHTML = typeof text === 'string' ?
        text.replace(forbiddenCharacters, '') :
        '';
}

function getSubmitClick(subjects) {
    console.log('Selected subject' + subjects);
    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];

    var payload = 'subjects=' + subjects
    + '&gid=' + gid
    + '&pid=' + localParticipant.person.id
    + '&pName=' + localParticipant.person.displayName

    httpRequest('POST', SERVER_PATH + 'publishsubjects', payload);

    //http.open('POST', SERVER_PATH + 'publishsubjects');
    //http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    //http.send('subjects=' + subjects
    //+ '&gid=' + gid
    //+ '&pid=' + localParticipant.person.id
    //+ '&pName=' + localParticipant.person.displayName);

}


function httpRequest(method, path, params)
{
	console.log('method: ' + method + ' path: ' + path + ' params: ' + params);
	
    var http = new XMLHttpRequest();
    http.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            var jsonResponse = JSON.parse(http.responseText);

            $('#message').html("Submitted");
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
    }
    else if ((method && method.toUpperCase() == "POST")) {
        http.open('POST', SERVER_PATH + 'publishsubjects');
        http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        http.send(params);
    }
    
}

function updateStateUi(state) {
    var countElement = document.getElementById('count');
    var stateCount = state['count'];
    if (!stateCount) {
        console.log('probably 0');
        //setText(countElement, 'Probably 0');
    } else {
        console.log(stateCount.toString());
        //setText(countElement, stateCount.toString());
    }
}

function updateParticipantsUi(participants) {
    console.log('Participants count: ' + participants.length);

    var clientParticipant = gapi.hangout.getLocalParticipant();
    $('.clientParticipant').html(clientParticipant.person.displayName);

    hangoutURL = gapi.hangout.getHangoutUrl();
    var arr = hangoutURL.split('/');
    gid = arr[arr.length - 1];

    if (participants.length > 1) {
        httpRequest('GET','subscribe','gid=' + gid);
    }
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
            $('.instructor').html(localParticipant.person.displayName);

            var startData = gapi.hangout.getStartData();
            console.log('start_data: ' + startData);

            if (startData && startData.length > 1) {
                $('#tutor-view').removeClass('hidden');
                $('#student-view').addClass('hidden');
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
        getSubmitClick(JSON.stringify($table.bootstrapTable('getSelections')));
    });


});

$(function () {
	    $('.aSpinEdit').spinedit({
			minimum: 0,
			maximum: 5,
			step:.25,
            value: 3,
            numberOfDecimals: 2
	    });


		$('.aSpinEdit').on("valueChanged", function (e) {
			console.log(e.value);
		});
});

gadgets.util.registerOnLoadHandler(init);