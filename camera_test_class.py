import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import numpy as np
import time

class CameraTest:
    def __init__(self, exposure_time, idle_time, run_time, cycles=1, gpio_line='3'):
        self.exposure_time = exposure_time
        self.idle_time = idle_time
        self.run_time = run_time
        self.cycles = cycles
        self.gpio_line = gpio_line

        self.heat_flag = 0
        self.images = []
        self.grabbing_details = []

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        print(self.camera)

    def data_process(self):
        self.grabbing_details = pd.DataFrame(self.grabbing_details, columns=['Time Stamp', 'Temperature'])

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
        np.savetxt('firstframe.txt', self.images[1], fmt='%d')

    def run(self): #TODO: Allow an input to decide whether this is being triggered with software or with hardware triggering
        self.camera.Open()
        self.camera.TriggerSource.Value = "Software" # This sets the camera to work soley off of this software
        #self.camera.LineSelector = "Line" + gpio_line
        #self.camera.LineMode = "Input"

        #self.camera.TriggerSelector = "FrameStart"
        #self.camera.TriggerSource = "Line" + gpio_line
        #self.camera.TriggerMode = "On"
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

                while self.camera.IsGrabbing() and (self.currtime - self.stime < self.run_time):
                    self.grab_result = self.camera.RetrieveResult(self.exposure_time, pylon.TimeoutHandling_ThrowException)
                    self.currtime = time.monotonic()

                    if self.grab_result.GrabSucceeded():
                        self.images.append(self.grab_result.Array)
                        self.grabbing_details.append((self.grab_result.TimeStamp / 1e9, self.camera.DeviceTemperature.Value))

                    if self.camera.DeviceTemperature.Value >= 85:
                        print(r'Warning, ', self.camera.DeviceTemperature.Value)
                    elif self.camera.DeviceTemperature.Value >= 100: # If overheating
                        print('CRITICAL ERROR, COOL CAMERA')
                        self.heat_flag = 1
                        break

                    self.grab_result.Release()
            if self.idle_time != 0:
                print('Entering Idle')
                #run(
                #    "echo '0' > '/sys/bus/usb/devices/2-1.4/power/autosuspend_delay_ms'",
                #    shell=True,
                #)
                #run("echo 'auto' > '/sys/bus/usb/devices/2-1.4/power/control'", shell=True)
                time.sleep(self.idle_time)
                #run("echo 'on' > '/sys/bus/usb/devices/2-1.4/power/control'", shell=True)

        self.camera.StopGrabbing()
        self.camera.Close()

        self.data_process()

if __name__ == '__main__':
    capture_test = CameraTest(20000, 0, 20, 2)
    capture_test.run()