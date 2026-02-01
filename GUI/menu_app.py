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


class Page:
    """
    Represents a content page with text and optional image.

    Displays formatted content with an image and text that wraps
    automatically based on the available space and font size.

    Attributes:
        title: Page title displayed at the top.
        text: Main text content to display (wraps automatically).
        image_path: Optional path to JPG/PNG image file.
        image_position: Position of image ('top', 'left', or 'right').
        image_size: Tuple of (width, height) for image scaling.
    """

    def __init__(
        self,
        title: str,
        text: str,
        image_path: Optional[str] = None,
        image_position: str = "top",
        image_size: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Initialize a content page.

        Args:
            title: Title of the page.
            text: Main text content.
            image_path: Optional path to image file (JPG/PNG).
            image_position: Where to place image ('top', 'left', 'right').
            image_size: Optional (width, height) tuple for image resize.
        """
        self.title: str = title
        self.text: str = text
        self.image_path: Optional[str] = image_path
        self.image_position: str = image_position
        self.image_size: Optional[Tuple[int, int]] = image_size
        self._cached_image: Optional[Image.Image] = None

    def _load_image(self) -> Optional[Image.Image]:
        """
        Load and cache the page image.

        Returns:
            PIL Image object or None if no image or load fails.
        """
        if self._cached_image is not None:
            return self._cached_image

        if not self.image_path or not os.path.exists(self.image_path):
            return None

        try:
            img: Image.Image = Image.open(self.image_path)
            if self.image_size:
                img = img.resize(self.image_size, Image.Resampling.LANCZOS)
            self._cached_image = img
            return img
        except Exception as e:
            print(f"Error loading image {self.image_path}: {e}")
            return None

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> List[str]:
        """
        Wrap text to fit within specified width.

        Args:
            text: Text to wrap.
            font: Font used for measuring text.
            max_width: Maximum width in pixels.

        Returns:
            List of text lines that fit within max_width.
        """
        lines: List[str] = []
        words: List[str] = text.split()
        current_line: str = ""

        for word in words:
            test_line: str = f"{current_line} {word}".strip()
            bbox = font.getbbox(test_line)
            text_width: int = bbox[2] - bbox[0]

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines


MenuItem = Tuple[str, Optional[Union["Menu", "Page", Callable[[], None]]]]


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
    BODY_FONT_SIZE: int = 16
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
        self.body_font: ImageFont.FreeTypeFont = ImageFont.truetype(
            self.FONT_PATH,
            self.BODY_FONT_SIZE
        )
        self.current_menu = root_menu
        self.menu_stack: List[Menu] = []
        self.current_page: Optional[Page] = None
        self.scroll_offset: int = 0
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
            if self.current_page:
                self._scroll_page_down()
            else:
                self.current_menu.next()
            time.sleep(self.DEBOUNCE_DELAY)
        elif disp.digital_read(disp.GPIO_KEY_UP_PIN) == 1:
            if self.current_page:
                self._scroll_page_up()
            else:
                self.current_menu.prev()
            time.sleep(self.DEBOUNCE_DELAY)
        elif disp.digital_read(disp.GPIO_KEY2_PIN) == 1:
            if not self.current_page:
                self._handle_selection()
            time.sleep(self.DEBOUNCE_DELAY)
        elif disp.digital_read(disp.GPIO_KEY1_PIN) == 1:
            if self.current_page:
                self.current_page = None  # Exit page view
            else:
                self.navigate_back()
            time.sleep(self.DEBOUNCE_DELAY)

    def _handle_selection(self) -> None:
        """
        Handle selection of current menu item.

        Navigates to submenu if item has a Menu target, displays page
        if item has a Page target, or executes callback if item has a
        callable target.
        """
        _, target = self.current_menu.get_selected()
        if isinstance(target, Menu):
            self.navigate_to_menu(target)
        elif isinstance(target, Page):
            self.current_page = target
            self.scroll_offset = 0
        elif callable(target):
            target()

    def draw_page(self, page: Page) -> None:
        """
        Render a page with text and optional image.

        Args:
            page: Page object to render.
        """
        image: Image.Image = Image.new(
            "RGB",
            (self.disp.width, self.disp.height),
            self.BG_COLOR
        )
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(image)
        self.battery_indicator.draw(draw)

        y: int = 0
        x: int = 10
        content_width: int = self.disp.width - 20

        # Draw title
        draw.text(
            (x, y),
            page.title,
            font=self.font,
            fill=self.FG_COLOR
        )
        y += self.FONT_SIZE + 10

        # Load and position image
        page_image: Optional[Image.Image] = page._load_image()
        if page_image:
            if page.image_position == "top":
                img_x: int = (self.disp.width - page_image.width) // 2
                image.paste(page_image, (img_x, y))
                y += page_image.height + 10
            elif page.image_position == "left":
                image.paste(page_image, (x, y))
                x += page_image.width + 10
                content_width -= (page_image.width + 10)
            elif page.image_position == "right":
                img_x = self.disp.width - page_image.width - 10
                image.paste(page_image, (img_x, y))
                content_width -= (page_image.width + 10)

        # Draw wrapped text with scrolling
        lines: List[str] = page._wrap_text(
            page.text,
            self.body_font,
            content_width
        )
        line_height: int = self.BODY_FONT_SIZE + 4
        start_line: int = self.scroll_offset
        
        for i, line in enumerate(lines[start_line:]):
            if y + self.BODY_FONT_SIZE > self.disp.height - 10:
                break  # Stop if we run out of space
            draw.text((x, y), line, font=self.body_font, fill=self.FG_COLOR)
            y += line_height

        image = image.rotate(270)
        self.disp.ShowImage(image)

    def _scroll_page_up(self) -> None:
        """Scroll page content up (show earlier lines)."""
        if self.scroll_offset > 0:
            self.scroll_offset -= 1

    def _scroll_page_down(self) -> None:
        """Scroll page content down (show later lines)."""
        if self.current_page:
            # Calculate total lines
            content_width: int = self.disp.width - 20
            lines: List[str] = self.current_page._wrap_text(
                self.current_page.text,
                self.body_font,
                content_width
            )
            # Don't scroll past the last line
            if self.scroll_offset < len(lines) - 1:
                self.scroll_offset += 1

    def run(self) -> None:
        """
        Run the main application loop.

        Continuously renders menu or page and processes input until
        self.running is set to False.
        """
        while self.running:
            if self.current_page:
                self.draw_page(self.current_page)
            else:
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

    # Sample Pokemon pages
    pikachu_page = Page(
        title="Pikachu",
        text="Pikachu is an Electric-type Pokemon. When several of "
             "these Pokemon gather, their electricity can build and "
             "cause lightning storms. It has small electric sacs on "
             "both its cheeks. If threatened, it looses electric charges "
             "from the sacs.",
        image_path='image.jpg',  # Set to actual image path like "images/pikachu.jpg"
        image_position="top",
        image_size=(100, 100),
    )

    charizard_page = Page(
        title="Charizard",
        text="Charizard is a Fire and Flying-type Pokemon. It spits fire "
             "that is hot enough to melt boulders. Known to cause forest "
             "fires unintentionally. When expelling a blast of super hot "
             "fire, the red flame at the tip of its tail burns more intensely.",
        image_path=None,  # Set to actual image path
        image_position="top",
        image_size=(100, 100),
    )

    # Pokemon menu
    pokemon_menu = Menu(
        [
            ("Pikachu", pikachu_page),
            ("Charizard", charizard_page),
        ],
        title="Pokedex",
    )

    settings_menu = Menu(
        [
            ("Sound", None),
            ("Brightness", None),
        ],
        title="Settings",
    )

    about_page = Page(
        title="About Pokedex",
        text="Raspberry Pi Pokedex v1.0. A portable Pokemon encyclopedia "
             "with information and images of your favorite Pokemon. "
             "Navigate using the buttons and explore the world of Pokemon!",
        image_path=None,
        image_position="top",
    )

    main_menu = Menu(
        [
            ("Pokedex", pokemon_menu),
            ("Settings", settings_menu),
            ("About", about_page),
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