$(document).ready(function() {
    console.log($(" #data ").val())
    var authors  = JSON.parse($(" #data ").val());
    console.log(authors);
    $( "#search" ).autocomplete({
       source: authors['name']
    });
});