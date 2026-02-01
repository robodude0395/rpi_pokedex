"""
Menu application for Raspberry Pi Pokedex with ST7789 display.

This module provides a hierarchical menu system with battery indicator,
keyboard navigation, and support for nested submenus.
"""

import os
import time
from typing import Callable, List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

from display_and_input import ST7789
from battery_utils import BatteryReader


class BatteryIndicator:
    """
    Display battery percentage on screen.

    Attributes:
        battery: BatteryReader instance for reading battery level.
        font: Font used to render battery percentage.
        pos: (x, y) position for battery text.
        font_color: RGB color tuple for text.
    """

    def __init__(
        self,
        font: ImageFont.FreeTypeFont,
        pos: Tuple[int, int] = (200, 5),
        font_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        """
        Initialize battery indicator.

        Args:
            font: TrueType font for rendering text.
            pos: Position tuple (x, y) for battery display.
            font_color: RGB color tuple for the text.
        """
        self.battery: BatteryReader = BatteryReader()
        self.font: ImageFont.FreeTypeFont = font
        self.pos: Tuple[int, int] = pos
        self.font_color: Tuple[int, int, int] = font_color

    def draw(self, draw_obj: ImageDraw.ImageDraw) -> None:
        """
        Draw battery percentage on the given drawing object.

        Args:
            draw_obj: PIL ImageDraw object to draw on.
        """
        percent: int = self.battery.get_percent()
        text: str = f"{percent}%"
        draw_obj.text(self.pos, text, font=self.font, fill=self.font_color)


MenuItem = Tuple[str, Optional[Union["Menu", Callable[[], None]]]]


class Menu:
    """
    Represents a menu with selectable items.

    A menu contains a list of items, each with a label and optional
    submenu or action callback. Navigation wraps around at boundaries.

    Attributes:
        items: List of (label, target) tuples where target is a Menu,
               callable, or None.
        selected: Index of currently selected item.
        title: Optional menu title displayed at top.
    """

    def __init__(
        self,
        items: List[MenuItem],
        title: Optional[str] = None
    ) -> None:
        """
        Initialize a menu.

        Args:
            items: List of menu items as (label, target) tuples.
            title: Optional title for the menu.
        """
        self.items: List[MenuItem] = items
        self.selected: int = 0
        self.title: Optional[str] = title

    def next(self) -> None:
        """Move selection to next item (wraps to start)."""
        self.selected = (self.selected + 1) % len(self.items)

    def prev(self) -> None:
        """Move selection to previous item (wraps to end)."""
        self.selected = (self.selected - 1) % len(self.items)

    def get_selected(self) -> MenuItem:
        """
        Get currently selected menu item.

        Returns:
            Tuple of (label, target) for selected item.
        """
        return self.items[self.selected]

    def reset_selection(self) -> None:
        """Reset selection to first item."""
        self.selected = 0


class MenuApp:
    """
    Main application for rendering and navigating menus.

    Manages display, input handling, menu navigation stack, and rendering.
    Uses ST7789 display with keyboard input for menu navigation.

    Class Attributes:
        BG_COLOR: Background color RGB tuple.
        FG_COLOR: Foreground text color RGB tuple.
        HIGHLIGHT_COLOR: Highlighted item text color RGB tuple.
        HIGHLIGHT_BG: Highlighted item background color RGB tuple.
        FONT_PATH: Path to TrueType font file.
        FONT_SIZE: Font size in pixels.
        DEBOUNCE_DELAY: Delay in seconds for button debouncing.

    Attributes:
        disp: ST7789 display instance.
        font: Loaded TrueType font.
        current_menu: Currently displayed menu.
        menu_stack: Stack of menus for back navigation.
        running: Flag to control main loop.
        battery_indicator: Battery percentage display.
    """

    BG_COLOR: Tuple[int, int, int] = (0, 0, 0)
    FG_COLOR: Tuple[int, int, int] = (255, 255, 255)
    HIGHLIGHT_COLOR: Tuple[int, int, int] = (255, 255, 255)
    HIGHLIGHT_BG: Tuple[int, int, int] = (80, 80, 80)
    FONT_PATH: str = os.path.join(
        os.path.dirname(ST7789.__file__),
        "Font",
        "Monocraft.ttf"
    )
    FONT_SIZE: int = 22
    DEBOUNCE_DELAY: float = 0.1

    def __init__(self, root_menu: Menu) -> None:
        """
        Initialize the menu application.

        Args:
            root_menu: The top-level menu to display initially.
        """
        self.disp: ST7789.ST7789 = ST7789.ST7789()
        self.disp.Init()
        self.disp.clear()
        self.disp.bl_DutyCycle(50)
        self.font: ImageFont.FreeTypeFont = ImageFont.truetype(
            self.FONT_PATH,
            self.FONT_SIZE
        )
        self.current_menu = root_menu
        self.menu_stack: List[Menu] = []
        self.running: bool = True
        self.battery_indicator: BatteryIndicator = BatteryIndicator(self.font)

    def draw_menu(self) -> None:
        """
        Render the current menu to the display.

        Creates an image with menu items, highlights the selected item,
        displays the battery indicator, and shows the result on screen.
        """
        menu = self.current_menu
        image: Image.Image = Image.new(
            "RGB",
            (self.disp.width, self.disp.height),
            self.BG_COLOR
        )
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(image)
        self.battery_indicator.draw(draw)

        y: int = 0
        if menu.title:
            draw.text(
                (10, y),
                menu.title,
                font=self.font,
                fill=self.FG_COLOR
            )
            y += self.FONT_SIZE + 5

        for i, (item_text, _) in enumerate(menu.items):
            if i == menu.selected:
                draw.rectangle(
                    [
                        (5, y - 2),
                        (self.disp.width - 5, y + self.FONT_SIZE + 2)
                    ],
                    fill=self.HIGHLIGHT_BG,
                )
                draw.text(
                    (10, y),
                    item_text,
                    font=self.font,
                    fill=self.HIGHLIGHT_COLOR
                )
            else:
                draw.text(
                    (10, y),
                    item_text,
                    font=self.font,
                    fill=self.FG_COLOR
                )
            y += self.FONT_SIZE + 8

        image = image.rotate(270)
        self.disp.ShowImage(image)

    def navigate_to_menu(self, target_menu: Menu) -> None:
        """
        Navigate to a new menu, pushing current menu to stack.

        Args:
            target_menu: The menu to navigate to.
        """
        self.menu_stack.append(self.current_menu)
        self.current_menu = target_menu
        self.current_menu.reset_selection()

    def navigate_back(self) -> None:
        """Navigate back to previous menu if stack is not empty."""
        if self.menu_stack:
            self.current_menu = self.menu_stack.pop()

    def handle_input(self) -> None:
        """
        Process keyboard input for menu navigation.

        Handles up/down navigation, selection, and back navigation.
        Includes debouncing delays to prevent multiple triggers.
        """
        disp: ST7789.ST7789 = self.disp

        if disp.digital_read(disp.GPIO_KEY_DOWN_PIN) == 1:
            self.current_menu.next()
            time.sleep(self.DEBOUNCE_DELAY)
        elif disp.digital_read(disp.GPIO_KEY_UP_PIN) == 1:
            self.current_menu.prev()
            time.sleep(self.DEBOUNCE_DELAY)
        elif disp.digital_read(disp.GPIO_KEY2_PIN) == 1:
            self._handle_selection()
            time.sleep(self.DEBOUNCE_DELAY)
        elif disp.digital_read(disp.GPIO_KEY1_PIN) == 1:
            self.navigate_back()
            time.sleep(self.DEBOUNCE_DELAY)

    def _handle_selection(self) -> None:
        """
        Handle selection of current menu item.

        Navigates to submenu if item has a Menu target, executes
        callback if item has a callable target, or does nothing
        if target is None.
        """
        _, target = self.current_menu.get_selected()
        if isinstance(target, Menu):
            self.navigate_to_menu(target)
        elif callable(target):
            target()

    def run(self) -> None:
        """
        Run the main application loop.

        Continuously renders menu and processes input until
        self.running is set to False.
        """
        while self.running:
            self.draw_menu()
            self.handle_input()

    def stop(self) -> None:
        """Stop the application and clean up display."""
        self.running = False
        self.disp.clear()
        self.disp.module_exit()


def create_sample_menus() -> Menu:
    """
    Create sample menu hierarchy for demonstration.

    Returns:
        Root menu with nested submenus.
    """
    def placeholder_action() -> None:
        """Placeholder action for menu items."""
        print("Action not implemented")

    settings_menu = Menu(
        [
            ("Sound", None),
            ("Brightness", None),
        ],
        title="Settings",
    )

    about_menu = Menu(
        [
            ("Version 1.0", None),
            ("License", None),
        ],
        title="About",
    )

    main_menu = Menu(
        [
            ("Start", placeholder_action),
            ("Settings", settings_menu),
            ("About", about_menu),
        ],
        title="Main Menu",
    )

    return main_menu


if __name__ == "__main__":
    root_menu = create_sample_menus()
    app = MenuApp(root_menu)
    try:
        app.run()
    except KeyboardInterrupt:
        app.stop()