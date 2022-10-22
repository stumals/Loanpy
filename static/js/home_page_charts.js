var w = +d3.select('.main').style('width').slice(0, -2) * .9
var h = 200
var m = {top: 30, bottom: 30, left: w*.01, right: w*.01}

var xScale = d3.scaleLinear().range([0, w])
var yScale = d3.scaleLinear().range([h, 0])

var svg = d3.select('.main').append('svg')
  .attr('width', w + m.left + m.right)
  .attr('height', h + m.top + m.bottom)
  .attr('class', 'line_chart')
  .append('g')
  .attr('class', 'container')
  .attr('transform', 'translate(' + m.left + ',' + m.top + ')')

var d = {{ data }}
console.log(d)