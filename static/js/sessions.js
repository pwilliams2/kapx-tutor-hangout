/**
 * Created by admin on 2/11/15.
 */

var SERVER_URL = '//kx-tutor-hangout-app.appspot.com/';
var SERVER_URL = '//localhost:8080/';

function popupSurvey(val) {
      var xmlhttp = new XMLHttpRequest();
      xmlhttp.onreadystatechange=function()
      {
      if (xmlhttp.status==200)
        {
            var jsonResponse = JSON.parse(xmlhttp.responseText);
            console.log(jsonResponse);
        }
      }
    xmlhttp.open("GET", SERVER_URL + "surveys/data?survey_key=" + val,true);
    xmlhttp.send();
    return true;
    //Update survey modal

    //Show survey modal
}
$(document).ready(function () {

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
                            val = '<a href="#" class="survey-link" onClick=popupSurvey("' + val + '")>Survey</a>'
                        }
                        else
                        {
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

});

