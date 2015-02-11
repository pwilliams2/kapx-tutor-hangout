/**
 * Created by admin on 2/11/15.
 */
$(document).ready(function () {

      var t = $('#sessions').DataTable( {
        "ajax": "/sessions/data",
          "columns": [
            { "title": "#" },
            { "title": "Tutor" },
            { "title": "Student" },
            { "title": "Subject" },
            { "title": "Start", "class": "center" },
            { "title": "Duration", "class": "center" },
            { "title": "Survey", "class": "center" }
        ],
           "columnDefs": [ {
            "searchable": false,
            "orderable": false,
            "targets": [0,5]
        } ],
          "columnDefs": [
            { "width": "10%", "targets": 5 },
            { "width": "15%", "targets": 1 },
            { "width": "15%", "targets": 2 }
          ],
        "order": [[ 1, 'asc' ]]
    });
    t.on( 'order.dt search.dt', function () {
        t.column(0).nodes().each( function (cell, i) {
            cell.innerHTML = i+1;
        } );
    } );

});
