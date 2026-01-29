
import time
import board
from adafruit_ads1x15 import ADS1015, AnalogIn, ads1x15

from PIL import Image, ImageDraw, ImageFont
import os

from display_and_input import ST7789
from display_and_input import config

# Display setup
disp = ST7789.ST7789()
disp.Init()
disp.clear()
disp.bl_DutyCycle(50)

# Font setup (use package font path)
font_path = os.path.join(os.path.dirname(ST7789.__file__), 'Font', 'Monocraft.ttf')
Font1 = ImageFont.truetype(font_path, 25)

# ADC setup
i2c = board.I2C()
ads = ADS1015(i2c)
chan = AnalogIn(ads, ads1x15.Pin.A0)

# Battery voltage range (adjust as needed)
MIN_VOLTAGE = 3.0
MAX_VOLTAGE = 4.2

def voltage_to_percent(voltage):
    percent = (voltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE) * 100
    percent = max(0, min(100, percent))
    return int(percent)

while True:
    voltage = chan.voltage
    percent = voltage_to_percent(voltage)
    image = Image.new("RGB", (disp.width, disp.height), "WHITE")
    draw = ImageDraw.Draw(image)
    text = f"Battery: {percent}%"
    draw.text((20, 20), text, fill="BLACK", font=Font1)
    im_r = image.rotate(270)
    disp.ShowImage(im_r)
    time.sleep(2)