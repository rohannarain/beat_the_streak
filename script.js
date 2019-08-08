d3.text("https://raw.githubusercontent.com/rohannarain/beat_the_streak/master/predictions_07_28_2019.csv", function(data) {
    var parsedCSV = d3.csv.parseRows(data);

    var container = d3.select("body")
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
