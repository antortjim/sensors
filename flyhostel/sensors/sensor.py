import threading
import time
import datetime
import logging
import os
import traceback
import json

import serial
import cv2

from flyhostel.arduino import utils
from flyhostel.arduino import Identifier
import flyhostel
from .camera import run as camera_run, CAMERA_LIGHT

TIMEOUT = 5
MAX_COUNT=3
DATA_SEPARATOR=","
METADATA_SEPARATOR=";"

with open(flyhostel.CONFIG_FILE, "r") as fh:
    conf = json.load(fh)

try:
    FREQUENCY = conf["sensors"]["frequency"]
except Exception:
    FREQUENCY = 60


class Sensor(threading.Thread):

    _freq = FREQUENCY  # seconds

    def __init__(
        self, logfile=None, verbose=False, port=None, baudrate=9600, *args, **kwargs
    ):

        self.reset()

        if port is None:
            port = self.detect()

        self._ser = serial.Serial(port, timeout=TIMEOUT, baudrate=baudrate)
        self._camera = threading.Thread(target=camera_run)
        self._logfile = logfile
        self._verbose = verbose
        super().__init__(*args, **kwargs)


    @property
    def last_time(self):
        return self._data["timestamp"]

    @property
    def must_update(self):
        return time.time() > self.last_time + self._freq

    @property
    def has_logfile(self):
        return self._logfile is not None


    def __getattr__(self, value):
        if value in self._data.keys():
            return self._data[value]

    def reset(self):
        self._data = {
            "temperature": 0,
            "pressure": 0,
            "altitude": 0,
            "light": 0,
            "humidity": 0,
            "timestamp": 0,
            "datetime": "",
            "camera_light": 0,
        }

    def detect(self):

        identifier = Identifier
        port = identifier.report().get("Environmental sensor", None)
        if port is None:
            raise Exception("Environmental sensor not detected")
        else:
            print("Detected Environmental sensor on port %s" % port)
        return port


    @staticmethod
    def compute_camera_light():
        if not os.path.exists(CAMERA_LIGHT):
            return None

        timestamp = os.path.getmtime(CAMERA_LIGHT)
        now = time.time()
        if (now - timestamp) > 300:
            return None
        else:
            im=cv2.imread(CAMERA_LIGHT)
            return im.mean()

    def communicate(self):

        code, data = utils.talk(self._ser, "D\n")
        if code != 0:
            raise Exception("Cannot communicate command")
        status, data = utils.safe_json_load(self._ser, data)
        data["camera_light"] = self.compute_camera_light()

        if status == 0:
        
            data["timestamp"] = time.time()
            data["datetime"] = datetime.datetime.fromtimestamp(
                data["timestamp"]
            ).strftime("%Y-%m-%d %H:%M:%S")
            self._data = data

        return status

    def get_readings(self):
        status = self.communicate()
        return status

    def loop(self):

        status = self.get_readings()

        if self.has_logfile and self.must_update:
            self.write()
        
        return status


    def run(self):
        self._camera.start()
        count = 0
        try:
            while True:

                status = self.loop()
                if status == 0:
                    count = 0
                else:
                    count +=1
                    if count == MAX_COUNT:
                        os.system("reboot")

        except KeyboardInterrupt:
            pass
        
    def write(self):
        with open(self._logfile, "a") as fh:
            args=(
                self._data["datetime"],
                self._data["temperature"],
                self._data["humidity"],
                self._data["light"],
                self._data["camera_light"],
                self._data["pressure"],
                self._data["altitude"],
            )
            line="%s\t" * (len(args) - 1) + "%s\n"
            fh.write(line % args)


if __name__ == "__main__":
    sensor = Sensor(verbose=True)
    sensor.start()
