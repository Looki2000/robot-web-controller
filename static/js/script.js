function fullscreen() {

    document.documentElement.requestFullscreen();
}

// listen for fullscreen exit
document.addEventListener("fullscreenchange", function () {
    if (document.fullscreenElement) { // entered fullscreen

        document.getElementById("fullscreen").style.display = "none";
        screen.orientation.lock("landscape-primary");

    } else { // exited fullscreen

        document.getElementById("fullscreen").style.display = "block";
    }
});



window.addEventListener("DOMContentLoaded", (event) => {


    function send_buttons_data(buttons_array) {
        document.getElementById("button_state").innerHTML = buttons_array;

        // send button states to server as raw binary data
        var xhttp = new XMLHttpRequest();
        xhttp.open("POST", "/buttons", true);
        xhttp.send(new Uint8Array(buttons_array));
        
    }


    // Initialize an array to hold button states
    var buttons = [];

    // Select all elements with class "button"
    var buttonsElements = document.querySelectorAll(".button");

    // Loop through each button element
    buttonsElements.forEach(function (element, idx) {

        // Initialize the button state for the current index
        buttons[idx] = false;

        element.addEventListener("mousedown", function () {
            buttons[idx] = true;
            send_buttons_data(buttons);
        });

        element.addEventListener("mouseup", function () {
            buttons[idx] = false;
            send_buttons_data(buttons);
        });

        element.addEventListener("touchstart", function () {
            buttons[idx] = true;
            send_buttons_data(buttons);
        });

        element.addEventListener("touchend", function () {
            buttons[idx] = false;
            send_buttons_data(buttons);
        });

    });

});



