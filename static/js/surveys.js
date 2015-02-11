/**
 * Created by admin on 2/11/15.
 */
$(document).ready(function () {

      var t = $('#surveys').DataTable( {
        "ajax": "/surveys/data",
          columns: [
                { data: null },
                { data: 'tutor_name' },
                { data: 'student_name' },
                { data: 'knowledge' },
                { data: 'communications' },
                { data: 'overall' },
                { data: 'subject' },
                { data: 'comments' }
            ],

           "columnDefs": [
            {
                "targets": [ 0 ],
                "visible": false,
                "searchable": false
            }],
           "columnDefs": [
            { "width": "10%", "targets": 1 },
            { "width": "10%", "targets": 2 },
            { "width": "25%", "targets": 7 }
          ],
        //    {
        //        "targets": [ 8 ],
        //        "visible": false
        //    }
        //],
        "order": [[ 1, 'asc' ]]
    });
    t.on( 'order.dt search.dt', function () {
        t.column(0).nodes().each( function (cell, i) {
            cell.innerHTML = i+1;
        } );
    }).draw();

});
