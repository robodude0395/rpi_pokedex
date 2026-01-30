
import board
from adafruit_ads1x15 import ADS1115, AnalogIn, ads1x15

class BatteryReader:
    def __init__(self, min_voltage=2.5, max_voltage=4.2):
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage
        # Create the I2C bus
        self.i2c = board.I2C()
        # Create the ADC object using the I2C bus
        self.ads = ADS1115(self.i2c)
        # Create single-ended input on channel 0
        self.chan = AnalogIn(self.ads, ads1x15.Pin.A0)

    def get_percent(self):
        voltage = self.chan.voltage
        percent = (voltage - self.min_voltage) / (self.max_voltage - self.min_voltage) * 100
        percent = max(0, min(100, percent))
        return int(percent)
