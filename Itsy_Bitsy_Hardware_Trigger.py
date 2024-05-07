import board
import digitalio
import time

# Sets the pins for the signal output
signal_pin = D10

# Sets the direction of the pin for the signal
signal = digitalio.DigitalInOut(signalPin)
signal.direction = digitalio.Direction.OUTPUT

startTime = time.monotonic()

class Trigger:
    def __init__(self, frequency, duration, run_time, idle_time, cycles):
        self.frequency = frequency # number of pulses per second
        self.wait_time = 1/frequency/2 # seconds between state change
        self.duration = duration # seconds
        self.startTime = time.monotonic()

    def run(self):
        while time.monotonic - self.startTime < self.duration:
            signal.value = True
            time.sleep(self.wait_time)
            signal.value = False
            time.sleep(self.wait_time)

        time.sleep(waitTime)
        led.value = False

        print("Finished")

SC = MonoSeries()
SC.dataCollect(10)
print(SC)
