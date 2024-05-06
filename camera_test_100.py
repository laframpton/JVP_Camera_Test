import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import numpy as np

class CameraTest:
    def __init__(self, max_frames, exposure_time, idle_time, run_time, cycles):
        self.max_frames = max_frames
        self.exposure_time = exposure_time
        self.idle_time = idle_time
        self.run_time = run_time
        self.cycles = cycles

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        print(self.camera)

    def run(self): #TODO: Allow an input to decide whether this is being triggered with software or with hardware triggering
        self.camera.Open()
        self.camera.TriggerSource.Value = "Software" # This sets the camera to work soley off of this software

        self.camera.StartGrabbingMax(self.max_frames)

        self.images = []
        self.grabbing_details = []

        self.camera.DeviceTemperatureSelector.Value = "FpgaCore"
        print('Capturing the temperature at: ' + self.camera.DeviceTemperatureSelector.Value)

        while self.camera.IsGrabbing():
            self.grab_result = self.camera.RetrieveResult(self.exposure_time, pylon.TimeoutHandling_ThrowException)

            if self.grab_result.GrabSucceeded():
                self.images.append(self.grab_result.Array)
                self.grabbing_details.append((self.grab_result.TimeStamp / 1e9, self.camera.DeviceTemperature.Value))

            self.grab_result.Release()

        self.camera.Close()

        self.grabbing_details = pd.DataFrame(self.grabbing_details, columns=['Time Stamp', 'Temperature'])

        plt.plot(self.grabbing_details['Temperature'], label='Temperature @ ' + "FpgaCore", color='blue')
        plt.axhline(85, label="Critical Temperature Threshold", color='orange')
        plt.legend()
        plt.ylim([30, 100])

        print(self.grabbing_details)

        ### For testing
        print(pd.DataFrame(self.images[0]).describe())

        self.avg_intensity = np.empty((0,0))
        for frame in range(self.max_frames):
            self.mean = np.array(self.images[frame]).mean()
            self.avg_intensity = np.append(self.avg_intensity,self.mean)

        print(self.avg_intensity)

if __name__ == '__main__':
    capture_test = CameraTest(300, 20000, 0, 300, 1)
    capture_test.run()