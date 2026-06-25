"""
login_screen.py — Login/Signup screen using CustomTkinter.
Matches the web app's lime green background with centered dark card design.
"""

import customtkinter as ctk
from ui.components import COLORS, get_font, StyledButton
from backend.auth import authenticate, signup, Session, get_all_timezones


class LoginScreen(ctk.CTkFrame):
    """Login screen with lime background and centered card."""

    def __init__(self, parent, on_login_success=None):
        super().__init__(parent, fg_color=COLORS['login_bg'])
        self.parent = parent
        self.on_login_success = on_login_success
        self.mode = "login"  # "login" or "signup"

        self._build_ui()

    def _build_ui(self):
        """Build the login screen."""
        # Center the card
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(self, width=420, height=520, corner_radius=32,
                                  fg_color=COLORS['login_card'],
                                  border_width=0)
        self.card.grid(row=0, column=0)
        self.card.grid_propagate(False)
        self.card.grid_columnconfigure(0, weight=1)

        self._build_login_card()

    def _build_login_card(self):
        """Build login form inside the card."""
        # Clear card
        for widget in self.card.winfo_children():
            widget.destroy()

        self.card.configure(height=520 if self.mode == "login" else 600)

        row = 0

        # Avatar icon
        avatar_frame = ctk.CTkFrame(self.card, width=80, height=80, corner_radius=20,
                                     fg_color=COLORS['bg_dark'])
        avatar_frame.grid(row=row, column=0, pady=(36, 20))
        avatar_frame.grid_propagate(False)
        avatar_frame.grid_columnconfigure(0, weight=1)
        avatar_frame.grid_rowconfigure(0, weight=1)

        avatar_icon = ctk.CTkLabel(avatar_frame, text="🎮", font=get_font(32),
                                    text_color=COLORS['accent'])
        avatar_icon.grid(row=0, column=0)
        row += 1

        # Title
        if self.mode == "login":
            title_text = "Welcome Back"
            subtitle_text = "Log in to manage game events"
        else:
            title_text = "Create Account"
            subtitle_text = "Sign up to view game events"

        title = ctk.CTkLabel(self.card, text=title_text,
                              font=get_font(20, bold=True),
                              text_color=COLORS['text_primary'])
        title.grid(row=row, column=0, pady=(0, 4))
        row += 1

        subtitle = ctk.CTkLabel(self.card, text=subtitle_text,
                                 font=get_font(12),
                                 text_color=COLORS['text_secondary'])
        subtitle.grid(row=row, column=0, pady=(0, 24))
        row += 1

        # Form frame (to control padding)
        form = ctk.CTkFrame(self.card, fg_color="transparent")
        form.grid(row=row, column=0, padx=40, sticky="ew")
        form.grid_columnconfigure(0, weight=1)
        row += 1

        form_row = 0

        # Username
        self.username_entry = ctk.CTkEntry(form, placeholder_text="Username",
                                            height=44, corner_radius=22,
                                            font=get_font(13),
                                            fg_color=COLORS['bg_input'],
                                            border_color=COLORS['accent_dark'],
                                            border_width=2,
                                            text_color=COLORS['text_primary'])
        self.username_entry.grid(row=form_row, column=0, sticky="ew", pady=(0, 12))
        form_row += 1

        # Password
        self.password_entry = ctk.CTkEntry(form, placeholder_text="Password",
                                            show="•", height=44, corner_radius=22,
                                            font=get_font(13),
                                            fg_color=COLORS['bg_input'],
                                            border_color=COLORS['accent_dark'],
                                            border_width=2,
                                            text_color=COLORS['text_primary'])
        self.password_entry.grid(row=form_row, column=0, sticky="ew", pady=(0, 12))
        form_row += 1

        # Signup-only: Timezone selector
        if self.mode == "signup":
            self.timezone_var = ctk.StringVar(value="UTC")
            tz_combo = ctk.CTkComboBox(form, values=get_all_timezones(),
                                        variable=self.timezone_var,
                                        height=44, corner_radius=22,
                                        font=get_font(12),
                                        fg_color=COLORS['bg_input'],
                                        border_color=COLORS['accent_dark'],
                                        border_width=2,
                                        button_color=COLORS['accent_dark'],
                                        button_hover_color=COLORS['accent'],
                                        dropdown_fg_color=COLORS['bg_medium'],
                                        dropdown_hover_color=COLORS['accent_dark'],
                                        text_color=COLORS['text_primary'])
            tz_combo.grid(row=form_row, column=0, sticky="ew", pady=(0, 12))
            form_row += 1

        # Error message label
        self.error_label = ctk.CTkLabel(form, text="",
                                         font=get_font(11),
                                         text_color=COLORS['error'],
                                         anchor="w", height=20)
        self.error_label.grid(row=form_row, column=0, sticky="ew", pady=(0, 8))
        form_row += 1

        # Submit button
        btn_text = "LOG IN" if self.mode == "login" else "SIGN UP"
        submit_btn = ctk.CTkButton(form, text=btn_text, height=48,
                                    corner_radius=24,
                                    font=get_font(16, bold=True),
                                    fg_color=COLORS['bg_dark'],
                                    hover_color="#111111",
                                    text_color=COLORS['text_primary'],
                                    command=self._on_submit)
        submit_btn.grid(row=form_row, column=0, sticky="ew", pady=(8, 0))
        form_row += 1

        # Toggle link
        toggle_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        toggle_frame.grid(row=row, column=0, pady=(20, 24))
        row += 1

        if self.mode == "login":
            link_text = "Don't have an account?"
            link_action = "Sign up here"
        else:
            link_text = "Already have an account?"
            link_action = "Log in here"

        ctk.CTkLabel(toggle_frame, text=link_text,
                      font=get_font(11),
                      text_color=COLORS['text_secondary']).pack(side="left", padx=(0, 4))

        toggle_btn = ctk.CTkButton(toggle_frame, text=link_action,
                                    font=get_font(11, bold=True),
                                    text_color=COLORS['text_primary'],
                                    fg_color="transparent",
                                    hover_color=COLORS['accent_dark'],
                                    height=24, width=100,
                                    command=self._toggle_mode)
        toggle_btn.pack(side="left")

        # Bind Enter key
        self.username_entry.bind("<Return>", lambda e: self._on_submit())
        self.password_entry.bind("<Return>", lambda e: self._on_submit())

        # Focus username
        self.username_entry.focus()

    def _toggle_mode(self):
        """Switch between login and signup modes."""
        self.mode = "signup" if self.mode == "login" else "login"
        self._build_login_card()

    def _on_submit(self):
        """Handle form submission."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(text="Please fill in all fields.")
            return

        if self.mode == "login":
            self._do_login(username, password)
        else:
            self._do_signup(username, password)

    def _do_login(self, username, password):
        """Attempt login."""
        success, message, user_data = authenticate(username, password)

        if success:
            # Set session
            session = Session.get_instance()
            session.login(
                user_id=user_data['user_id'],
                username=user_data['username'],
                role=user_data['role'],
                user_timezone=user_data['user_timezone']
            )
            # Navigate to home
            if self.on_login_success:
                self.on_login_success()
        else:
            self.error_label.configure(text=message)

    def _do_signup(self, username, password):
        """Attempt signup."""
        timezone = self.timezone_var.get() if hasattr(self, 'timezone_var') else "UTC"
        success, message = signup(username, password, timezone)

        if success:
            self.error_label.configure(text="", text_color=COLORS['success'])
            # Switch to login mode with success message
            self.mode = "login"
            self._build_login_card()
            self.error_label.configure(text="Account created! You can now log in.",
                                        text_color=COLORS['success'])
        else:
            self.error_label.configure(text=message, text_color=COLORS['error'])
