$(document).ready(function(){
  $("body").height($(window).height());
})

var months = ['January','February','March','April','May','June','July',
'August','September','October','November','December']; 
var today = new Date();
today.setTime(today.getTime());
document.getElementById("span-date").innerHTML = months[today.getMonth()] + " " + today.getDate() + ", " + today.getFullYear();

var monthNumbers = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
var fileMonth = monthNumbers[today.getMonth()]

var fileDate = today.getDate();
if (fileDate < 10) {
    fileDate = "0" + String(fileDate)
}

var fileYear = today.getFullYear();

d3.text("https://raw.githubusercontent.com/rohannarain/beat_the_streak/master/data/predictions/predictions_${fileMonth}_${fileDate}_${fileYear}.csv", 
    function(data) {
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
