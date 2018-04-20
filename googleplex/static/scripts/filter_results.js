$(document).ready(function () {

	$("#reset").click(function(){
        $("tbody tr").show();
        $( "input:checkbox:checked" ).prop( "checked", false );
    });

    $(".year,.tag,.ethnicity").on("change", function () {
        var year = $(".year:checked").map(function () {
            return $(this).val()
        }).get();
        var tag = $(".tag:checked").map(function () {
            return $(this).val()
        }).get();
				var ethnicity = $(".ethnicity:checked").map(function () {
            return $(this).val()
        }).get();

        var all = $("tbody tr").hide();
        var tagshow = $("td").filter(function () {
            var ttext = $(this).text();
            var match = $.grep(tag, function(elemt) {
	            		return ttext.indexOf(elemt) > -1;
	            });
	            return match.length > 0
        }).parent()
        if (!tagshow.length) tagshow = all

        var period = $("td").filter(function () {
            var ytext = $(this).text();
            var matched = $.grep(year, function(elem) {
            		return ytext.indexOf(elem) > -1;
            });
            return matched.length > 0
        }).parent()
        if (!year.length) period = all

				var eshow = $(".eth").filter(function () {
            var etext = $(this).attr("value");
										console.log(etext);
						var ematch = $.grep(ethnicity, function(elem) {
            		return etext.indexOf(elem) > -1;
            });
            return ematch.length > 0
        }).parent()
				if (!eshow.length) eshow = all

        tagshow.filter(period).filter(eshow).show()

    }).first().change()
});
