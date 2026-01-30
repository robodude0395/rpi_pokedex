
import board
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class BatteryReader:
    def __init__(self, min_voltage=2.5, max_voltage=4.2, channel=ADS.P0):
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage
        self.channel = channel
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        self.ads.gain = 1
        self.chan = AnalogIn(self.ads, self.channel)

    def get_percent(self):
        voltage = self.chan.voltage
        percent = (voltage - self.min_voltage) / (self.max_voltage - self.min_voltage) * 100
        percent = max(0, min(100, percent))
        return int(percent)
