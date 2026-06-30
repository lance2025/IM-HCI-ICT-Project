"""
game_selector.py — Custom game dropdown with hover-to-reveal edit (✏️) icons.
Replaces CTkComboBox for game selection in the Add Event form.
"""

import os
import shutil
import customtkinter as ctk
from tkinter import messagebox, filedialog
from ui.components import COLORS, get_font, get_game_logo_ctk, LOGOS_DIR
from backend.games import get_all_games, add_game, update_game, delete_game


class GameSelectorWidget(ctk.CTkFrame):
    """
    A custom dropdown for selecting games.
    Each item in the dropdown shows a game name + a pencil icon on hover.
    Clicking the pencil opens an edit popup (rename, change logo, delete).
    """

    def __init__(self, parent, games, game_var, on_game_selected=None,
                 on_game_added=None, on_game_edited=None, on_game_deleted=None):
        super().__init__(parent, fg_color="transparent")
        self.games = games
        self.game_var = game_var
        self.on_game_selected = on_game_selected
        self.on_game_added = on_game_added
        self.on_game_edited = on_game_edited
        self.on_game_deleted = on_game_deleted
        self.dropdown_open = False
        self.dropdown_window = None

        self.grid_columnconfigure(0, weight=1)
        self._build_selector()

    def _build_selector(self):
        """Build the selector entry + dropdown button."""
        self.selector_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_input'],
                                            corner_radius=12, border_width=1,
                                            border_color=COLORS['border'], height=38)
        self.selector_frame.grid(row=0, column=0, sticky="ew")
        self.selector_frame.grid_columnconfigure(0, weight=1)
        self.selector_frame.grid_propagate(False)

        # Display label showing selected game
        self.display_label = ctk.CTkLabel(self.selector_frame, text="Select a game...",
                                           font=get_font(12),
                                           text_color=COLORS['text_muted'],
                                           anchor="w")
        self.display_label.grid(row=0, column=0, sticky="ew", padx=(12, 0), pady=4)

        # Dropdown toggle button
        self.toggle_btn = ctk.CTkButton(self.selector_frame, text="▾", width=38, height=32,
                                         corner_radius=8, font=get_font(14),
                                         fg_color="transparent",
                                         hover_color=COLORS['border'],
                                         text_color=COLORS['accent'],
                                         command=self._toggle_dropdown)
        self.toggle_btn.grid(row=0, column=1, padx=(0, 4), pady=3)

        # Make the whole selector clickable
        self.display_label.bind("<Button-1>", lambda e: self._toggle_dropdown())
        self.selector_frame.bind("<Button-1>", lambda e: self._toggle_dropdown())

    def _toggle_dropdown(self):
        """Open or close the dropdown."""
        if self.dropdown_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self):
        """Open the custom dropdown below the selector."""
        if self.dropdown_open:
            return
        self.dropdown_open = True
        self.toggle_btn.configure(text="▴")

        # Create a toplevel dropdown
        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.configure(fg_color=COLORS['bg_medium'])
        self.dropdown_window.attributes("-topmost", True)

        # Position below the selector
        x = self.selector_frame.winfo_rootx()
        y = self.selector_frame.winfo_rooty() + self.selector_frame.winfo_height() + 2
        width = self.selector_frame.winfo_width()

        # Calculate height based on number of games (max 250px)
        item_h = 40
        total_h = min(len(self.games) * item_h + 50, 300)  # +50 for the "New" button
        self.dropdown_window.geometry(f"{width}x{total_h}+{x}+{y}")

        # Scrollable list of games
        self.game_list_frame = ctk.CTkScrollableFrame(
            self.dropdown_window, fg_color=COLORS['bg_medium'],
            corner_radius=0, scrollbar_button_color=COLORS['border'],
            scrollbar_button_hover_color=COLORS['accent_dark']
        )
        self.game_list_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.game_list_frame.grid_columnconfigure(0, weight=1)

        self._populate_game_rows()

        # "+ New Game" button at the bottom
        new_btn = ctk.CTkButton(self.dropdown_window, text="＋  New Game",
                                 height=36, corner_radius=0,
                                 font=get_font(11, bold=True),
                                 fg_color=COLORS['accent_dark'],
                                 hover_color=COLORS['accent'],
                                 text_color=COLORS['accent'],
                                 anchor="w",
                                 command=self._add_new_game)
        new_btn.pack(fill="x", side="bottom", padx=2, pady=2)

        # Close dropdown when clicking outside
        self.dropdown_window.bind("<FocusOut>", self._on_focus_out)
        self.dropdown_window.focus_set()

    def _populate_game_rows(self):
        """Build the game rows inside the dropdown."""
        for widget in self.game_list_frame.winfo_children():
            widget.destroy()

        for i, game in enumerate(self.games):
            self._create_game_row(i, game)

    def _create_game_row(self, index, game):
        """Create a single game row with hover-to-reveal edit icon."""
        game_name = game['game_name']
        game_id = game['game_id']

        row_frame = ctk.CTkFrame(self.game_list_frame, fg_color="transparent",
                                  height=38, corner_radius=8)
        row_frame.grid(row=index, column=0, sticky="ew", pady=1, padx=2)
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_propagate(False)

        # Game name label (clickable to select)
        name_label = ctk.CTkLabel(row_frame, text=game_name,
                                   font=get_font(12), text_color=COLORS['text_primary'],
                                   anchor="w")
        name_label.grid(row=0, column=0, sticky="ew", padx=(10, 0), pady=4)

        # Edit button (hidden by default, shown on hover)
        edit_btn = ctk.CTkButton(row_frame, text="✎", width=34, height=28,
                                  corner_radius=6, font=get_font(14, bold=True),
                                  fg_color=COLORS['border'],
                                  hover_color=COLORS['accent_dark'],
                                  text_color=COLORS['accent'],
                                  command=lambda gid=game_id, gn=game_name: self._open_edit_game(gid, gn))
        edit_btn.grid(row=0, column=1, padx=(0, 6), pady=4)
        edit_btn.grid_remove()  # Hidden by default

        # Hover effects
        def on_enter(e, frame=row_frame, btn=edit_btn):
            frame.configure(fg_color=COLORS['accent_dark'])
            btn.grid()  # Show edit button

        def on_leave(e, frame=row_frame, btn=edit_btn):
            frame.configure(fg_color="transparent")
            btn.grid_remove()  # Hide edit button

        # Bind hover to the row frame and all its children
        for widget in [row_frame, name_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        edit_btn.bind("<Enter>", on_enter)
        edit_btn.bind("<Leave>", on_leave)

        # Clicking the name selects the game
        def select_game(e, gn=game_name):
            self.game_var.set(gn)
            self.display_label.configure(text=gn, text_color=COLORS['text_primary'])
            self._close_dropdown()
            if self.on_game_selected:
                self.on_game_selected(gn)

        name_label.bind("<Button-1>", select_game)
        row_frame.bind("<Button-1>", select_game)

    def _close_dropdown(self):
        """Close the dropdown."""
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None
        self.dropdown_open = False
        self.toggle_btn.configure(text="▾")

    def _on_focus_out(self, event):
        """Close dropdown when focus leaves."""
        if self.dropdown_window:
            # Small delay to allow button clicks to register
            self.dropdown_window.after(150, self._check_focus)

    def _check_focus(self):
        """Check if focus is still within the dropdown."""
        if self.dropdown_window:
            try:
                focused = self.dropdown_window.focus_get()
                if focused is None or not str(focused).startswith(str(self.dropdown_window)):
                    self._close_dropdown()
            except Exception:
                self._close_dropdown()

    def _add_new_game(self):
        """Popup to add a new game with optional logo."""
        self._close_dropdown()

        popup = ctk.CTkToplevel(self)
        popup.title("Add New Game")
        popup.geometry("400x250")
        popup.configure(fg_color=COLORS['bg_dark'])
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        popup.attributes("-topmost", True)

        ctk.CTkLabel(popup, text="Game Name:", font=get_font(12),
                      text_color=COLORS['text_secondary']).pack(anchor="w", padx=24, pady=(20, 4))
        name_entry = ctk.CTkEntry(popup, placeholder_text="e.g., Elden Ring",
                                   height=38, corner_radius=12, font=get_font(12),
                                   fg_color=COLORS['bg_input'],
                                   border_color=COLORS['border'], border_width=1,
                                   text_color=COLORS['text_primary'])
        name_entry.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(popup, text="Logo (optional):", font=get_font(12),
                      text_color=COLORS['text_secondary']).pack(anchor="w", padx=24, pady=(4, 4))

        logo_path_var = ctk.StringVar(value="")
        logo_frame = ctk.CTkFrame(popup, fg_color="transparent")
        logo_frame.pack(fill="x", padx=24, pady=(0, 16))

        logo_label = ctk.CTkLabel(logo_frame, text="No file selected",
                                   font=get_font(11), text_color=COLORS['text_muted'])
        logo_label.pack(side="left", expand=True, anchor="w")

        def pick_logo():
            path = filedialog.askopenfilename(
                title="Select Game Logo",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
            if path:
                logo_path_var.set(path)
                logo_label.configure(text=os.path.basename(path))

        ctk.CTkButton(logo_frame, text="📁 Browse", width=90, height=30,
                       corner_radius=10, font=get_font(11),
                       fg_color=COLORS['accent_dark'], hover_color=COLORS['accent'],
                       text_color=COLORS['accent'],
                       command=pick_logo).pack(side="right")

        def submit_game():
            game_name = name_entry.get().strip()
            if not game_name:
                messagebox.showwarning("Add Game", "Please enter a game name.")
                return
            success, msg = add_game(game_name)
            if success:
                # Copy logo if provided
                logo_src = logo_path_var.get()
                if logo_src:
                    ext = os.path.splitext(logo_src)[1]
                    os.makedirs(LOGOS_DIR, exist_ok=True)
                    dest = os.path.join(LOGOS_DIR, f"{game_name}{ext}")
                    try:
                        shutil.copy2(logo_src, dest)
                    except Exception:
                        pass
                # Refresh and select the new game
                self.games = get_all_games()
                self.game_var.set(game_name)
                self.display_label.configure(text=game_name, text_color=COLORS['text_primary'])
                if self.on_game_added:
                    self.on_game_added()
                if self.on_game_selected:
                    self.on_game_selected(game_name)
                popup.destroy()
            else:
                messagebox.showwarning("Add Game", msg)

        ctk.CTkButton(popup, text="Add Game", height=40, corner_radius=20,
                       font=get_font(13, bold=True),
                       fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
                       text_color=COLORS['bg_dark'],
                       command=submit_game).pack(fill="x", padx=24, pady=(0, 20))

    def _open_edit_game(self, game_id, game_name):
        """Open edit popup for a specific game (rename, change logo, delete)."""
        self._close_dropdown()

        popup = ctk.CTkToplevel(self)
        popup.title(f"Edit Game — {game_name}")
        popup.geometry("420x340")
        popup.configure(fg_color=COLORS['bg_dark'])
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        popup.attributes("-topmost", True)

        # Title
        ctk.CTkLabel(popup, text=f"✏️  Edit Game", font=get_font(16, bold=True),
                      text_color=COLORS['accent']).pack(anchor="w", padx=24, pady=(20, 16))

        # Rename section
        ctk.CTkLabel(popup, text="Game Name:", font=get_font(12),
                      text_color=COLORS['text_secondary']).pack(anchor="w", padx=24, pady=(0, 4))
        name_entry = ctk.CTkEntry(popup, height=38, corner_radius=12, font=get_font(12),
                                   fg_color=COLORS['bg_input'],
                                   border_color=COLORS['border'], border_width=1,
                                   text_color=COLORS['text_primary'])
        name_entry.pack(fill="x", padx=24, pady=(0, 12))
        name_entry.insert(0, game_name)

        # Logo section
        ctk.CTkLabel(popup, text="Game Logo:", font=get_font(12),
                      text_color=COLORS['text_secondary']).pack(anchor="w", padx=24, pady=(4, 4))

        logo_frame = ctk.CTkFrame(popup, fg_color="transparent")
        logo_frame.pack(fill="x", padx=24, pady=(0, 16))

        from backend.games import get_game_logo_path as _get_logo
        current_logo = _get_logo(game_name)
        logo_status = os.path.basename(current_logo) if current_logo else "No logo"

        logo_path_var = ctk.StringVar(value="")
        logo_label = ctk.CTkLabel(logo_frame, text=logo_status,
                                   font=get_font(11), text_color=COLORS['text_muted'])
        logo_label.pack(side="left", expand=True, anchor="w")

        def pick_new_logo():
            path = filedialog.askopenfilename(
                title="Select New Logo",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.webp")])
            if path:
                logo_path_var.set(path)
                logo_label.configure(text=f"New: {os.path.basename(path)}")

        ctk.CTkButton(logo_frame, text="📁 Change Logo", width=120, height=30,
                       corner_radius=10, font=get_font(11),
                       fg_color=COLORS['accent_dark'], hover_color=COLORS['accent'],
                       text_color=COLORS['accent'],
                       command=pick_new_logo).pack(side="right")

        # Button row
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 20))
        btn_frame.grid_columnconfigure(0, weight=1)

        def save_changes():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Edit Game", "Game name cannot be empty.")
                return

            # Rename if name changed
            if new_name != game_name:
                success, msg = update_game(game_id, new_name)
                if not success:
                    messagebox.showwarning("Edit Game", msg)
                    return

            # Update logo if new one selected
            logo_src = logo_path_var.get()
            if logo_src:
                # Remove old logos
                final_name = new_name if new_name != game_name else game_name
                for ext in ['.png', '.jpg', '.jpeg']:
                    old_path = os.path.join(LOGOS_DIR, f"{final_name}{ext}")
                    if os.path.isfile(old_path):
                        try:
                            os.remove(old_path)
                        except Exception:
                            pass
                # Copy new logo
                ext = os.path.splitext(logo_src)[1]
                os.makedirs(LOGOS_DIR, exist_ok=True)
                dest = os.path.join(LOGOS_DIR, f"{final_name}{ext}")
                try:
                    shutil.copy2(logo_src, dest)
                except Exception as e:
                    messagebox.showwarning("Edit Game", f"Could not copy logo: {e}")

            # Refresh
            self.games = get_all_games()
            # Update selection if the currently selected game was renamed
            if self.game_var.get() == game_name and new_name != game_name:
                self.game_var.set(new_name)
                self.display_label.configure(text=new_name)
            if self.on_game_edited:
                self.on_game_edited()
            if self.on_game_selected:
                self.on_game_selected(self.game_var.get())
            popup.destroy()

        def delete_this_game():
            confirm = messagebox.askyesno(
                "Delete Game",
                f"Are you sure you want to delete '{game_name}'?\n\n"
                "This cannot be undone. Games with existing events cannot be deleted.")
            if not confirm:
                return
            success, msg = delete_game(game_id)
            if success:
                # Remove logo file
                for ext in ['.png', '.jpg', '.jpeg']:
                    logo_path = os.path.join(LOGOS_DIR, f"{game_name}{ext}")
                    if os.path.isfile(logo_path):
                        try:
                            os.remove(logo_path)
                        except Exception:
                            pass
                # Clear selection if this game was selected
                if self.game_var.get() == game_name:
                    self.game_var.set("")
                    self.display_label.configure(text="Select a game...",
                                                 text_color=COLORS['text_muted'])
                # Refresh
                self.games = get_all_games()
                if self.on_game_deleted:
                    self.on_game_deleted()
                popup.destroy()
            else:
                messagebox.showwarning("Delete Game", msg)

        # Save button
        ctk.CTkButton(btn_frame, text="Save Changes", height=40, corner_radius=20,
                       font=get_font(13, bold=True),
                       fg_color=COLORS['accent'], hover_color=COLORS['accent_hover'],
                       text_color=COLORS['bg_dark'],
                       command=save_changes).pack(side="left", expand=True, fill="x", padx=(0, 8))

        # Delete button
        ctk.CTkButton(btn_frame, text="🗑 Delete", height=40, corner_radius=20, width=100,
                       font=get_font(12, bold=True),
                       fg_color=COLORS['error'], hover_color="#cc3333",
                       text_color=COLORS['text_primary'],
                       command=delete_this_game).pack(side="right")

    def refresh_games(self, games):
        """Refresh the game list (called after add/edit/delete)."""
        self.games = games

    def set_game(self, game_name):
        """Programmatically set the selected game (for edit mode pre-fill)."""
        if game_name:
            self.game_var.set(game_name)
            self.display_label.configure(text=game_name, text_color=COLORS['text_primary'])
        else:
            self.game_var.set("")
            self.display_label.configure(text="Select a game...", text_color=COLORS['text_muted'])
