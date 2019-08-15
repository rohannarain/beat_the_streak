$(document).ready(function(){
  $("body").height($(window).height());
})

var months = ['January','February','March','April','May','June','July',
'August','September','October','November','December']; 
var today = new Date();
today.setTime(today.getTime());
document.getElementById("span-date").innerHTML = months[today.getMonth()] + " " + today.getDate()+ ", " + today.getFullYear();

d3.text("https://raw.githubusercontent.com/rohannarain/beat_the_streak/master/data/predictions/predictions_08_15_2019.csv", function(data) {
    var parsedCSV = d3.csv.parseRows(data);

    var container = d3.select("header")
        .append("table")

    .selectAll("tr")
        .data(parsedCSV).enter()
        .append("tr")

    .selectAll("td")
        .data(function(d) {
            return d;
        }).enter()
        .append("td")
        .text(function(d) {
            return d;
        });
});
