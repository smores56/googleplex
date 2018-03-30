var bestsellersOffset = 2; //number of items before bestseller title input boxes
var prevSelected = null;
var greenBackground = "#99DD99";
var whiteBackground = "#FFFFFF";


$(document).ready(function() {
  // put your Javascript here
  labels = document.getElementsByClassName("selectable_label");

  for (var i = 0; i < labels.length; i++) {
      labels[i].addEventListener('click', function(event) {
          if (event.target !== event.currentTarget) {
              event.stopPropagation();
              return false;
          } else {
              switchSelect(this);
          }
      }, false);
  }

  $("#load").click(function() {
    var num_bestsellers = document.getElementById("list_form").children.length - bestsellersOffset + 1;
    form = document.getElementById("list_form");

    //add styling label
    var label = document.createElement("label");
    label.classList.add("form_label");
    label.innerHTML = "                Book " + num_bestsellers + ":\n ";
    label.addEventListener('click', function(event) {
        if (event.target !== event.currentTarget) {
            event.stopPropagation();
            return false;
        } else {
            switchSelect(this);
        }
    }, false);
    //add actual input box
    var input = document.createElement("input");
    input.type = "text";
    input.name = "book" + num_bestsellers;
    label.appendChild(input);
    //add delete button
    var button = document.createElement("button")
    button.id = "button" + num_bestsellers;
    button.innerHTML = "Delete"
    button.type = "button";
    button.onclick = function() { deleteClick(button.id) };
    label.appendChild(button);
    //textbox and button to form
    form.appendChild(label);
  });

  $("#submit").click(function() {
      var num_bestsellers = document.getElementById("list_form").children.length - bestsellersOffset;
      var listTitle = document.forms["list_form"]["title"];
      if (listTitle == "") {
          alert("List requires a title.");
          return false;
      }

      //Ensure there is at least one book on the list
      if (num_bestsellers < 1) {
          alert("List must have at least one book!");
          return false;
      }

      for (var i = 1; i <= num_bestsellers; i++) {
          var bookName = "book" + i;
          var bestseller = document.forms["list_form"][bookName].value;
          if (bestseller == "") {
              var logStr = "Book " + i + " is empty, please delete it before submitting the list.";
              alert(logStr);
              return false;
          }
      }

      document.forms['list_form'].submit();
  })

});

function switchSelect(object) {
    if (!prevSelected) {
        object.style.backgroundColor = greenBackground;
        prevSelected = object;
    } else {
        //swap object and prevSelected here
        objectText = object.children[0].value;
        object.children[0].value = prevSelected.children[0].value;
        prevSelected.children[0].value = objectText;
        prevSelected.style.backgroundColor = whiteBackground;
        prevSelected = null;
    }
}

function deleteClick(clicked_id) {
    var bookToDelete = document.getElementById(clicked_id).parentElement;
    bookToDelete.remove();
    var loopStart = parseInt(clicked_id[6]) + bestsellersOffset - 1;
    elements = document.getElementById("list_form").children;

    for(var i = loopStart; i < elements.length; i++) {
        children = elements[i].childNodes;
        var bookNum = i - 1;
        children[0].data = "                Book " + bookNum + ":\n "
        children[1].name = "book" + bookNum;
        children[2].id = "button" + bookNum;
    }
};
