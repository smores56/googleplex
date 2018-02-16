$(document).ready(function() {
    // put your Javascript here
    // $("div").slice(0, 2).show(); // select the first ten

    var title = 1;
    var author = 1;
    var year = 1;
    $("#load").click(function () {
      $('#list tr:last').after('<br/><br/><tr>' +
          '<td>' +
            '<table style="width:80%">' +
              '<tr>' +
                '<td>' +
                  '<span class="col-lg-3" style="text-align:left">Title: </span>' +
                  '<input type="text" id="bookTitle' + (title+=1) + '">' +
                '</td>' +
              '</tr>' +
              '<tr>' +
                '<td>' +
                  '<span class="col-lg-4" style="text-align:left">Author: </span>' +
                  '<input type="text" id="author' + (author+=1) + '">' +
                '</td>' +
              '</tr>' +
              '<tr>' +
                '<td>' +
                  '<span class="col-lg-4" style="text-align:left">Year Published: </span>' +
                  '<input type="text" id="yearPublished' + (year+=1) + '">' +
                '</td>' +
              '</tr>' +
            '</table>' +
            '</td>' +
        '</tr>');
      });

      $('#manual-submit').submit(function(ev) {
        ev.preventDefault();

        var length = $("#books tr").length;
        var numBooks = length / 3;
        var data = {};
        for (i = 1; i < numBooks + 1; i++) {
          data["book".concat(i)] = {
            bookTitle: $("#bookTitle" + i).val(),
            author: $("#author" + i).val(),
            yearPublished: $("#yearPublished" + i).val()
          };
        }
        data['list_title'] = $("#listTitle").val()
        data['book_count'] = numBooks;
        $.ajax({
          url: '/manualpreview',
          data: JSON.stringify(data),
          type: "POST",
          success: function(response) {
            window.location.href = '/preview';
          },
          error: function(xhr) {
            console.trace()
          }
        });
      });

});
