import subprocess
import time
CAMERA_LIGHT = "/root/camera_light.jpg"

def run():
    while True:
        process=subprocess.Popen(["libcamera-jpeg", "-o", CAMERA_LIGHT])
        process.communicate()
        print("Saving camera_light")
        time.sleep(60)
    return 0
