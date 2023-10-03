#Import necessary libraries
from flask import Flask, render_template, Response, request
import cv2
import struct

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

#Initialize the Flask app
app = Flask(__name__)

def gen_frames():

    camera = cv2.VideoCapture(0)

    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            #buffer = cv2.imencode('.jpg', frame)[1]
            buffer = cv2.imencode('.jpg', frame, encode_param)[1]
            frame = buffer.tobytes()
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

    # stop camera
    camera.release()
    print("Camera released")


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# receive data from client
#192.168.100.9 - - [03/Oct/2023 23:32:24] "POST /buttons HTTP/1.1" 404 -
@app.route('/buttons', methods=['POST'])
def buttons():
    if request.method == 'POST':
        
        # unpack data to boolean list. example: b'\x00\x00\x00\x00'
        data = request.data
        data = struct.unpack('4?', data)
        print(f"begin {data} end")

        return 'success', 200
    else:
        return 'error', 404


if __name__ == "__main__":
    with open("ip.txt", "r") as f:
        ip = f.read()
        print(f"ip: {ip}")

    app.run(debug=False, port=5002, host=ip)