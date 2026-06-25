"""
components.py — Reusable UI widgets and utilities using CustomTkinter.
Provides colors, fonts, EventCard, game logo loading, and helper functions.
"""

import os
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

# ─── COLOR SCHEME (matches the web app) ─────────────────────────────────────
COLORS = {
    'bg_dark': '#1a1a1a',
    'bg_medium': '#2b2b2b',
    'bg_card': '#2b2b2b',
    'bg_input': '#222222',
    'accent': '#a3ff1a',
    'accent_hover': '#b8ff4d',
    'accent_dark': '#445916',
    'text_primary': '#ffffff',
    'text_secondary': '#888888',
    'text_muted': '#555555',
    'border': '#333333',
    'error': '#ff4444',
    'success': '#a3ff1a',
    'login_bg': '#99ff00',
    'login_card': '#2a2a2a',
    'status_upcoming': '#3b82f6',
    'status_ongoing': '#a3ff1a',
    'status_finished': '#888888',
    'status_cancelled': '#ff4444',
}

# ─── FONT HELPER ─────────────────────────────────────────────────────────────
def get_font(size=13, bold=False):
    """Return a CTkFont tuple."""
    weight = "bold" if bold else "normal"
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)


# ─── LOGO DIRECTORY ──────────────────────────────────────────────────────────
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS_DIR = os.path.join(APP_DIR, "game_logos")

# Image cache to prevent garbage collection
_image_cache = {}


def clear_image_cache():
    """Clear the image cache."""
    global _image_cache
    _image_cache = {}


def create_placeholder_icon(size=48, text="?"):
    """Create a placeholder image for games without a logo."""
    img = Image.new('RGBA', (size, size), (43, 43, 43, 255))
    draw = ImageDraw.Draw(img)
    # Draw a rounded rectangle
    draw.rounded_rectangle([2, 2, size-2, size-2], radius=8,
                           fill=(68, 89, 22, 255), outline=(163, 255, 26, 200), width=2)
    # Draw text in center
    try:
        font = ImageFont.truetype("segoeui.ttf", size // 3)
    except (OSError, IOError):
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, (size - th) / 2 - 2), text, fill=(163, 255, 26, 255), font=font)
    return img


def load_game_logo(game_name, size=48):
    """Load a game logo from the game_logos folder, or return placeholder."""
    if game_name:
        os.makedirs(LOGOS_DIR, exist_ok=True)
        for ext in ['.png', '.jpg', '.jpeg']:
            path = os.path.join(LOGOS_DIR, f"{game_name}{ext}")
            if os.path.isfile(path):
                try:
                    img = Image.open(path).convert('RGBA')
                    img = img.resize((size, size), Image.LANCZOS)
                    return img
                except Exception:
                    pass

    # Return placeholder with first letter of game name
    letter = game_name[0].upper() if game_name else "?"
    return create_placeholder_icon(size, letter)


def get_game_logo_ctk(game_name, size=48):
    """Get a CTkImage for a game logo (handles hi-DPI)."""
    cache_key = f"{game_name}_{size}"
    if cache_key not in _image_cache:
        pil_img = load_game_logo(game_name, size)
        _image_cache[cache_key] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                                size=(size, size))
    return _image_cache[cache_key]


# Keep backward compat name
get_game_logo_tk = get_game_logo_ctk


def get_status_color(status):
    """Get accent color for event status."""
    status_colors = {
        'Upcoming': COLORS['status_upcoming'],
        'Ongoing': COLORS['status_ongoing'],
        'Finished': COLORS['status_finished'],
        'Cancelled': COLORS['status_cancelled'],
    }
    return status_colors.get(status, COLORS['text_muted'])


# ─── EVENT CARD WIDGET ───────────────────────────────────────────────────────

