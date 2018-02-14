$(document).ready(function() {
  $('#file').hide();
  $('#image').hide();

  $("#selectfile").click(function() {
    $("#sumission").hide();
    $("#file").show();
  });

  $("#selectimage").click(function() {
    $("#submission").hide();
    $("#image").show();
  });

  $("#prevfile").click(function() {
    $("#submission").show();
    $("#file").hide();
  });

  $("#previmage").click(function() {
    $("#submission").show();
    $("#image").hide();
  });
});
