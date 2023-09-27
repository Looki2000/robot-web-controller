function onload() {
    if ('DeviceOrientationEvent' in window) {
        window.addEventListener("deviceorientationabsolute", handleOrientation, true);
    } else {
        document.getElementById("orientation").innerText = "Device orientation API is not supported. (propably because lack of https on chrome)";
    }

}


function handleOrientation(event) {
    if (event.alpha !== null && event.beta !== null && event.gamma !== null) {
        document.getElementById("orientation_alpha").innerText = event.alpha.toFixed(1);
        document.getElementById("orientation_beta").innerText = event.beta.toFixed(1);
        document.getElementById("orientation_gamma").innerText = event.gamma.toFixed(1);

    } else {
        document.getElementById("orientation_alpha").innerText = "Orientation data not available.";
    }
}

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

// main loop
function loop() {

    // get all touch points
    var touches = Array.from(event.touches);

    // 


    requestAnimationFrame(loop);
}

// start main loop
requestAnimationFrame(loop);