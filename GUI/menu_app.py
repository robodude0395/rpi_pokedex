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
        right_padding: int = 0,
        battery_font_size: int = 12,
    ) -> None:
        """
        Initialize battery indicator.

        Args:
            font: TrueType font for rendering text.
            pos: Position tuple (x, y) for battery display.
            font_color: RGB color tuple for the text.
            right_padding: Right padding in pixels from screen edge.
            battery_font_size: Font size for battery percentage text.
        """
        self.battery: BatteryReader = BatteryReader()
        self.font: ImageFont.FreeTypeFont = font
        self.pos: Tuple[int, int] = pos
        self.font_color: Tuple[int, int, int] = font_color
        self.right_padding: int = right_padding
        self.battery_font_size: int = battery_font_size

    def draw(self, draw_obj: ImageDraw.ImageDraw) -> None:
        """
        Draw battery percentage on the given drawing object.

        Args:
            draw_obj: PIL ImageDraw object to draw on.
        """
        percent: int = self.battery.get_percent()
        
        # Battery dimensions
        battery_width: int = 40
        battery_height: int = 18
        terminal_width: int = 3
        terminal_height: int = 8
        border_thickness: int = 2
        
        # Position for battery body (from right edge with padding)
        # pos[0] is display width minus battery width minus padding
        body_x: int = self.pos[0] - battery_width - terminal_width - self.right_padding
        body_y: int = self.pos[1]
        
        # Draw battery body outline (light grey)
        draw_obj.rectangle(
            [(body_x, body_y), (body_x + battery_width, body_y + battery_height)],
            outline=(200, 200, 200),
            width=border_thickness
        )
        
        # Draw battery terminal (light grey)
        terminal_x: int = body_x + battery_width
        terminal_y: int = body_y + (battery_height - terminal_height) // 2
        draw_obj.rectangle(
            [(terminal_x, terminal_y), (terminal_x + terminal_width, terminal_y + terminal_height)],
            fill=(200, 200, 200)
        )
        
        # Calculate fill width based on battery percentage
        inner_padding: int = border_thickness + 1
        fill_area_width: int = battery_width - (inner_padding * 2)
        fill_width: int = int(fill_area_width * (percent / 100))
        
        # Draw battery fill (white)
        if fill_width > 0:
            draw_obj.rectangle(
                [
                    (body_x + inner_padding, body_y + inner_padding),
                    (body_x + inner_padding + fill_width, body_y + battery_height - inner_padding)
                ],
                fill=(255, 255, 255)
            )
        
        # Create smaller font for battery percentage
        try:
            battery_font: ImageFont.FreeTypeFont = MenuApp._load_font(
                self.battery_font_size
            )
        except Exception:
            battery_font = self.font  # Fallback to original font
        
        # Draw percentage text overlaid on battery with contrast
        text: str = f"{percent}%"
        bbox = battery_font.getbbox(text)
        text_width: int = bbox[2] - bbox[0]
        text_height: int = bbox[3] - bbox[1]
        
        # Center text on battery
        text_x: int = body_x + (battery_width - text_width) // 2
        text_y: int = body_y + (battery_height - text_height) // 2 - 1
        
        # Determine text color based on what's behind the text center
        # Text center is at battery_width / 2, so check if fill extends past center
        battery_center: int = battery_width // 2
        fill_end_position: int = inner_padding + fill_width
        
        if fill_end_position > battery_center:
            # Text is over white fill - use black text
            text_color = (0, 0, 0)
        else:
            # Text is over empty area - use white text
            text_color = (255, 255, 255)
        
        draw_obj.text((text_x, text_y), text, font=battery_font, fill=text_color)


class BasePage:
    """
    Base class for scrollable content pages.

    Provides basic text display and scrolling functionality.

    Attributes:
        title: Page title displayed at the top.
        text: Main text content to display (wraps automatically).
    """

    def __init__(self, title: str, text: str) -> None:
        """
        Initialize a base page.

        Args:
            title: Title of the page.
            text: Main text content.
        """
        self.title: str = title
        self.text: str = text

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


class Page(BasePage):
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
        super().__init__(title, text)
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


