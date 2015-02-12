/**
 * Created by admin on 2/10/15.
 */


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

Morris.Line({
  element: 'line-sessions',
  data: [
    { y: 'Jan 2015', a: 10 },
    { y: 'Feb', a: 17 },
    { y: 'Mar', a: 15 },
    { y: 'Apr', a: 27 },
    { y: 'May', a: 18 },
    { y: 'Jun', a: 13 },
    { y: 'Jul', a: 12}
  ],
  xkey: 'y',
  ykeys: ['a'],
parseTime: false,
  labels: ['Client Sessions']
});

