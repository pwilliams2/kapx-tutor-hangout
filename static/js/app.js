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

  //var selectedSub = document.getElementById('subjects').value;
  console.log('Selected subject' + subjects);

  var http = new XMLHttpRequest();
  http.open('GET', serverPath + "subjects?=" + subjects + '&hoURL=' + hangoutURL);
  http.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      var jsonResponse = JSON.parse(http.responseText);
      console.log(jsonResponse);

      $('message').html('params: ' + subjects
        + ' uri=' + encodeURI(hangoutURL) + '&pid='
        + localParticipant.person.id + '&pName='
        + localParticipant.person.displayName);
    }
  }
  http.send();
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
  //var tutorEmail = participants[0].person.emails[0].value;
   // console.log(tutorEmail);

  var participantsListElement = document.getElementById('participants');
  setText(participantsListElement, participants.length.toString());

}





// A function to be run at app initialization time which registers our callbacks
function init() {
  console.log('Init app.');

  var apiReady = function(eventObj) {
    if (eventObj.isApiReady) {
        console.log('API is ready');

        hangoutURL = gapi.hangout.getHangoutUrl();
        console.log('hangoutUrl: ' + hangoutURL);

        localParticipant = gapi.hangout.getLocalParticipant();  //Tutor
        $('#localParticipant').html(localParticipant.person.displayName);

       gapi.hangout.data.onStateChanged.add(function(eventObj) {
         updateStateUi(eventObj.state);
       });

       gapi.hangout.onParticipantsChanged.add(function(eventObj) {
       updateParticipantsUi(eventObj.participants);
      });

      gapi.hangout.onApiReady.remove(apiReady);
    }
  };

  // This application is pretty simple, but use this special api ready state
  // event if you would like to any more complex app setup.
  gapi.hangout.onApiReady.add(apiReady);
}

gadgets.util.registerOnLoadHandler(init);

$(function() {
     console.log('loadData');
      var id = 0,
          getRows = function () {

           var rows = [
              {"subject" : "Business"},
              {"subject" : "General Math"},
              {"subject" : "Calculus"},
              {"subject" : "Geometry"},
              {"subject" : "Science"},
              {"subject" : "Technology"},
              {"subject" : "Writing"}
            ];

            return rows;
          },
          // init table use data
          $table = $('#subjectTable').bootstrapTable({
            data: getRows()
          });

        // $table is defined above
        $('#get-selections').click(function () {
            getSubmitClick(JSON.stringify($table.bootstrapTable('getSelections')));
            //    alert('Selected values: ' + JSON.stringify($table.bootstrapTable('getSelections')));

        });

});

