$(document).ready(function() {
  // put your Javascript here
  // $("div").slice(0, 2).show(); // select the first ten

  var num_bestsellers = (document.getElementById("list_form").length - 1)/2; //total inputs - single title input / 2 = total text box inputs

  $("#load").click(function() {
    num_bestsellers++;
    form = document.getElementById("list_form");
    //add styling label
    var label = document.createElement("label");
    label.classList.add("form_label");
    label.innerHTML = 'Book ' + num_bestsellers + ': ';
    //add actual input box
    var input = document.createElement("input");
    input.type = "text";
    input.name = "book" + num_bestsellers;
    label.appendChild(input);
    //add delete button
    var button = document.createElement("button")
    button.name = "button" + num_bestsellers;
    button.innerHTML = "Delete"
    button.type = "button";
    button.onClick = deleteClick();
    label.appendChild(button);
    //textbox and button to form
    form.appendChild(label);
  });

  $("#submit").click(function() {
      document.getElementById("list_form").submit();
  })
  // $('#remove').on('click', function() {
  //   for (i = 0; i < 3; i++) {
  //     $('#books tr:last').remove();
  //   }
  //   num_bestsellers--;
  // });
});

function deleteClick() {
  console.log('xdd');
  //   console.log(this.name);
};
