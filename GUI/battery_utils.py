
import board
import adafruit_ads1x15.ads1015 as ADS1015
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1x15 as ADS

class BatteryReader:
    def __init__(self, min_voltage=2.5, max_voltage=4.2, channel=ADS.P0):
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage
        self.channel = channel
        self.i2c = board.I2C()
        self.ads = ADS1015(self.i2c)
        self.chan = AnalogIn(self.ads, self.channel)

    def get_percent(self):
        voltage = self.chan.voltage
        percent = (voltage - self.min_voltage) / (self.max_voltage - self.min_voltage) * 100
        percent = max(0, min(100, percent))
        return int(percent)
