

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

//// main loop
//function loop() {
//
//    // get all touch points
//    var touches = Array.from(event.touches);
//
//    // 
//
//
//    requestAnimationFrame(loop);
//}
//
//// start main loop
//requestAnimationFrame(loop);