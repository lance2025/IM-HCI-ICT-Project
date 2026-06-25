"""
main.py — Entry point for Game Event Calendar Desktop App.
Launches the CustomTkinter application.
"""

import sys
import os

# Ensure the app directory is in the path for imports
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import customtkinter as ctk
from tkinter import ttk, messagebox

# Check for Pillow (required for logo handling)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from backend.database import initialize as init_db
from backend.archive import run_auto_archive
from ui.login_screen import LoginScreen
from ui.home_screen import HomeScreen
from ui.components import COLORS, clear_image_cache


class GameEventApp:
    """Main application controller."""

    def __init__(self):
        # Configure CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.root = ctk.CTk()
        self.root.title("Game Event Calendar")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(fg_color=COLORS['bg_dark'])

        # Ensure game_logos directory exists
        logos_dir = os.path.join(APP_DIR, "game_logos")
        os.makedirs(logos_dir, exist_ok=True)

        # Initialize database
        try:
            init_db()
        except Exception as e:
            messagebox.showerror("Database Error",
                                 f"Failed to initialize database:\n{e}")
            sys.exit(1)

        # Run auto-archive on startup
        try:
            run_auto_archive()
        except Exception:
            pass

        # Current screen reference
        self.current_screen = None

        # Show login screen
        self._show_login()

    def _show_login(self):
        """Display the login screen."""
        if self.current_screen:
            self.current_screen.destroy()
            clear_image_cache()

        self.current_screen = LoginScreen(
            self.root,
            on_login_success=self._show_home
        )
        self.current_screen.pack(fill="both", expand=True)

    def _show_home(self):
        """Display the home/dashboard screen."""
        if self.current_screen:
            self.current_screen.destroy()

        self.current_screen = HomeScreen(
            self.root,
            on_logout=self._show_login
        )
        self.current_screen.pack(fill="both", expand=True)

    def run(self):
        """Start the application main loop."""
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")

        print("=" * 50)
        print("  🎮 Game Event Calendar — Desktop Edition")
        print("  Starting application...")
        if not PIL_AVAILABLE:
            print("  ⚠️  Pillow not installed — logos will not display.")
            print("     Install with: pip install Pillow")
        print("=" * 50)

        self.root.mainloop()


def main():
    """Application entry point."""
    if not PIL_AVAILABLE:
        print("WARNING: Pillow (PIL) is not installed.")
        print("Game logos will not display. Install with: pip install Pillow")
        print()

    app = GameEventApp()
    app.run()


if __name__ == "__main__":
    main()
