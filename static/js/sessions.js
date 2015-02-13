/**
 * Created by admin on 2/11/15.
 */
function popupSurvey(val)
{
    alert('survey click ' + val);
    //Get data

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
            {data: "start", "class": "center",
                "render": function (val, type, data, meta) {
                    if (type == "display") {
                        val = moment(val).format('MM/DD/YYYY h:mma');
                    }
                    return val;
                }
            },
            {data: "duration", "class": "center",
                "render": function (val, type, data, meta) {
                    if (type == "display") {
                        if (val) {
                            val = parseFloat(Math.round(val * 100) / 100).toFixed(2);
                        }
                    }
                    return val;
                }
            },
            {data: "survey_key", "class": "center",
                "render": function (val, type, data, meta) {
                    if (type == "display") {
                        if (val) {
                            val = '<a href="#" onClick=popupSurvey(val)>Survey</a>'
                        }
                        //else
                        //{
                        //    val = '<a href="#" onClick=popupSurvey(12345)>Survey</a>'
                        //}
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
