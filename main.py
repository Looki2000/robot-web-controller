import os
from flask import Flask, render_template, Response, request
import cv2
import struct
import time
import threading
from flask import request
import sys

######## CONFIG ########

loop_hz = 60

host_port = 5002
write_video = True

# selection for acceleration system version
# 0 - first version, 1 - second version
accel_system = 0

## config for acceleration system second version (has no affect on the first version)
# atack and release in seconds
accel_atack = 0.5
accel_release = 0.2


# video write config
vid_write_fps = 30
vid_write_res = (640, 480)

########################


loop_delay = 1/loop_hz

accel_atack = 1/accel_atack * loop_hz
accel_release = 1/accel_release * loop_hz


# if linux
is_linux = sys.platform.startswith("linux")
if is_linux:
    os.system("nmcli connection up penetration\ master")
    
    import RPi.GPIO as GPIO

    # get pid of port 5002
    pid = os.popen(f"lsof -t -i:{host_port}").read()

    print(f"pid: {pid}")

    # kill process
    os.system(f"kill -9 {pid}")


    GPIO.setmode(GPIO.BCM)
    LEFT_MOTOR_PWM = 12
    RIGHT_MOTOR_PWM = 13

    LEFT_MOTOR_DIR_1 = 16
    RIGHT_MOTOR_DIR_1 = 19

    LEFT_MOTOR_DIR_2 = 18
    RIGHT_MOTOR_DIR_2 = 21

    GPIO.setup(LEFT_MOTOR_PWM, GPIO.OUT)
    GPIO.setup(RIGHT_MOTOR_PWM, GPIO.OUT)
    lmp = GPIO.PWM(LEFT_MOTOR_PWM,1000)
    lmp.start(0)
    rmp = GPIO.PWM(RIGHT_MOTOR_PWM, 1000)
    rmp.start(0)

    GPIO.setup(LEFT_MOTOR_DIR_1, GPIO.OUT)
    GPIO.setup(RIGHT_MOTOR_DIR_1, GPIO.OUT)

    GPIO.setup(LEFT_MOTOR_DIR_2, GPIO.OUT)
    GPIO.setup(RIGHT_MOTOR_DIR_2, GPIO.OUT)


import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]



#Initialize the Flask app
app = Flask(__name__)


# Create a lock to ensure that frames are sent one at a time
frame_lock = threading.Lock()


def gen_frames():
    global frame
    global new_frame_ready

    while True:
        if new_frame_ready:
            #success, frame = camera.read()
            #if not success:
                #break
            #else:
            buffer = cv2.imencode('.jpg', frame, encode_param)[1]
            frame_bytes = buffer.tobytes()
                
            with frame_lock:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
            new_frame_ready = False



    # stop camera
    #camera.release()
    #print("Camera released")


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
    global last_received_time

    if request.method == 'POST':
        
        # unpack data to boolean list. example: b'\x00\x00\x00\x00'
        data = request.data
        buttons_array = struct.unpack('4?', data)

        last_received_time = time.perf_counter()

        return 'success', 200
    else:
        return 'error', 404


def clamp(val, min, max):
    if val < min:
        return min
    elif val > max:
        return max
    else:
        return val


