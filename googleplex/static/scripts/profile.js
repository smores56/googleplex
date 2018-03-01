function onContainerClick (event) {
    if(event.classList.contains('activity')) {
        event.classList.remove('activity');
        document.getElementById("activityLabel").style.color = "black";
        document.getElementById("profileLabel").style.color = "white";
        document.getElementById("profileTable").hidden = false;
        document.getElementById("activityPage").hidden = true;
    } else {
        event.classList.add('activity');
        document.getElementById("activityLabel").style.color = "white";
        document.getElementById("profileLabel").style.color = "black";
        document.getElementById("profileTable").hidden = true;
        document.getElementById("activityPage").hidden = false;
    }
}
