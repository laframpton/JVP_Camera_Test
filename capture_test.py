import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import numpy as np

MAX_FRAMES = 300
EXPOSURE_TIME = 20000

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
print(camera)

camera.Open()
camera.TriggerSource.Value = "Software" # This sets the camera to work soley off of this software

camera.StartGrabbingMax(MAX_FRAMES)

images = []
grabbing_details = []

camera.DeviceTemperatureSelector.Value = "FpgaCore"
print('Capturing the temperature at: ' + camera.DeviceTemperatureSelector.Value)

while camera.IsGrabbing():
    grab_result = camera.RetrieveResult(EXPOSURE_TIME, pylon.TimeoutHandling_ThrowException)

    if grab_result.GrabSucceeded():
        images.append(grab_result.Array)
        grabbing_details.append((grab_result.TimeStamp / 1e9, camera.DeviceTemperature.Value))

    grab_result.Release()

camera.Close()

grabbing_details = pd.DataFrame(grabbing_details, columns=['Time Stamp', 'Temperature'])

plt.plot(grabbing_details['Temperature'], label='Temperature @ ' + "FpgaCore", color='blue')
plt.axhline(85, label="Critical Temperature Threshold", color='orange')
plt.legend()
plt.ylim([30, 100])

print(grabbing_details)

### For testing
print(pd.DataFrame(images[0]).describe())

avg_intensity = np.empty((0,0))
for frame in range(MAX_FRAMES):
    mean = np.array(images[frame]).mean()
    avg_intensity = np.append(avg_intensity,mean)

print(avg_intensity)