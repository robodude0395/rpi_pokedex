# display_and_input

A simple library for driving the ST7789 display and handling input for Raspberry Pi projects.

## Installation (editable/development mode)

From the root of your project (where `setup.py` or `pyproject.toml` will be):

```bash
pip install -e ./display_and_input
```

## Usage

```python
from display_and_input import ST7789
from display_and_input import config
# ...
```

## Fonts

Font files are included in the `Font/` subdirectory. Reference them in your code like:

```python
from PIL import ImageFont
import os
font_path = os.path.join(os.path.dirname(__file__), 'Font/Font01.ttf')
font = ImageFont.truetype(font_path, 25)
```

## Requirements

- spidev
- numpy
- gpiozero (or lgpio, RPi.GPIO)
- Pillow

Install requirements with:

```bash
pip install -r requirements.txt
```
