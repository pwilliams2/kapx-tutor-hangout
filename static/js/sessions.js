/**
 * Created by admin on 2/11/15.
 */


$(function () {
    popupSurvey = function (val) {
        var xmlhttp = new XMLHttpRequest();
        xmlhttp.onreadystatechange = function () {
            if (xmlhttp.status == 200) {
                var jsonResponse = JSON.parse(xmlhttp.responseText);
                updateModal(jsonResponse);
            }
        }
        xmlhttp.open("GET", "/surveys/data?survey_key=" + val, true);
        xmlhttp.send();

        //Update survey modal


        return true;
    }

    updateModal = function (survey) {
        console.log(survey);

        $("#surveyModal #knowledge").html(survey.knowledge);
        $("#surveyModal #communications").html(survey.communications);
        $("#surveyModal #overall").html(survey.overall);
        $("#surveyModal #comments").html(survey.comments);

        //Show survey modal
        $("#surveyModal").modal('show');

    }

    var t = $('#sessions').DataTable({
        "ajax": "/sessions/data",
        "columns": [
            {"data": null},
            {data: "tutor_name"},
            {data: "participant_name"},
            {data: "subject"},
            {
                data: "start", "class": "center",
                "render": function (val, type, data, meta) {
                    if (type == "display") {
                        val = moment(val).format('MM/DD/YYYY h:mma');
                    }
                    return val;
                }
            },
            {
                data: "duration", "class": "center",
                "render": function (val, type, data, meta) {
                    if (type == "display") {
                        if (val) {
                            val = parseFloat(Math.round(val * 100) / 100).toFixed(2);
                        }
                    }
                    return val;
                }
            },
            {
                data: "survey_key",
                "render": function (val, type, data, meta) {
                    if (type == "display") {
                        if (val) {
                            val = '<a href="#" class="survey-link" onClick=popupSurvey("' + val + '");>Survey</a>'
                            //val = '<a class="survey-link">Survey</a>'
                        }
                        else {
                            //val = '<a href="#" onClick=popupSurvey(12345)>Survey</a>';
                        }
                    }
                    return val;
                }
            }
        ],
        "columnDefs": [{
            "searchable": false,
            "orderable": false,
            "targets": [0, 5]
        }],
        "columnDefs": [
            {"width": "10%", "targets": 5},
            {"width": "15%", "targets": 1},
            {"width": "15%", "targets": 2}
        ],
        "order": [[1, 'asc']]
    });
    t.on('order.dt search.dt', function () {
        t.column(0).nodes().each(function (cell, i) {
            cell.innerHTML = i + 1;
        });
    });

    //$('.survey-link').click(function () {
    //      console.log('survey-link clicked');
    //      var val = $(this).find(".survey-link").text();
    //      popupSurvey(val)
    //  });
});