def motor_driver():
    global last_received_time
    global buttons_array

    motor_left = 0.0
    motor_right = 0.0
    motor_right_target = 0.0
    motor_left_target = 0.0

    last_received_time = time.perf_counter()

    connection_state = False
    last_connection_state = False

    while True:
        
        # if last received data is older than some amount of time, set buttons_array to zeros
        # this time should be about 2x the time of the loop cycle set in the script.js
        if time.perf_counter() - last_received_time > 0.4:
            buttons_array = [False, False, False, False]

            connection_state = False

        else:
            connection_state = True

        if connection_state != last_connection_state:
            print("New connection acomplished!" if connection_state else "Connection lost!")

        last_connection_state = connection_state



        # first version of acceleration system
        if accel_system == 0:
            motor_right_old = motor_right
            motor_left_old = motor_left
            # processing buttons array to make smooth movement
            #print(buttons_array)

        # forward
        if buttons_array[0]:
            motor_right_target -= 1.0
            motor_left_target -= 1.0

        # backward
        if buttons_array[1]:
            motor_right_target += 1.0
            motor_left_target += 1.0

        # left
        if buttons_array[2]:
            motor_right_target += 0.5
            motor_left_target -= 0.5

        # right
        if buttons_array[3]:
            motor_right_target -= 0.5
            motor_left_target += 0.5

        # clamp values
        motor_right_target = clamp(motor_right_target, -1.0, 1.0)
        motor_left_target = clamp(motor_left_target, -1.0, 1.0)

        # first version of acceleration system
        if accel_system == 0:
            motor_left = (motor_left_target + motor_left_old) / 2
            motor_right = (motor_right_target + motor_right_old) / 2

            if motor_left_target - motor_left_old < 0.1:
                motor_left = motor_left_target
            if motor_right_target - motor_right_old < 0.1:
                motor_right = motor_right_target

        # second version of acceleration system
        elif accel_system == 1:

            # update motor values if they are not equal to target
            # use atack if new target is greater than current value
            # use release if new target is less than current value

            # right motor
            if motor_right_target > motor_right:
                motor_right += accel_atack
                if motor_right > motor_right_target:
                    motor_right = motor_right_target

            elif motor_right_target < motor_right:
                motor_right -= accel_release
                if motor_right < motor_right_target:
                    motor_right = motor_right_target

            # left motor
            if motor_left_target > motor_left:
                motor_left += accel_atack
                if motor_left > motor_left_target:
                    motor_left = motor_left_target

            elif motor_left_target < motor_left:
                motor_left -= accel_release
                if motor_left < motor_left_target:
                    motor_left = motor_left_target


        #print(buttons_array)
        #print(f"motor_left: {motor_left}, motor_right: {motor_right}")
        

        if is_linux:
            lmp.ChangeDutyCycle(int(abs(motor_left*100)))
            rmp.ChangeDutyCycle(int(abs(motor_right*100)))

            #pins_state_string = f"L PWM: {abs(motor_left)}, R PWM: {abs(motor_right)} | "
            # pwm

            if motor_left > 0:
                GPIO.output(LEFT_MOTOR_DIR_1, 1)
                GPIO.output(LEFT_MOTOR_DIR_2, 0)
                #pins_state_string += "L DIR1: 1, L DIR2: 0 | "

            elif motor_left < 0:
                GPIO.output(LEFT_MOTOR_DIR_1, 0)
                GPIO.output(LEFT_MOTOR_DIR_2, 1)
                #pins_state_string += "L DIR1: 0, L DIR2: 1 | "
                
            elif motor_left== 0:
                GPIO.output(LEFT_MOTOR_DIR_1, 0)
                GPIO.output(LEFT_MOTOR_DIR_2, 0)
                #pins_state_string += "L DIR1: 0, L DIR2: 0 | "
            

            elif motor_left== 0:
                GPIO.output(LEFT_MOTOR_DIR_1, 0)
                GPIO.output(LEFT_MOTOR_DIR_2, 0)

            if motor_right > 0:
                GPIO.output(RIGHT_MOTOR_DIR_1, 1)
                GPIO.output(RIGHT_MOTOR_DIR_2, 0)
                #pins_state_string += "R DIR1: 1, R DIR2: 0 | "

            elif motor_right < 0:
                GPIO.output(RIGHT_MOTOR_DIR_1, 0)
                GPIO.output(RIGHT_MOTOR_DIR_2, 1)
                #pins_state_string += "R DIR1: 0, R DIR2: 1 | "

            elif motor_right== 0:
                GPIO.output(RIGHT_MOTOR_DIR_1, 0)
                GPIO.output(RIGHT_MOTOR_DIR_2, 0)
                #pins_state_string += "R DIR1: 0, R DIR2: 0 | "

            #print(pins_state_string)


        # perfect delay for making loop oscillate exactly at loop_hz frequency, no matter how long does it take to execute the code inside the loop
        time.sleep(loop_delay - time.perf_counter() % loop_delay)



def video_writer():
    global frame
    global new_frame_ready
    global camera

    camera = cv2.VideoCapture(0)
    
    if write_video:
        #fps = camera.get(cv2.CAP_PROP_FPS)
        #width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        #height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        #
        #print("cam fps:", fps)
        #print(f"{width} x {height}")

        # create video_path folder if it doesn't exist
        if not os.path.exists(video_path):
            os.makedirs(video_path)

        print(f"Camera FPS: {vid_write_fps}")
        print(f"Camera resolution: {vid_write_res[0]} x {vid_write_res[1]}")

        writer = cv2.VideoWriter(os.path.join(video_path, time.strftime("%d-%m-%Y_%H-%M-%S") + ".avi"), cv2.VideoWriter_fourcc(*'XVID'), vid_write_fps, vid_write_res)
    
    print("capturing!")
    while True:
        success, frame = camera.read()
        if not success:
            continue
        else:
            new_frame_ready = True
            if write_video:
                writer.write(frame)



if __name__ == "__main__":

    run_path = os.path.dirname(__file__)

    video_path = os.path.join(run_path, "videos")
    
    ip_path = os.path.join(run_path, "ip.txt")

    
    with open(ip_path, "r") as f:
        ip = f.read().splitlines()[0]
        print(f"web address: {ip}:{host_port}")

    buttons_array = [False, False, False, False]

    # motor driver thread
    t_motor = threading.Thread(target=motor_driver, daemon=True)
    t_motor.start()

    
    camera = None

    # video writer thread
    print("starting camera thread...")
    new_frame_ready = False
    t_video = threading.Thread(target=video_writer, daemon=True)
    t_video.start()
    
    while camera is None:
        time.sleep(0.1)

    print("camera initialized!")
    

    # start flask app
    app.run(debug=False, port=host_port, host=ip)
