import os
import time

from PIL import Image, ImageDraw, ImageFont

from display_and_input import ST7789

class Menu:
    def __init__(self, items, title=None):
        self.items = items
        self.selected = 0
        self.title = title

    def next(self):
        self.selected = (self.selected + 1) % len(self.items)

    def prev(self):
        self.selected = (self.selected - 1) % len(self.items)

    def get_selected(self):
        return self.items[self.selected]

class MenuApp:
    BG_COLOR = (0, 0, 0)
    FG_COLOR = (255, 255, 255)
    HIGHLIGHT_COLOR = (255, 255, 255)
    HIGHLIGHT_BG = (80, 80, 80)
    FONT_PATH = os.path.join(os.path.dirname(ST7789.__file__), 'Font', 'Monocraft.ttf')
    FONT_SIZE = 22

    def __init__(self, menus):
        self.disp = ST7789.ST7789()
        self.disp.Init()
        self.disp.clear()
        self.disp.bl_DutyCycle(50)
        self.font = ImageFont.truetype(self.FONT_PATH, self.FONT_SIZE)
        self.menus = menus
        self.current_menu = 0
        self.running = True

    def draw_menu(self):
        menu = self.menus[self.current_menu]
        image = Image.new('RGB', (self.disp.width, self.disp.height), self.BG_COLOR)
        draw = ImageDraw.Draw(image)
        y = 10
        if menu.title:
            draw.text((10, y), menu.title, font=self.font, fill=self.FG_COLOR)
            y += self.FONT_SIZE + 5
        for i, item in enumerate(menu.items):
            if i == menu.selected:
                draw.rectangle([(5, y-2), (self.disp.width-5, y+self.FONT_SIZE+2)], fill=self.HIGHLIGHT_BG)
                draw.text((10, y), item, font=self.font, fill=self.HIGHLIGHT_COLOR)
            else:
                draw.text((10, y), item, font=self.font, fill=self.FG_COLOR)
            y += self.FONT_SIZE + 8
        image = image.rotate(270)
        self.disp.ShowImage(image)

    def handle_input(self):
        disp = self.disp
        # Replace with your actual button logic
        if disp.digital_read(disp.GPIO_KEY_UP_PIN) == 1:
            self.menus[self.current_menu].next()
            time.sleep(0.1)

        elif disp.digital_read(disp.GPIO_KEY_DOWN_PIN) == 1:
            self.menus[self.current_menu].prev()
            time.sleep(0.1)

        elif disp.digital_read(disp.GPIO_KEY2_PIN) == 1:
            # Example: go to next menu or select
            self.current_menu = (self.current_menu + 1) % len(self.menus)
            time.sleep(0.1)

        """
        elif disp.digital_read(disp.GPIO_KEY1_PIN) == 1:
            self.running = False
            time.sleep(0.2)
        """

    def run(self):
        while self.running:
            self.draw_menu()
            self.handle_input()

if __name__ == '__main__':
    main_menu = Menu(['Start', 'Settings', 'About'], title='Main Menu')
    settings_menu = Menu(['Sound', 'Brightness', 'Back'], title='Settings')
    app = MenuApp([main_menu, settings_menu])
    app.run()
