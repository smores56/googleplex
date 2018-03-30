$(document).ready(function() {
    console.log($(" #data ").val())
    var data  = JSON.parse($(" #data ").val());
    console.log($( '#type option:selected').text())

    $( "#search" ).autocomplete({
               source: data['lists']
    });
    $('#type').change(function() {
        if ($( '#type option:selected').text() == 'Authors') {
            $( "#search" ).autocomplete({
               source: data['authors']
            });
        }
        else if ($( '#type option:selected').text() == 'Books') {
            $( "#search" ).autocomplete({
               source: data['books']
            });
        }
        else if ($( '#type option:selected').text() == 'Lists') {
            $( "#search" ).autocomplete({
               source: data['lists']
            });
        }
    })
});