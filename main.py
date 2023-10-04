#Import necessary libraries
from flask import Flask, render_template, Response, request
import cv2
import struct
import time
import threading
from flask import request
import sys
import os

# if linux
is_linux = sys.platform.startswith("linux")
if is_linux:
    import RPi.GPIO as GPIO

    # get pid of port 5002
    pid = os.popen("lsof -t -i:5002").read()

    print(f"pid: {pid}")

    # kill process
    os.system(f"kill -9 {pid}")




#Import GPIO library for RPI
#import RPi.GPIO as GPIO
LEFT_MOTOR_PWM = 12
RIGHT_MOTOR_PWM = 13

LEFT_MOTOR_DIR_1 = 16
RIGHT_MOTOR_DIR_1 = 19

LEFT_MOTOR_DIR_2 = 18
RIGHT_MOTOR_DIR_2 = 21


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]

loop_hz = 60
loop_delay = 1/loop_hz

#Initialize the Flask app
app = Flask(__name__)


# Create a lock to ensure that frames are sent one at a time
frame_lock = threading.Lock()


def gen_frames():
    camera = cv2.VideoCapture(0)

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            buffer = cv2.imencode('.jpg', frame, encode_param)[1]
            frame_bytes = buffer.tobytes()
            
            with frame_lock:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')



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
@app.route('/buttons', methods=['POST'])
def buttons():
    global buttons_array

    if request.method == 'POST':
        
        # unpack data to boolean list. example: b'\x00\x00\x00\x00'
        data = request.data
        buttons_array = struct.unpack('4?', data)

        return 'success', 200
    else:
        return 'error', 404



def motor_driver():
    motor_left = 0.0
    motor_right = 0.0
    while True:
        motor_right_target = 0.0
        motor_left_target = 0.0
        motor_right_old = motor_right
        motor_left_old = motor_left
        # processing buttons array to make smooth movement
        #print(buttons_array)


        if buttons_array[0]:
            motor_right_target += 1.0
            motor_left_target += 1.0
        if buttons_array[1]:
            motor_right_target -= 1.0
            motor_left_target -= 1.0
        if buttons_array[2]:
            motor_right_target += 0.5
            motor_left_target -= 0.5
        if buttons_array[3]:
            motor_right_target -= 0.5
            motor_left_target += 0.5

        if motor_right_target > 1.0:
            motor_right_target = 1.0
        if motor_right_target < -1.0:
            motor_right_target = -1.0

        if motor_left_target > 1.0:
            motor_left_target = 1.0
        if motor_left_target < -1.0:
            motor_left_target = -1.0

        motor_left = (motor_left_target + motor_left_old) / 2
        motor_right = (motor_right_target + motor_right_old) / 2

        if motor_left_target - motor_left_old < 0.1:
            motor_left = motor_left_target
        if motor_right_target - motor_right_old < 0.1:
            motor_right = motor_right_target

        print(buttons_array)
        print(f"motor_left: {motor_left}, motor_right: {motor_right}")

        

        if is_linux:
            #GPIO.output(LEFT_MOTOR_PWM, abs(motor_left))
            #GPIO.output(RIGHT_MOTOR_PWM, abs(motor_right))

            pins_state_string = f"L PWM: {abs(motor_left)}, R PWM: {abs(motor_right)} | "

            if motor_left > 0:
                #GPIO.output(LEFT_MOTOR_DIR_1, 1)
                #GPIO.output(LEFT_MOTOR_DIR_2, 0)
                pins_state_string += "L DIR1: 1, L DIR2: 0 | "

            elif motor_left < 0:
                #GPIO.output(LEFT_MOTOR_DIR_1, 0)
                #GPIO.output(LEFT_MOTOR_DIR_2, 1)
                pins_state_string += "L DIR1: 0, L DIR2: 1 | "
                
            elif motor_left== 0:
                #GPIO.output(LEFT_MOTOR_DIR_1, 0)
                #GPIO.output(LEFT_MOTOR_DIR_2, 0)
                pins_state_string += "L DIR1: 0, L DIR2: 0 | "
            

            if motor_right > 0:
                #GPIO.output(RIGHT_MOTOR_DIR_1, 1)
                #GPIO.output(RIGHT_MOTOR_DIR_2, 0)
                pins_state_string += "R DIR1: 1, R DIR2: 0 | "

            elif motor_right < 0:
                #GPIO.output(RIGHT_MOTOR_DIR_1, 0)
                #GPIO.output(RIGHT_MOTOR_DIR_2, 1)
                pins_state_string += "R DIR1: 0, R DIR2: 1 | "

            elif motor_right== 0:
                #GPIO.output(RIGHT_MOTOR_DIR_1, 0)
                #GPIO.output(RIGHT_MOTOR_DIR_2, 0)
                pins_state_string += "R DIR1: 0, R DIR2: 0 | "

            print(pins_state_string)


        # perfect delay for making loop oscillate exactly at loop_hz frequency, no matter how long does it take to execute the code inside the loop
        time.sleep(loop_delay - time.perf_counter() % loop_delay)



if __name__ == "__main__":
    with open("ip.txt", "r") as f:
        ip = f.read().splitlines()[0]
        print(f"ip: {ip}")

    buttons_array = [False, False, False, False]

    t = threading.Thread(target=motor_driver, daemon=True)
    t.start()

    app.run(debug=False, port=5002, host=ip)
