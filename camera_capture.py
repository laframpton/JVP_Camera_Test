import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import argparse


def capture_frames(number_of_frames=300, gpio_line='3', temperature_region='FpgaCore'):

    cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    cam.Open()

    cam.UserSetSelector = "Default"
    cam.UserSetLoad.Execute()

    cam.LineSelector = "Line" + gpio_line
    cam.LineMode = "Input"

    cam.TriggerSelector = "FrameStart"
    cam.TriggerSource = "Line" + gpio_line
    cam.TriggerMode = "On"

    cam.StartGrabbingMax(number_of_frames)

    images = []
    grabbing_details = []

    cam.DeviceTemperatureSelector.Value = temperature_region
    print('Capturing the temperature at: ' + cam.DeviceTemperatureSelector.Value)

    while cam.IsGrabbing():
        grab_result = cam.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            images.append(grab_result.Array)
            grabbing_details.append((grab_result.TimeStamp / 1e9, cam.DeviceTemperature.Value))

        grab_result.Release()

    cam.Close()

    grabbing_details = pd.DataFrame(grabbing_details, columns=['Time Stamp', 'Temperature'])

    plt.plot(grabbing_details['Temperature'], label='Temperature @ ' + temperature_region, color='blue')
    plt.axhline(85, label="Critical Temperature Threshold", color='orange')
    plt.legend()
    plt.ylim([30, 100])

    return grabbing_details


if __name__ == "main":
    parser = argparse.ArgumentParser()

    parser.add_argument('-n', '--NumberOfFrames', default=300, type=int, help="Number of frames to be captured")
    parser.add_argument('-l', '--GPIOLine', default='3', type=str, help="GPIO line for the hardware triggers")
    parser.add_argument('-r', '--TemperatureRegion', default='FpgaCore', type=str, help="Temperature measuring region")

    args = parser.parse_args()

    grab_details = capture_frames(args.NumberOfFrames, args.GPIOLine, args.TemperatureRegion)

    # plt.show()

    print("Complete")
    print(grab_details)