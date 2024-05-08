import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import numpy as np
import time
from subprocess import run

class CameraTest:
    def __init__(self, exposure_time, idle_time, run_time, cycles=1, gpio_line='3', frame_factor=50, hardware_trigger=False):
        self.exposure_time = exposure_time
        self.idle_time = idle_time
        self.run_time = run_time
        self.cycles = cycles
        self.gpio_line = gpio_line
        self.frame_factor = frame_factor
        self.hardware_trigger = hardware_trigger

        self.heat_flag = 0
        self.frame_count = 1
        self.images = []
        self.grabbing_details = []

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        print(self.camera)

    def DataProcess(self):
        self.grabbing_details = pd.DataFrame(self.grabbing_details, columns=['Time Stamp', 'Local Time', 'Temperature'])

        plt.plot(self.grabbing_details['Temperature'], label='Temperature @ ' + "FpgaCore", color='blue')
        plt.axhline(85, label="Critical Temperature Threshold", color='orange')
        plt.legend()
        plt.ylim([30, 100])

        print(self.grabbing_details)

        ### For testing
        print(pd.DataFrame(self.images[0]).describe())

        self.avg_intensity = np.empty((0,0))
        for frame in range(len(self.images)):
            self.mean = np.array(self.images[frame]).mean()
            self.avg_intensity = np.append(self.avg_intensity,self.mean)

        print(self.avg_intensity)

        pd.DataFrame(self.avg_intensity).to_csv('avg_intensities.csv')
        pd.DataFrame(self.grabbing_details).to_csv('grabbing_details.csv')
        np.savetxt('firstframe.txt', self.images[1], fmt='%d')

    def HardwareTrigger(self):
        self.camera.LineSelector = "Line" + self.gpio_line
        self.camera.LineMode = "Input"

        self.camera.TriggerSelector = "FrameStart"
        self.camera.TriggerSource = "Line" + self.gpio_line
        self.camera.TriggerMode = "On"

    def GrabbingProtocol(self):
        while self.camera.IsGrabbing() and (self.currtime - self.stime < self.run_time):
            self.grab_result = self.camera.RetrieveResult(self.exposure_time, pylon.TimeoutHandling_ThrowException)
            self.currtime = time.monotonic()

            if self.grab_result.GrabSucceeded() and self.frame_count % self.frame_factor == 0:
                self.frame_count += 1
                self.images.append(self.grab_result.Array)
                self.grabbing_details.append((self.grab_result.TimeStamp / 1e9, time.localtime, self.camera.DeviceTemperature.Value))

            elif self.grab_result.GrabSucceeded():
                self.frame_count += 1
                self.grabbing_details.append((self.grab_result.TimeStamp / 1e9, time.localtime, self.camera.DeviceTemperature.Value))

            if self.camera.DeviceTemperature.Value >= 85:
                print(r'Warning, ', self.camera.DeviceTemperature.Value)
            elif self.camera.DeviceTemperature.Value >= 100: # If overheating
                print('CRITICAL ERROR, COOL CAMERA')
                self.heat_flag = 1
                break

            self.grab_result.Release()

    def DisableCamera(self):
        run(
            "echo '0' > '/sys/bus/usb/devices/2-1.4/power/autosuspend_delay_ms'",
            shell=True,
        )
        run("echo 'auto' > '/sys/bus/usb/devices/2-1.4/power/control'", shell=True)

    def EnableCamera(self):
        run("echo 'on' > '/sys/bus/usb/devices/2-1.4/power/control'", shell=True)

    def Activate(self):
        self.camera.Open()

        if self.hardware_trigger == True:
            self.HardwareTrigger()
        else:
            self.camera.TriggerSource.Value = "Software" # This sets the camera to work soley off of this software
        
        self.camera.StartGrabbing()

        self.camera.DeviceTemperatureSelector.Value = "FpgaCore"
        print('Capturing the temperature at: ' + self.camera.DeviceTemperatureSelector.Value)

        for c in range(self.cycles): 
            if self.heat_flag == 1: # Checks if overheating
                break
            if self.run_time != 0:
                self.stime = time.monotonic()
                self.currtime = 0
                print(r'Cycle number:', c)

                self.GrabbingProtocol()

            if self.idle_time != 0:
                print('Entering Idle')
                self.camera.StopGrabbing()
                #self.EnableCamera()
                time.sleep(self.idle_time)
                #self.DisableCamera()
                self.camera.StartGrabbing()

        self.camera.StopGrabbing()
        self.camera.Close()

        self.DataProcess()

if __name__ == '__main__':
    capture_test = CameraTest(20000, 0, 20, 2)
    capture_test.Activate()