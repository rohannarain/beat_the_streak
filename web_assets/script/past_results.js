$(document).ready(function(){
  $("body").height($(window).height());
})

var months = ['January','February','March','April','May','June','July',
'August','September','October','November','December']; 
var today = new Date();
today.setTime(today.getTime());
document.getElementById("span-date").innerHTML = months[today.getMonth()] + " " + today.getDate() + ", " + today.getFullYear();

var tempDate = new Date();

function padForDate(number) {
    return number < 10 ? '0'+number : number;
}

function formatToDateInURL(str) {
    var removeSlashes = str.replace("/", "_").replace("/", "_")
    var firstUnderscore = removeSlashes.indexOf("_")
    var secondUnderscore = removeSlashes.lastIndexOf("_")

    var month = padForDate(removeSlashes.slice(0, firstUnderscore))
    var day = padForDate(removeSlashes.slice(firstUnderscore+1, secondUnderscore))
    var year = removeSlashes.slice(secondUnderscore+1)

    return month + "_" + day + "_" + year
}

for (i = 1, len = 8; i < len; i++) {
    var prevDate = tempDate.getDate() - 1;
    tempDate.setDate(prevDate);
    var prevDateFormatted = tempDate.toLocaleDateString();
    var dropdown = d3.select(".dropdown-menu")
        .append("a")
        .attr("class", "dropdown-item")
        .attr("id", "date" + prevDateFormatted)
        .text(prevDateFormatted);
}

var dropdownItem = d3.selectAll(".dropdown-item");

dropdownItem.on("click", function() {
    var dateToRetrieve = this.id.slice(4);
    var dateInURL = formatToDateInURL(dateToRetrieve);
    var getURL = "https://raw.githubusercontent.com/rohannarain/beat_the_streak/master/data/past_results/past_results_" + dateInURL + ".csv";

    var performanceStatsURL = "https://raw.githubusercontent.com/rohannarain/beat_the_streak/master/data/model_stats/performance_" + dateInURL + ".csv";

    header = d3.select("header");
    header.selectAll("table").remove();
    header.select("#error-message").remove();

    d3.text(getURL, function(data) {
        try {
            var parsedCSV = d3.csv.parseRows(data);
            var container = d3.select("header")
                .append("table")
                .attr("class", "table")

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
        }
        catch(error) {
            header.select("#error-message").remove();

            header.append("div")
            .attr("class", "alert alert-warning")
            .attr("role", "alert")
            .attr("id", "error-message")
            .attr("style", "text-align: center")
            .text("Sorry, it doesn't look like there are any results for that date.");
        }
    });

    d3.text(performanceStatsURL, function(data) {
        try {
            var parsedCSV = d3.csv.parseRows(data);
            var container = d3.select("header")
                .append("div")
                .attr("class", "table-responsive")
                .append("table")
                .attr("class", "table")

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
        }
        catch(error) {
            header.select("#error-message").remove();

            header.append("div")
            .attr("class", "alert alert-warning")
            .attr("role", "alert")
            .attr("id", "error-message")
            .attr("style", "text-align: center")
            .text("Sorry, it doesn't look like there are any results for that date.");
        }
    });
});