class PokemonDescriptionPage(BasePage):
    """
    Specialized page for displaying Pokemon information.

    Displays Pokemon image on left, info box on right (dex number,
    types, height, weight), and scrollable description text at bottom.

    Attributes:
        name: Pokemon name (used as title).
        dex_number: National Pokedex number.
        types: List of (type_name, bg_color) tuples.
        height: Height as string (e.g., "0.7m").
        weight: Weight as string (e.g., "6.9kg").
        description: Scrollable description text.
        image_path: Path to Pokemon image file.
    """

    def __init__(
        self,
        name: str,
        dex_number: int,
        types: List[Tuple[str, Tuple[int, int, int]]],
        height: str,
        weight: str,
        description: str,
        image_path: str,
    ) -> None:
        """
        Initialize a Pokemon description page.

        Args:
            name: Pokemon name.
            dex_number: National Pokedex number.
            types: List of (type_name, bg_color_rgb) tuples.
            height: Height string.
            weight: Weight string.
            description: Full description text (scrollable).
            image_path: Path to Pokemon image.
        """
        super().__init__(name, description)
        self.name: str = name
        self.dex_number: int = dex_number
        self.types: List[Tuple[str, Tuple[int, int, int]]] = types
        self.height: str = height
        self.weight: str = weight
        self.description: str = description
        self.image_path: str = image_path
        self._cached_image: Optional[Image.Image] = None

    def _load_image(self) -> Optional[Image.Image]:
        """
        Load and cache the Pokemon image.

        Returns:
            PIL Image object or None if load fails.
        """
        if self._cached_image is not None:
            return self._cached_image

        if not self.image_path or not os.path.exists(self.image_path):
            return None

        try:
            img: Image.Image = Image.open(self.image_path)
            # Resize to fixed size for Pokemon sprites
            from display_and_input import ST7789
            img = img.resize((MenuApp.POKEMON_IMAGE_SIZE, MenuApp.POKEMON_IMAGE_SIZE), Image.Resampling.LANCZOS)
            self._cached_image = img
            return img
        except Exception as e:
            print(f"Error loading image {self.image_path}: {e}")
            return None


