$(document).ready(function() {
  // put your Javascript here
  // $("div").slice(0, 2).show(); // select the first ten

  var num_bestsellers = 1;
  var data  = JSON.parse($(" #data ").val());

    $(".title").autocomplete({
      source: data['books']
    });
    $(".author").autocomplete({
      source: data['authors']
    });


  $("#load").click(function() {
    num_bestsellers++;
    $('#list tr:last').after(`<br/><br/><tr>
          <td>
            <table style="width:80%">
              <tr>
                <td>
                  <span class="col-lg-3" style="text-align:left">Title: </span>
                  <input type="text" class="title" id="title` + num_bestsellers + `">
                </td>
              </tr>
              <tr>
                <td>
                  <span class="col-lg-4" style="text-align:left">Author: </span>
                  <input type="text" class="author" id="author` + num_bestsellers + `">
                </td>
              </tr>
              <tr>
                <td>
                  <span class="col-lg-4" style="text-align:left">Date Published: </span>
                  <input type="date" class="date" id="authored_date` + num_bestsellers + `">
                </td>
              </tr>
            </table>
          </td>
        </tr>`);

        $(".title").autocomplete({
          source: data['books']
        });
        $(".author").autocomplete({
          source: data['authors']
        });
  });

  $('#manual-submit').submit(function(ev) {
    ev.preventDefault();

    var data = {
      bestsellers: [],
      title: $("#title").val(),
      num_bestsellers: num_bestsellers
    };
    for (i = 1; i < num_bestsellers + 1; i++) {
      data["bestsellers"].push({
        title: $("#title" + i).val(),
        author: $("#author" + i).val(),
        authored_date: $("#authored_date" + i).val()
      });
    }
    $.ajax({
      url: '/manual_submit?type=manual',
      data: JSON.stringify(data),
      type: "POST",
      success: function(response) {
        window.location.href = '/preview?type=manual&list_id=' + response.list_id;
      },
      error: function(xhr) {
        console.trace()
      }
    });
  });

  $('#remove').on('click', function() {
    for (i = 0; i < 3; i++) {
      $('#books tr:last').remove();
    }
    num_bestsellers--;
  });

});
