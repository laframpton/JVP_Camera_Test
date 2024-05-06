import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import numpy as np

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
print(camera)

camera.Open()
camera.TriggerSource.Value = "Software" # This sets the camera to work soley off of this software

camera.StartGrabbingMax(300)

images = []
grabbing_details = []

camera.DeviceTemperatureSelector.Value = "FpgaCore"
print('Capturing the temperature at: ' + camera.DeviceTemperatureSelector.Value)

while camera.IsGrabbing():
    grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

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
print(images[1])
pd.DataFrame(images[1]).to_csv('imagesdf.csv')