MenuItem = Tuple[str, Optional[Union["Menu", "BasePage", Callable[[], None]]]]


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
    MENU_FONT_SIZE: int = 16
    BODY_FONT_SIZE: int = 10
    DEBOUNCE_DELAY: float = 0.1
    
    # Padding and spacing constants
    PADDING_HORIZONTAL: int = 10
    PADDING_VERTICAL: int = 5
    PADDING_EDGE: int = 5
    HIGHLIGHT_PADDING: int = 2
    MENU_ITEM_SPACING: int = 8
    TITLE_SPACING: int = 10
    IMAGE_SPACING: int = 10
    BODY_LINE_SPACING: int = 4
    PAGE_BOTTOM_MARGIN: int = 10
    TOP_BAR_HEIGHT: int = 35
    POKEMON_IMAGE_SIZE: int = 100    
    @staticmethod
    def _load_font(size: int) -> ImageFont.FreeTypeFont:
        """Load TrueType font with specified size.
        
        Args:
            size: Font size in pixels.
            
        Returns:
            Loaded font object.
        """
        font_path: str = os.path.join(
            os.path.dirname(ST7789.__file__),
            "Font",
            "Monocraft.ttf"
        )
        return ImageFont.truetype(font_path, size)

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
        self.font: ImageFont.FreeTypeFont = self._load_font(self.FONT_SIZE)
        self.menu_font: ImageFont.FreeTypeFont = self._load_font(self.MENU_FONT_SIZE)
        self.body_font: ImageFont.FreeTypeFont = self._load_font(self.BODY_FONT_SIZE)
        self.current_menu = root_menu
        self.menu_stack: List[Menu] = []
        self.current_page: Optional[Page] = None
        self.scroll_offset: int = 0
        self.running: bool = True
        self.battery_indicator: BatteryIndicator = BatteryIndicator(
            self.font, right_padding=10, battery_font_size=10
        )

    def _get_page_content_width(self) -> int:
        """Calculate available width for page content.
        
        Returns:
            Content width in pixels.
        """
        return self.disp.width - (self.PADDING_HORIZONTAL * 2)

    def _display_image(self, image: Image.Image) -> None:
        """Rotate and display image on screen.
        
        Args:
            image: Image to display.
        """
        image = image.rotate(270)
        self.disp.ShowImage(image)

    def _create_display_image(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        """Create a new display image with battery indicator.
        
        Returns:
            Tuple of (image, draw) objects.
        """
        image: Image.Image = Image.new(
            "RGB",
            (self.disp.width, self.disp.height),
            self.BG_COLOR
        )
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(image)
        self.battery_indicator.draw(draw)
        return image, draw

    def draw_menu(self) -> None:
        """
        Render the current menu to the display.

        Creates an image with menu items, highlights the selected item,
        displays the battery indicator, and shows the result on screen.
        """
        menu = self.current_menu
        image, draw = self._create_display_image()

        y: int = 0
        if menu.title:
            draw.text(
                (self.PADDING_HORIZONTAL, y),
                menu.title,
                font=self.font,
                fill=self.FG_COLOR
            )
            y += self.FONT_SIZE + self.PADDING_VERTICAL

        for i, (item_text, _) in enumerate(menu.items):
            if i == menu.selected:
                draw.rectangle(
                    [
                        (self.PADDING_EDGE, y - self.HIGHLIGHT_PADDING),
                        (self.disp.width - self.PADDING_EDGE, y + self.MENU_FONT_SIZE + self.HIGHLIGHT_PADDING)
                    ],
                    fill=self.HIGHLIGHT_BG,
                )
                draw.text(
                    (self.PADDING_HORIZONTAL, y),
                    item_text,
                    font=self.menu_font,
                    fill=self.HIGHLIGHT_COLOR
                )
            else:
                draw.text(
                    (self.PADDING_HORIZONTAL, y),
                    item_text,
                    font=self.menu_font,
                    fill=self.FG_COLOR
                )
            y += self.MENU_FONT_SIZE + self.MENU_ITEM_SPACING

        self._display_image(image)

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
        elif isinstance(target, BasePage):
            self.current_page = target
            self.scroll_offset = 0
        elif callable(target):
            target()

    def draw_page(self, page: BasePage) -> None:
        """
        Render a page with text and optional image.

        Args:
            page: Page object to render.
        """
        if isinstance(page, PokemonDescriptionPage):
            self._draw_pokemon_page(page)
        else:
            self._draw_standard_page(page)

    def _draw_standard_page(self, page: BasePage) -> None:
        """
        Render a standard page (Page or BasePage).

        Args:
            page: Page object to render.
        """
        image, draw = self._create_display_image()

        y: int = self.TOP_BAR_HEIGHT
        x: int = self.PADDING_HORIZONTAL
        content_width: int = self._get_page_content_width()

        # Draw title
        draw.text(
            (x, y),
            page.title,
            font=self.font,
            fill=self.FG_COLOR
        )
        y += self.FONT_SIZE + self.TITLE_SPACING

        # Load and position image
        page_image: Optional[Image.Image] = None
        if isinstance(page, Page) and page.image_path:
            page_image = page._load_image()
            
        if page_image:
            if page.image_position == "top":
                img_x: int = (self.disp.width - page_image.width) // 2
                image.paste(page_image, (img_x, y))
                y += page_image.height + self.IMAGE_SPACING
            elif page.image_position == "left":
                image.paste(page_image, (x, y))
                x += page_image.width + self.IMAGE_SPACING
                content_width -= (page_image.width + self.IMAGE_SPACING)
            elif page.image_position == "right":
                img_x = self.disp.width - page_image.width - self.PADDING_HORIZONTAL
                image.paste(page_image, (img_x, y))
                content_width -= (page_image.width + self.IMAGE_SPACING)

        # Draw wrapped text with scrolling
        lines: List[str] = page._wrap_text(
            page.text,
            self.body_font,
            content_width
        )
        line_height: int = self.BODY_FONT_SIZE + self.BODY_LINE_SPACING
        start_line: int = self.scroll_offset
        
        for i, line in enumerate(lines[start_line:]):
            if y + self.BODY_FONT_SIZE > self.disp.height - self.PAGE_BOTTOM_MARGIN:
                break  # Stop if we run out of space
            draw.text((x, y), line, font=self.body_font, fill=self.FG_COLOR)
            y += line_height

        self._display_image(image)

    def _draw_pokemon_page(self, page: PokemonDescriptionPage) -> None:
        """
        Render a Pokemon description page with image, info box, and description.

        Args:
            page: PokemonDescriptionPage object to render.
        """
        image, draw = self._create_display_image()

        # Draw page title
        draw.text(
            (self.PADDING_HORIZONTAL, 0),
            "Description",
            font=self.font,
            fill=self.FG_COLOR
        )

        y: int = self.TOP_BAR_HEIGHT
        x: int = self.PADDING_HORIZONTAL
        
        # Load Pokemon image (left side)
        pokemon_image: Optional[Image.Image] = page._load_image()
        image_width: int = self.POKEMON_IMAGE_SIZE
        
        if pokemon_image:
            image.paste(pokemon_image, (x, y))
        
        # Info box (right side)
        info_x: int = x + image_width + self.IMAGE_SPACING
        info_y: int = y
        info_width: int = self.disp.width - info_x - self.PADDING_HORIZONTAL
        
        # Draw info box background
        box_height: int = 100
        draw.rectangle(
            [(info_x, info_y), (info_x + info_width, info_y + box_height)],
            outline=self.FG_COLOR,
            width=1
        )
        
        # Info content with tighter spacing
        info_text_x: int = info_x + 3
        info_text_y: int = info_y + 3
        small_font: ImageFont.FreeTypeFont = self.body_font
        line_height: int = self.BODY_FONT_SIZE + 1
        
        # Dex number
        dex_text: str = f"#{page.dex_number:03d}"
        draw.text((info_text_x, info_text_y), dex_text, font=small_font, fill=self.FG_COLOR)
        info_text_y += line_height
        
        # Pokemon name
        draw.text((info_text_x, info_text_y), page.name, font=small_font, fill=self.FG_COLOR)
        info_text_y += line_height + 2
        
        # Types with background colors in 2-column grid
        type_y: int = info_text_y
        type_x: int = info_text_x
        type_height: int = self.BODY_FONT_SIZE + 2
        types_per_row: int = 2
        max_type_width: int = (info_width - 6) // 2  # Divide available width by 2
        
        for idx, (type_name, type_color) in enumerate(page.types):
            # Calculate position in grid
            col: int = idx % types_per_row
            row: int = idx // types_per_row
            
            # Position for this type badge
            current_type_x: int = info_text_x + (col * (max_type_width + 3))
            current_type_y: int = type_y + (row * (type_height + 2))
            
            # Draw type badge
            bbox = small_font.getbbox(type_name)
            type_width: int = min((bbox[2] - bbox[0]) + 6, max_type_width)
            
            draw.rectangle(
                [(current_type_x, current_type_y), (current_type_x + type_width, current_type_y + type_height)],
                fill=type_color
            )
            draw.text(
                (current_type_x + 3, current_type_y + 1),
                type_name,
                font=small_font,
                fill=(255, 255, 255)
            )
        
        # Calculate total rows needed for types
        num_rows: int = (len(page.types) + types_per_row - 1) // types_per_row
        info_text_y += (num_rows * (type_height + 2)) + 2
        
        # Height and Weight
        draw.text((info_text_x, info_text_y), f"Height: {page.height}", font=small_font, fill=self.FG_COLOR)
        info_text_y += line_height
        draw.text((info_text_x, info_text_y), f"Weight: {page.weight}", font=small_font, fill=self.FG_COLOR)
        
        # Description text (scrollable) below the image/info box
        desc_y: int = y + box_height + self.IMAGE_SPACING
        desc_x: int = self.PADDING_HORIZONTAL
        content_width: int = self._get_page_content_width()
        
        lines: List[str] = page._wrap_text(
            page.description,
            self.body_font,
            content_width
        )
        desc_line_height: int = self.BODY_FONT_SIZE + self.BODY_LINE_SPACING
        start_line: int = self.scroll_offset
        
        for i, line in enumerate(lines[start_line:]):
            if desc_y + self.BODY_FONT_SIZE > self.disp.height - self.PAGE_BOTTOM_MARGIN:
                break
            draw.text((desc_x, desc_y), line, font=self.body_font, fill=self.FG_COLOR)
            desc_y += desc_line_height

        self._display_image(image)

    def _scroll_page_up(self) -> None:
        """Scroll page content up (show earlier lines)."""
        if self.scroll_offset > 0:
            self.scroll_offset -= 1

    def _scroll_page_down(self) -> None:
        """Scroll page content down (show later lines)."""
        if self.current_page:
            # Calculate total lines
            content_width: int = self._get_page_content_width()
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

    # Sample Pokemon description pages
    bulbasaur_page = PokemonDescriptionPage(
        name="Bulbasaur",
        dex_number=1,
        types=[("Grass", (120, 200, 80)), ("Poison", (160, 64, 160)), ("Bitch", (90, 100, 200))],
        height="0.7m",
        weight="6.9kg",
        description="Bulbasaur can be seen napping in bright sunlight. There is a seed on its back. By soaking up the sun's rays, the seed grows progressively larger.",
        image_path="image.png",  # Set to actual bulbasaur image path
    )

    # Sample standard Pokemon pages (old style)
    pikachu_page = Page(
        title="Pikachu",
        text="Pikachu is an Electric-type Pokemon. When several of "
             "these Pokemon gather, their electricity can build and "
             "cause lightning storms. It has small electric sacs on "
             "both its cheeks. If threatened, it looses electric charges "
             "from the sacs.",
        image_path='image.png',  # Set to actual image path like "images/pikachu.jpg"
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
            ("Bulbasaur", bulbasaur_page),
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
        title="About",
        text=open("about.txt").read(),
        image_path='icon.jpg',
        image_position="top"
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