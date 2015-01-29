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
var serverPath = '//kx-tutor-hangout-app.appspot.com/';
var hangoutURL = '';
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
    var gid = arr[arr.length - 1];

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
    http.open('POST', serverPath + 'publishsubjects');
    http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    http.send('subjects=' + subjects
    + '&gid=' + gid
    + '&pid=' + localParticipant.person.id
    + '&pName=' + localParticipant.person.displayName);

    console.log('subjects=' + subjects
    + '&gid=' + gid
    + '&pid=' + localParticipant.person.id
    + '&pName=' + localParticipant.person.displayName);
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
    $('#participants').html(participants.length.toString());

    // For now, assume that if there is a participant, you are
    if (participants.length > 1) {
        $('#tutor-view').addClass('hidden');
        $('#student-view').removeClass('hidden');
    }
    else
    {
        $('#tutor-view').removeClass('hidden');
        $('#student-view').addClass('hidden');
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
            $('#localParticipant').html(localParticipant.person.displayName);

			console.log('setup view');
 			$('#tutor-view').removeClass('hidden');
        	$('#student-view').addClass('hidden');
        	
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
			minimum: -10,
			maximum: 50,
			step: 1
	    });

        console.log('loading sknow');
	    $('#spinknow').spinedit({
	        minimum: 0,
	        maximum: 5,
	        step: 0.25,
	        numberOfDecimals: 2
	    });

        console.log('loading skcomm');
        $('#spincomm').spinedit({
	        minimum: 0,
	        maximum: 5,
	        step: 0.25,
	        numberOfDecimals: 2
	    });

        console.log('loading skall');
        $('#spinall').spinedit({
	        minimum: 0,
	        maximum: 5,
	        step: 0.25,
	        numberOfDecimals: 2
	    });

		$('.aSpinEdit').on("valueChanged", function (e) {
			console.log(e.value);
		});
});

gadgets.util.registerOnLoadHandler(init);