/**
 * Created by admin on 2/10/15.
 */

Morris.Donut({
  element: 'donut-usage',
  data: [
    {label: "Business", value: 5},
    {label: "Writing", value: 10},
    {label: "Math", value: 45},
      {label: "Science", value: 15},
      {label: "Technology", value: 25}
  ]
});


Morris.Bar({
    element: 'bar-survey',
    data: [
        {x: 'Jan 2015', a: 3.25, b: 3.75, c: 4.1},
        {x: 'Feb', a: 3.75, b: 3.95, c: 4.3},
        {x: 'Mar', a: 3.65, b: 3.25, c: 3.9},
        {x: 'Apr', a: 3.25, b: 3.75, c: 4.3},
        {x: 'May', a: 3.85, b: 3.75, c: 3.5},
        {x: 'Jun', a: 3.15, b: 3.75, c: 4.2},
        {x: 'Jul', a: 4.25, b: 4.3, c: 4.4},


    ],
    hoverCallback: function(index, options, content) {
        return(content);
    },
    xkey: 'x',
    ykeys: ['a', 'b', 'c'],
    labels: ['Knowledge', 'Communications', 'Overall'],
    parseTime: true,
    ymax: 5,
    xLabelAngle: 35,
    hideHover: 'auto'

});

Morris.Area({
  element: 'area-usage',
  data: [
       { x: '2015-02-09 11:00', a: 0, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 11:11', a: 1, b: 0, c:0, d:0, e:0 },
       { x: '2015-02-09 11:20', a: 0, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 11:30', a: 0, b: 0, c:0, d:1, e:0 },
       { x: '2015-02-09 12:00', a: 0, b: 1, c:0, d:0, e:1 },
       { x: '2015-02-09 13:00', a: 0, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 13:10', a: 0, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 13:23', a: 0, b: 0, c:0, d:0, e:1 },
       { x: '2015-02-09 13:57', a: 0, b: 0, c:1, d:0, e:0 },
       { x: '2015-02-09 14:20', a: 1, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 18:00', a: 0, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 19:00', a: 1, b: 0, c:0, d:0, e:0 },
         { x: '2015-02-09 19:20', a: 0, b: 0, c:0, d:2, e:0 },
       { x: '2015-02-09 20:00', a: 0, b: 1, c:0, d:0, e:0 },
       { x: '2015-02-09 21:00', a: 0, b: 0, c:0, d:0, e:0 }

  ],
  xkey: 'x',
  ykeys: ['a', 'b','c','d','e'],
  labels: ['Business', 'Math', 'Science', 'Technology','Writing'],
  parseTime:true

});