class EventCard(ctk.CTkFrame):
    """A modern event card displaying event info with game logo."""

    def __init__(self, parent, event_data, on_click=None, **kwargs):
        super().__init__(parent, corner_radius=16, fg_color=COLORS['bg_card'],
                         border_width=1, border_color=COLORS['border'], **kwargs)
        self.event_data = event_data
        self.on_click = on_click

        self._build()

        # Click binding
        if on_click:
            self.bind("<Button-1>", lambda e: on_click(event_data))
            self.configure(cursor="hand2")
            self._bind_click_recursive(self, lambda e: on_click(event_data))

    def _build(self):
        """Build the card layout."""
        self.grid_columnconfigure(1, weight=1)

        game_name = self.event_data.get('game_name', 'Unknown')
        event_name = self.event_data.get('event_name', 'Untitled Event')
        event_date = self.event_data.get('event_date', '')
        start_time = self.event_data.get('start_time', '')
        end_time = self.event_data.get('end_time', '')
        status = self.event_data.get('status', 'Upcoming')
        event_theme = self.event_data.get('event_theme', '')

        # Game logo
        logo = get_game_logo_ctk(game_name, size=48)
        logo_label = ctk.CTkLabel(self, image=logo, text="", width=48, height=48)
        logo_label.grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=16, sticky="n")

        # Event info column
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=(16, 4))
        info_frame.grid_columnconfigure(0, weight=1)

        # Event name
        name_label = ctk.CTkLabel(info_frame, text=event_name,
                                   font=get_font(14, bold=True),
                                   text_color=COLORS['text_primary'],
                                   anchor="w")
        name_label.grid(row=0, column=0, sticky="w")

        # Status badge
        status_color = get_status_color(status)
        badge = ctk.CTkLabel(info_frame, text=f" {status} ",
                              font=get_font(10, bold=True),
                              text_color=COLORS['bg_dark'] if status == 'Ongoing' else '#ffffff',
                              fg_color=status_color,
                              corner_radius=8, height=22)
        badge.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Subtitle row (game + theme)
        subtitle = game_name
        if event_theme:
            subtitle += f"  •  {event_theme}"
        sub_label = ctk.CTkLabel(info_frame, text=subtitle,
                                  font=get_font(11),
                                  text_color=COLORS['text_secondary'],
                                  anchor="w")
        sub_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # Bottom row (date + time)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=(0, 16))

        time_str = start_time
        if end_time:
            time_str += f" – {end_time}"
        date_str = f"📅 {event_date}"
        if time_str:
            date_str += f"   🕐 {time_str}"

        date_label = ctk.CTkLabel(bottom_frame, text=date_str,
                                   font=get_font(11),
                                   text_color=COLORS['text_muted'],
                                   anchor="w")
        date_label.pack(side="left")

        # Prize pool indicator
        prize = self.event_data.get('prize_pool', '')
        if prize:
            prize_label = ctk.CTkLabel(bottom_frame, text=f"🏆 {prize}",
                                        font=get_font(10),
                                        text_color=COLORS['accent'],
                                        anchor="e")
            prize_label.pack(side="right")

    def _bind_click_recursive(self, widget, callback):
        """Bind click event to a widget and all its children recursively."""
        try:
            widget.bind("<Button-1>", callback)
            widget.configure(cursor="hand2")
        except Exception:
            pass
        # After the widget is fully built, bind to all children
        self.after(50, lambda: self._bind_children(widget, callback))

    def _bind_children(self, widget, callback):
        """Bind click to all child widgets."""
        for child in widget.winfo_children():
            try:
                child.bind("<Button-1>", callback)
                child.configure(cursor="hand2")
            except Exception:
                pass
            self._bind_children(child, callback)


# ─── STYLED BUTTON (shortcut) ────────────────────────────────────────────────

class StyledButton(ctk.CTkButton):
    """A pre-styled button matching the app theme."""

    def __init__(self, parent, text="", command=None, accent=True, **kwargs):
        defaults = {
            'corner_radius': 25,
            'height': 42,
            'font': get_font(14, bold=True),
        }
        if accent:
            defaults['fg_color'] = COLORS['accent']
            defaults['hover_color'] = COLORS['accent_hover']
            defaults['text_color'] = COLORS['bg_dark']
        else:
            defaults['fg_color'] = COLORS['bg_medium']
            defaults['hover_color'] = COLORS['border']
            defaults['text_color'] = COLORS['text_primary']

        defaults.update(kwargs)
        super().__init__(parent, text=text, command=command, **defaults)
