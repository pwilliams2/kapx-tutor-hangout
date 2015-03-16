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

var DICTIONARY_URL = 'http://dictionary.reference.com/';
var SURVEY_URL = 'http://kaplan.libsurveys.com/loader.php?id=7777f816624c182ea729979de88aeabc';
var DRIVE_URL = 'https://docs.google.com/picker?protocol=gadgets&origin=https://plus.google.com&title=Choose%20files%20to%20share%20with%20a%20link&hl=en&ui=2&multiselectEnabled=true&hostId=hangouts&authuser=0&relayUrl=https%3A%2F%2Fplus.google.com%2Ffavicon.ico&nav=((%22all%22%2Cnull%2C%7B%22ownedByMe%22%3Atrue%2C%22includeFolders%22%3Atrue%2C%22docTypesDropDown%22%3Atrue%2C%22selectFolder%22%3Atrue%7D)%2C(%22all%22%2Cnull%2C%7B%22ownedByMe%22%3Afalse%2C%22includeFolders%22%3Atrue%2C%22docTypesDropDown%22%3Atrue%2C%22selectFolder%22%3Atrue%7D)%2C(%22upload%22%2Cnull%2C%7B%22query%22%3A%22docs%22%7D))&rpctoken=8l7n7n9hf75m&rpcService=lcs85d4xd2pf'
$(function () {
    console.log('loading subjects');
    var id = 0,
        getRows = function () {

            var rows = [
                {"subject": "Business"},
                {"subject": "Math"},
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
        publish($table.bootstrapTable('getSelections'));
    });

    $('#feedback').click(function () {
        window.open(SURVEY_URL, "", "width=1002,height=700,location=0,menubar=0,scrollbars=1,status=1,resizable=0")
    });

    $('#btn-subjects-menu').click(function () {
        $('#subject-options').removeClass('hidden');
        $('#tutor-toolbox').addClass('hidden');
        $('#app-calculator').addClass('hidden');
        $('#app-calendar').addClass('hidden');
        console.log('btn-subjects-menu click');
    });

    $('#btn-toolbox-menu').click(function () {
        $('#tutor-toolbox').removeClass('hidden');
        $('#subject-options').addClass('hidden');
    });

    $('.btn-calendar').click(function () {
        $('#app-calendar').toggleClass('hidden');
        $('#app-calculator').addClass('hidden');
        console.log('btn-calendar click');
    });

    $('.btn-calculator').click(function () {
        $('#app-calculator').toggleClass('hidden');
        $('#app-calendar').addClass('hidden');
    });

    $('.btn-dictionary').click(function () {
        window.open(DICTIONARY_URL, "", "width=1002,height=700,location=0,menubar=0,scrollbars=1,status=1,resizable=0")
    });

    $('.btn-drive').click(function () {
        window.open(DRIVE_URL, "", "width=1002,height=700,location=0,menubar=0,scrollbars=1,status=1,resizable=0")
    });


    $('.today').html(getDate());

    webix.ui({
        container: "app-calendar",
        weekHeader: true,
        view: "calendar",
        events: webix.Date.isHoliday,
        width: 240
    });
});

function postSurvey() {
    console.log('postSurvey');
    studentId = localParticipant.person.id;
    payload = 'student_id=' + studentId
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