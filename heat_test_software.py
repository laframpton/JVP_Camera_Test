import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import numpy as np
import time
from subprocess import run
import pickle

import RPi.GPIO as GPIO


class HeatTest:
    def __init__(self, exposure_time, idle_time, run_time, cycles=1, gpio_line='3', led_ring=31, frame_factor=250, hardware_trigger=False, intensity_protocol='number'):
        self.exposure_time = exposure_time
        self.idle_time = idle_time
        self.run_time = run_time
        self.cycles = cycles
        self.gpio_line = gpio_line
        self.frame_factor = frame_factor
        self.hardware_trigger = hardware_trigger
        self.intensity_protocol = intensity_protocol
        self.led_ring = led_ring

        self.heat_flag = 0
        self.frame_count = 1
        self.images = []
        self.grabbing_details = []
        self.avg_intensity = np.empty((0,0))
        self.slice_intensity = np.empty((0,0))

        # Setup for lightring
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.led_ring, GPIO.OUT)
        GPIO.output(self.led_ring, GPIO.LOW)

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        print(self.camera)

    def DataProcess(self):
        self.grabbing_details = pd.DataFrame(self.grabbing_details, columns=['Time Stamp', 'Local Time', 'Temperature'])
        print(self.grabbing_details)

        ### For testing
        print(pd.DataFrame(self.images[0]).describe())

        print(self.avg_intensity)

        ### Saving Data
        with open('avg_intensities.pkl', 'wb') as file:
            pickle.dump(self.avg_intensity, file)
        with open('grabbing_details.pkl', 'wb') as file:
            pickle.dump(self.grabbing_details, file)

        # Subsection Image
        self.ImageSubsection()

        with open('slice_intensities.pkl', 'wb') as file:
            pickle.dump(self.slice_intensity, file)

        self.FullImageSave()

    def FullImageSave(self):
        for frame in range(len(self.images)):
            plt.imshow(self.images[frame], cmap=plt.cm.binary)
            plt.axis('on') # Hide axes
            plt.savefig((str(frame) + 'frame(' + str(time.monotonic()) + ').png'), dpi=100, pad_inches=0.0, bbox_inches='tight')

    def ImageSubsection(self):
        for frame in range(len(self.images)):
            self.mean = np.array(self.images[frame])[275:325,800:850].mean()
            self.slice_intensity = np.append(self.slice_intensity,self.mean)
            plt.imshow(np.array(self.images[frame])[275:325,800:850], cmap=plt.cm.binary)
            plt.axis('on')
            plt.savefig(str(frame) + 'slice(' + str(time.monotonic()) + ').png', dpi=100, pad_inches=0.0, bbox_inches='tight')

    def HardwareTrigger(self):
        self.camera.LineSelector = "Line" + self.gpio_line
        self.camera.LineMode = "Input"

        self.camera.TriggerSelector = "FrameStart"
        self.camera.TriggerSource = "Line" + self.gpio_line

    def IntensityProtocol(self):
        if self.intensity_protocol == 'number':
            self.frame_count += 1
            if self.frame_count % self.frame_factor == 0:
                self.images.append(self.grab_result.Array)
                self.mean = self.grab_result.Array.mean()
                print(self.mean)
                print(self.frame_count)
                print('Frame Stored')
                self.avg_intensity = np.append(self.avg_intensity,self.mean)
        elif self.intensity_protocol == 'state':
            self.images.append(self.grab_result.Array)
            self.mean = self.grab_result.Array.mean()
            self.avg_intensity = np.append(self.avg_intensity,self.mean)

    def GrabbingProtocol(self):
        while self.camera.IsGrabbing() and (self.currtime - self.stime < self.run_time):
            self.grab_result = self.camera.RetrieveResult(self.exposure_time, pylon.TimeoutHandling_ThrowException)
            self.currtime = time.monotonic()

            if self.grab_result.GrabSucceeded():
                self.IntensityProtocol() # if self.intensity_protocol == 'number':
                self.grabbing_details.append((self.grab_result.TimeStamp / 1e9, time.localtime(), self.camera.DeviceTemperature.Value))

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

    def WritePin(self, pin: int, value: int) -> None:
        try:
            GPIO.output(pin, value)
        except ValueError:
            self.log.info(f"Pin {pin} is not a valid output pin.")
        finally:
            pass
        
    def SetLightRing(self, value: int):
        self.WritePin(self.led_ring, value)

    def Activate(self):
        try:
            self.EnableCamera()
        except:
            pass
        
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
                self.SetLightRing(1)
                self.IntensityProtocol() # if self.intensity_protocol == 'state'
                self.stime = time.monotonic()
                self.currtime = 0
                print(r'Cycle number:', c)

                self.GrabbingProtocol()

            if self.idle_time != 0:
                self.SetLightRing(0)
                self.IntensityProtocol() # if self.intensity_protocol == 'state'
                print('Entering Idle')
                self.camera.StopGrabbing()
                self.EnableCamera()
                time.sleep(self.idle_time)
                self.DisableCamera()
                self.camera.StartGrabbing()

        try:
            self.SetLightRing(0)
        except:
            pass
        self.camera.StopGrabbing()
        self.camera.Close()
        try:
            self.DisableCamera()
        except:
            pass
        self.DataProcess()

if __name__ == '__main__':
    capture_test = HeatTest(8000, 20, 10, 2, hardware_trigger=False)
    capture_test.Activate()
    GPIO.cleanup()