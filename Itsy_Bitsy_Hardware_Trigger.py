import board
import digitalio
import time

# Sets the pins for the signal output
signal_pin = D10

# Sets the direction of the pin for the signal
signal = digitalio.DigitalInOut(signalPin)
signal.direction = digitalio.Direction.OUTPUT

class Trigger:
    def __init__(self, run_time, idle_time, cycles):

        self.

    def __str__(self):
        return f"Stamps:{self.stamps} \nData:{self.data}"

    def lightDebounce(self, waitTime=0.2):
        led.value = True
        for i in range(8):
            timeMono = time.monotonic()
            if i == 0:
                self.stamps.append(timeMono)
            timeMonoInt = int(10 * timeMono)
            self.data.append(timeMonoInt)
            time.sleep(0.1)

        time.sleep(waitTime)
        led.value = False

    def dataCollect(self, num):
        while len(self.data) < num * 8:
            if switch.value:
                led.value = False

            else:
                self.lightDebounce()

        print("Finished")

SC = MonoSeries()
SC.dataCollect(10)
print(SC)
