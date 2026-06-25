"""
add_event_window.py — "Add Game Event" dialog using CustomTkinter.
All location fields are under the collapsible "More Details" section.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from ui.components import COLORS, get_font, get_game_logo_ctk
from backend.games import get_all_games, add_game
from backend.events import create_event
from backend.auth import Session, get_all_timezones


class AddEventWindow(ctk.CTkToplevel):
    """Popup window for adding or editing a game event."""

    def __init__(self, parent, on_event_added=None, edit_data=None):
        super().__init__(parent)
        self.parent = parent
        self.on_event_added = on_event_added
        self.edit_data = edit_data
        self.is_edit_mode = edit_data is not None
        self.more_details_visible = False

        self.title("Edit Game Event" if self.is_edit_mode else "Add Game Event")
        self.geometry("620x700")
        self.minsize(580, 650)
        self.configure(fg_color=COLORS['bg_dark'])

        # Make it modal
        self.transient(parent)
        self.grab_set()
        self.after(100, self.focus_force)

        self._build_ui()

        # Pre-fill fields if editing
        if self.is_edit_mode:
            self._populate_edit_data()

    def _build_ui(self):
        """Build the add event form."""
        # Scrollable container
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS['bg_dark'],
                                              corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # Title
        title_text = "✏️  Edit Game Event" if self.is_edit_mode else "＋  Add Game Event"
        ctk.CTkLabel(self.scroll, text=title_text,
                      font=get_font(20, bold=True),
                      text_color=COLORS['accent']).grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        # ─── ALWAYS VISIBLE FIELDS ───────────────────────────────────────

        # Event Name
        row = self._add_label(row, "Event Name *")
        self.event_name_entry = self._add_entry(row, "e.g., Minecraft Civ War #3")
        row += 1

        # Game Selection
        row = self._add_label(row, "Game *")

        game_row_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        game_row_frame.grid(row=row, column=0, sticky="ew", pady=(0, 4))
        game_row_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self.games = get_all_games()
        game_names = [g['game_name'] for g in self.games]

        self.game_var = ctk.StringVar(value="")
        self.game_combo = ctk.CTkComboBox(game_row_frame, values=game_names,
                                           variable=self.game_var,
                                           height=38, corner_radius=12,
                                           font=get_font(12),
                                           fg_color=COLORS['bg_input'],
                                           border_color=COLORS['border'],
                                           border_width=1,
                                           button_color=COLORS['accent_dark'],
                                           button_hover_color=COLORS['accent'],
                                           dropdown_fg_color=COLORS['bg_medium'],
                                           dropdown_hover_color=COLORS['accent_dark'],
                                           text_color=COLORS['text_primary'],
                                           command=self._on_game_selected)
        self.game_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.game_combo.set("")

        add_game_btn = ctk.CTkButton(game_row_frame, text="+ New", width=70,
                                      height=38, corner_radius=12,
                                      font=get_font(11),
                                      fg_color=COLORS['bg_input'],
                                      hover_color=COLORS['border'],
                                      text_color=COLORS['accent'],
                                      command=self._add_new_game)
        add_game_btn.grid(row=0, column=1)

        # Logo preview
        self.logo_frame = ctk.CTkFrame(self.scroll, fg_color="transparent", height=56)
        self.logo_frame.grid(row=row, column=0, sticky="w", pady=(0, 12))
        self.logo_label = ctk.CTkLabel(self.logo_frame, text="")
        self.logo_label.pack(side="left")
        row += 1

        # Event Type / Theme
        row = self._add_label(row, "Event Type / Theme")
        self.theme_entry = self._add_entry(row, "e.g., Tournament, Community Night, Speedrun")
        row += 1

        # Description
        row = self._add_label(row, "Description")
        self.description_text = ctk.CTkTextbox(self.scroll, height=80,
                                                corner_radius=12,
                                                font=get_font(12),
                                                fg_color=COLORS['bg_input'],
                                                border_color=COLORS['border'],
                                                border_width=1,
                                                text_color=COLORS['text_primary'])
        self.description_text.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # ─── EVENT START DATE (calendar picker) ───
        row = self._add_label(row, "Event Start Date *")
        date_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        date_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        self.date_display = ctk.CTkEntry(date_frame, placeholder_text="Click to pick date",
                                          height=38, corner_radius=12, width=160,
                                          font=get_font(12),
                                          fg_color=COLORS['bg_input'],
                                          border_color=COLORS['border'], border_width=1,
                                          text_color=COLORS['text_primary'],
                                          state="disabled")
        self.date_display.pack(side="left", padx=(0, 8))

        self.pick_date_btn = ctk.CTkButton(date_frame, text="📅 Pick Date",
                                            height=38, corner_radius=12,
                                            font=get_font(11),
                                            fg_color=COLORS['accent_dark'],
                                            hover_color=COLORS['accent'],
                                            text_color=COLORS['accent'],
                                            command=self._open_date_picker)
        self.pick_date_btn.pack(side="left")

        self.selected_date = ""

        # ─── EVENT END DATE (with "Within the day" checkbox) ───
        row = self._add_label(row, "Event End Date")
        end_date_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        end_date_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        self.within_day_var = ctk.StringVar(value="on")
        self.within_day_check = ctk.CTkCheckBox(end_date_frame, text="Within the day",
                                                  variable=self.within_day_var,
                                                  onvalue="on", offvalue="off",
                                                  font=get_font(11),
                                                  fg_color=COLORS['accent'],
                                                  hover_color=COLORS['accent_dark'],
                                                  text_color=COLORS['text_secondary'],
                                                  command=self._toggle_end_date)
        self.within_day_check.pack(side="left", padx=(0, 12))

        self.end_date_display = ctk.CTkEntry(end_date_frame, placeholder_text="Same as start",
                                              height=38, corner_radius=12, width=160,
                                              font=get_font(12),
                                              fg_color=COLORS['bg_input'],
                                              border_color=COLORS['border'], border_width=1,
                                              text_color=COLORS['text_primary'],
                                              state="disabled")
        self.end_date_display.pack(side="left", padx=(0, 8))

        self.pick_end_date_btn = ctk.CTkButton(end_date_frame, text="📅",
                                                height=38, width=38, corner_radius=12,
                                                font=get_font(11),
                                                fg_color=COLORS['accent_dark'],
                                                hover_color=COLORS['accent'],
                                                text_color=COLORS['accent'],
                                                state="disabled",
                                                command=self._open_end_date_picker)
        self.pick_end_date_btn.pack(side="left")

        self.selected_end_date = ""

        # ─── TIME PICKERS (dropdowns for hour/minute) ───
        time_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        time_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(0, 60, 5)]

        ctk.CTkLabel(time_frame, text="Start", font=get_font(11),
                      text_color=COLORS['text_secondary']).pack(side="left", padx=(0, 6))
        self.start_hour_var = ctk.StringVar(value="12")
        self.start_hour_combo = ctk.CTkComboBox(time_frame, values=hours,
                                                  variable=self.start_hour_var,
                                                  width=70, height=38, corner_radius=12,
                                                  font=get_font(12),
                                                  fg_color=COLORS['bg_input'],
                                                  border_color=COLORS['border'], border_width=1,
                                                  button_color=COLORS['accent_dark'],
                                                  dropdown_fg_color=COLORS['bg_card'])
        self.start_hour_combo.pack(side="left", padx=(0, 2))
        ctk.CTkLabel(time_frame, text=":", font=get_font(14, bold=True),
                      text_color=COLORS['text_secondary']).pack(side="left")
        self.start_min_var = ctk.StringVar(value="00")
        self.start_min_combo = ctk.CTkComboBox(time_frame, values=minutes,
                                                variable=self.start_min_var,
                                                width=70, height=38, corner_radius=12,
                                                font=get_font(12),
                                                fg_color=COLORS['bg_input'],
                                                border_color=COLORS['border'], border_width=1,
                                                button_color=COLORS['accent_dark'],
                                                dropdown_fg_color=COLORS['bg_card'])
        self.start_min_combo.pack(side="left", padx=(2, 20))

        ctk.CTkLabel(time_frame, text="End", font=get_font(11),
                      text_color=COLORS['text_secondary']).pack(side="left", padx=(0, 6))
        self.end_hour_var = ctk.StringVar(value="13")
        self.end_hour_combo = ctk.CTkComboBox(time_frame, values=hours,
                                               variable=self.end_hour_var,
                                               width=70, height=38, corner_radius=12,
                                               font=get_font(12),
                                               fg_color=COLORS['bg_input'],
                                               border_color=COLORS['border'], border_width=1,
                                               button_color=COLORS['accent_dark'],
                                               dropdown_fg_color=COLORS['bg_card'])
        self.end_hour_combo.pack(side="left", padx=(0, 2))
        ctk.CTkLabel(time_frame, text=":", font=get_font(14, bold=True),
                      text_color=COLORS['text_secondary']).pack(side="left")
        self.end_min_var = ctk.StringVar(value="00")
        self.end_min_combo = ctk.CTkComboBox(time_frame, values=minutes,
                                              variable=self.end_min_var,
                                              width=70, height=38, corner_radius=12,
                                              font=get_font(12),
                                              fg_color=COLORS['bg_input'],
                                              border_color=COLORS['border'], border_width=1,
                                              button_color=COLORS['accent_dark'],
                                              dropdown_fg_color=COLORS['bg_card'])
        self.end_min_combo.pack(side="left", padx=(2, 12))

        self.duration_label = ctk.CTkLabel(time_frame, text="",
                                            font=get_font(10),
                                            text_color=COLORS['text_muted'])
        self.duration_label.pack(side="left")

        # Auto-calculate duration when time changes
        for var in [self.start_hour_var, self.start_min_var, self.end_hour_var, self.end_min_var]:
            var.trace_add("write", lambda *_: self._calc_duration())

        # Timezone
        row = self._add_label(row, "Timezone")
        self.tz_var = ctk.StringVar(value="UTC")
        tz_combo = ctk.CTkComboBox(self.scroll, values=get_all_timezones(),
                                    variable=self.tz_var,
                                    height=38, corner_radius=12,
                                    font=get_font(12),
                                    fg_color=COLORS['bg_input'],
                                    border_color=COLORS['border'],
                                    border_width=1,
                                    button_color=COLORS['accent_dark'],
                                    button_hover_color=COLORS['accent'],
                                    dropdown_fg_color=COLORS['bg_medium'],
                                    dropdown_hover_color=COLORS['accent_dark'],
                                    text_color=COLORS['text_primary'])
        tz_combo.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        # Cancelled toggle (status is auto-detected, not manually set)
        self.status_var = ctk.StringVar(value="Upcoming")  # internal only, auto-set on submit
        cancel_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cancel_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        self.cancelled_var = ctk.StringVar(value="off")
        cancelled_switch = ctk.CTkSwitch(cancel_frame, text="Mark as Cancelled",
                                          variable=self.cancelled_var,
                                          onvalue="on", offvalue="off",
                                          font=get_font(11),
                                          text_color=COLORS['text_secondary'],
                                          fg_color=COLORS['border'],
                                          progress_color=COLORS['error'],
                                          button_color=COLORS['text_primary'],
                                          button_hover_color=COLORS['text_secondary'])
        cancelled_switch.pack(side="left")

        # Prize Pool
        row = self._add_label(row, "Prize Pool")
        self.prize_entry = self._add_entry(row, "e.g., $500, In-game items")
        row += 1

        # Entry Fee
        fee_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fee_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1

        ctk.CTkLabel(fee_frame, text="Entry Fee", font=get_font(11),
                      text_color=COLORS['text_secondary']).pack(side="left", padx=(0, 12))
        self.fee_type_var = ctk.StringVar(value="Free")
        fee_seg = ctk.CTkSegmentedButton(fee_frame, values=["Free", "Paid"],
                                          variable=self.fee_type_var,
                                          font=get_font(11),
                                          fg_color=COLORS['bg_input'],
                                          selected_color=COLORS['accent'],
                                          selected_hover_color=COLORS['accent_hover'],
                                          unselected_color=COLORS['bg_input'],
                                          unselected_hover_color=COLORS['border'],
                                          text_color=COLORS['bg_dark'],
                                          text_color_disabled=COLORS['text_muted'],
                                          command=self._toggle_fee_amount)
        fee_seg.pack(side="left")

        self.fee_amount_entry = ctk.CTkEntry(fee_frame, placeholder_text="Amount",
                                              height=34, corner_radius=12, width=120,
                                              font=get_font(11),
                                              fg_color=COLORS['bg_input'],
                                              border_color=COLORS['border'], border_width=1,
                                              text_color=COLORS['text_primary'])
        # Hidden initially
        self.fee_amount_entry.pack(side="left", padx=(12, 0))
        self.fee_amount_entry.pack_forget()

        # ─── MORE DETAILS (COLLAPSIBLE) ──────────────────────────────────

        # Toggle button
        self.more_btn = ctk.CTkButton(self.scroll, text="▶  More Details",
                                       height=36, corner_radius=12,
                                       font=get_font(12, bold=True),
                                       fg_color=COLORS['bg_input'],
                                       hover_color=COLORS['border'],
                                       text_color=COLORS['accent'],
                                       anchor="w",
                                       command=self._toggle_more_details)
        self.more_btn.grid(row=row, column=0, sticky="w", pady=(8, 8))
        row += 1

        # More details frame (hidden by default)
        self.more_frame = ctk.CTkFrame(self.scroll, fg_color=COLORS['bg_medium'],
                                        corner_radius=16, border_width=1,
                                        border_color=COLORS['border'])
        self.more_row = row
        row += 1

        self._build_more_details()

        # ─── SUBMIT BUTTON ───────────────────────────────────────────────

        submit_text = "Save Changes" if self.is_edit_mode else "Create Event"
        self.submit_btn = ctk.CTkButton(self.scroll, text=submit_text,
                                         height=48, corner_radius=24,
                                         font=get_font(15, bold=True),
                                         fg_color=COLORS['accent'],
                                         hover_color=COLORS['accent_hover'],
                                         text_color=COLORS['bg_dark'],
                                         command=self._submit_event)
        self.submit_btn.grid(row=row, column=0, sticky="ew", pady=(20, 10))
        row += 1

    def _build_more_details(self):
        """Build the collapsible more details section."""
        frame = self.more_frame
        frame.grid_columnconfigure(0, weight=1)

        pad_x = 16
        r = 0

        # Location Type
        ctk.CTkLabel(frame, text="Location Type", font=get_font(11),
                      text_color=COLORS['text_secondary']).grid(
            row=r, column=0, sticky="w", padx=pad_x, pady=(16, 4))
        r += 1

        self.location_type_var = ctk.StringVar(value="Online")
        loc_seg = ctk.CTkSegmentedButton(frame, values=["Online", "Physical"],
                                          variable=self.location_type_var,
                                          font=get_font(11),
                                          fg_color=COLORS['bg_input'],
                                          selected_color=COLORS['accent_dark'],
                                          selected_hover_color=COLORS['accent'],
                                          unselected_color=COLORS['bg_input'],
                                          unselected_hover_color=COLORS['border'],
                                          text_color=COLORS['accent'],
                                          text_color_disabled=COLORS['text_muted'],
                                          command=self._toggle_location)
        loc_seg.grid(row=r, column=0, sticky="w", padx=pad_x, pady=(0, 8))
        r += 1

        # Online fields
        self.online_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.online_frame.grid(row=r, column=0, sticky="ew", padx=pad_x, pady=(0, 8))
        self.online_frame.grid_columnconfigure(1, weight=1)
        self.online_row = r
        r += 1

        ctk.CTkLabel(self.online_frame, text="Platform", font=get_font(10),
                      text_color=COLORS['text_muted']).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.platform_var = ctk.StringVar(value="")
        platform_combo = ctk.CTkComboBox(self.online_frame,
                                          values=["Discord", "Twitch", "YouTube", "Custom"],
                                          variable=self.platform_var,
                                          height=34, corner_radius=10,
                                          font=get_font(11),
                                          fg_color=COLORS['bg_input'],
                                          border_color=COLORS['border'], border_width=1,
                                          button_color=COLORS['accent_dark'],
                                          button_hover_color=COLORS['accent'],
                                          dropdown_fg_color=COLORS['bg_medium'],
                                          dropdown_hover_color=COLORS['accent_dark'],
                                          text_color=COLORS['text_primary'])
        platform_combo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        ctk.CTkLabel(self.online_frame, text="Link", font=get_font(10),
                      text_color=COLORS['text_muted']).grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.online_link_entry = ctk.CTkEntry(self.online_frame,
                                               placeholder_text="https://discord.gg/...",
                                               height=34, corner_radius=10,
                                               font=get_font(11),
                                               fg_color=COLORS['bg_input'],
                                               border_color=COLORS['border'], border_width=1,
                                               text_color=COLORS['text_primary'])
        self.online_link_entry.grid(row=3, column=0, columnspan=2, sticky="ew")

        # Physical fields (hidden by default)
        self.physical_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.physical_row = r
        r += 1

        ctk.CTkLabel(self.physical_frame, text="Venue / Address", font=get_font(10),
                      text_color=COLORS['text_muted']).pack(anchor="w", pady=(0, 4))
        self.venue_entry = ctk.CTkEntry(self.physical_frame,
                                         placeholder_text="e.g., Convention Center, Room 3B",
                                         height=34, corner_radius=10,
                                         font=get_font(11),
                                         fg_color=COLORS['bg_input'],
                                         border_color=COLORS['border'], border_width=1,
                                         text_color=COLORS['text_primary'])
        self.venue_entry.pack(fill="x")

        # Region
        ctk.CTkLabel(frame, text="Region", font=get_font(11),
                      text_color=COLORS['text_secondary']).grid(
            row=r, column=0, sticky="w", padx=pad_x, pady=(12, 4))
        r += 1

        self.region_var = ctk.StringVar(value="")
        region_combo = ctk.CTkComboBox(frame, values=["", "NA", "EU", "SEA", "OCE", "SA", "MENA", "Global"],
                                        variable=self.region_var,
                                        height=34, corner_radius=10,
                                        font=get_font(11),
                                        fg_color=COLORS['bg_input'],
                                        border_color=COLORS['border'], border_width=1,
                                        button_color=COLORS['accent_dark'],
                                        button_hover_color=COLORS['accent'],
                                        dropdown_fg_color=COLORS['bg_medium'],
                                        dropdown_hover_color=COLORS['accent_dark'],
                                        text_color=COLORS['text_primary'])
        region_combo.grid(row=r, column=0, sticky="ew", padx=pad_x, pady=(0, 8))
        r += 1

        # Recurring
        ctk.CTkLabel(frame, text="Recurring", font=get_font(11),
                      text_color=COLORS['text_secondary']).grid(
            row=r, column=0, sticky="w", padx=pad_x, pady=(8, 4))
        r += 1

        self.recurring_var = ctk.StringVar(value="None")
        recurring_seg = ctk.CTkSegmentedButton(frame, values=["None", "Weekly", "Monthly", "Yearly"],
                                                variable=self.recurring_var,
                                                font=get_font(11),
                                                fg_color=COLORS['bg_input'],
                                                selected_color=COLORS['accent_dark'],
                                                selected_hover_color=COLORS['accent'],
                                                unselected_color=COLORS['bg_input'],
                                                unselected_hover_color=COLORS['border'],
                                                text_color=COLORS['accent'],
                                                text_color_disabled=COLORS['text_muted'])
        recurring_seg.grid(row=r, column=0, sticky="w", padx=pad_x, pady=(0, 8))
        r += 1

        # Max Participants
        ctk.CTkLabel(frame, text="Max Participants", font=get_font(11),
                      text_color=COLORS['text_secondary']).grid(
            row=r, column=0, sticky="w", padx=pad_x, pady=(8, 4))
        r += 1

        self.max_participants_entry = ctk.CTkEntry(frame, placeholder_text="0 = unlimited",
                                                    height=34, corner_radius=10,
                                                    font=get_font(11),
                                                    fg_color=COLORS['bg_input'],
                                                    border_color=COLORS['border'], border_width=1,
                                                    text_color=COLORS['text_primary'])
        self.max_participants_entry.grid(row=r, column=0, sticky="ew", padx=pad_x, pady=(0, 8))
        r += 1

        # Registration Link
        ctk.CTkLabel(frame, text="Registration / Sign-up Link", font=get_font(11),
                      text_color=COLORS['text_secondary']).grid(
            row=r, column=0, sticky="w", padx=pad_x, pady=(8, 4))
        r += 1

        self.registration_link_entry = ctk.CTkEntry(frame,
                                                     placeholder_text="https://forms.gle/...",
                                                     height=34, corner_radius=10,
                                                     font=get_font(11),
                                                     fg_color=COLORS['bg_input'],
                                                     border_color=COLORS['border'], border_width=1,
                                                     text_color=COLORS['text_primary'])
        self.registration_link_entry.grid(row=r, column=0, sticky="ew", padx=pad_x, pady=(0, 8))
        r += 1

        # Availability
        ctk.CTkLabel(frame, text="Availability", font=get_font(11),
                      text_color=COLORS['text_secondary']).grid(
            row=r, column=0, sticky="w", padx=pad_x, pady=(8, 4))
        r += 1

        self.availability_var = ctk.StringVar(value="Open")
        avail_seg = ctk.CTkSegmentedButton(frame, values=["Open", "Invite Only", "Members Only"],
                                            variable=self.availability_var,
                                            font=get_font(11),
                                            fg_color=COLORS['bg_input'],
                                            selected_color=COLORS['accent_dark'],
                                            selected_hover_color=COLORS['accent'],
                                            unselected_color=COLORS['bg_input'],
                                            unselected_hover_color=COLORS['border'],
                                            text_color=COLORS['accent'],
                                            text_color_disabled=COLORS['text_muted'])
        avail_seg.grid(row=r, column=0, sticky="w", padx=pad_x, pady=(0, 16))
        r += 1

    # ─── HELPER METHODS ──────────────────────────────────────────────────────

    def _add_label(self, row, text):
        """Add a field label and return next row."""
        ctk.CTkLabel(self.scroll, text=text, font=get_font(11, bold=True),
                      text_color=COLORS['text_secondary']).grid(
            row=row, column=0, sticky="w", pady=(0, 4))
        return row + 1

    def _add_entry(self, row, placeholder=""):
        """Add an entry field and return the widget."""
        entry = ctk.CTkEntry(self.scroll, placeholder_text=placeholder,
                              height=38, corner_radius=12,
                              font=get_font(12),
                              fg_color=COLORS['bg_input'],
                              border_color=COLORS['border'],
                              border_width=1,
                              text_color=COLORS['text_primary'])
        entry.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        return entry

    def _on_game_selected(self, choice):
        """Update logo preview when game is selected."""
        game_name = self.game_var.get()
        if game_name:
            logo = get_game_logo_ctk(game_name, size=48)
            self.logo_label.configure(image=logo, text="")
        else:
            self.logo_label.configure(image=None, text="")

    def _add_new_game(self):
        """Popup to add a new game."""
        dialog = ctk.CTkInputDialog(text="Enter new game name:",
                                     title="Add New Game",
                                     fg_color=COLORS['bg_dark'],
                                     button_fg_color=COLORS['accent'],
                                     button_hover_color=COLORS['accent_hover'],
                                     button_text_color=COLORS['bg_dark'])
        game_name = dialog.get_input()
        if game_name and game_name.strip():
            success, msg = add_game(game_name.strip())
            if success:
                # Refresh game list
                self.games = get_all_games()
                game_names = [g['game_name'] for g in self.games]
                self.game_combo.configure(values=game_names)
                self.game_combo.set(game_name.strip())
                self._on_game_selected(game_name.strip())
            else:
                messagebox.showwarning("Add Game", msg)

    def _calc_duration(self):
        """Calculate and display duration between start and end time."""
        try:
            s = datetime.strptime(f"{self.start_hour_var.get()}:{self.start_min_var.get()}", "%H:%M")
            e = datetime.strptime(f"{self.end_hour_var.get()}:{self.end_min_var.get()}", "%H:%M")
            diff = e - s
            if diff.total_seconds() > 0:
                hours = int(diff.total_seconds() // 3600)
                mins = int((diff.total_seconds() % 3600) // 60)
                if hours > 0 and mins > 0:
                    self.duration_label.configure(text=f"≈ {hours}h {mins}m")
                elif hours > 0:
                    self.duration_label.configure(text=f"≈ {hours}h")
                else:
                    self.duration_label.configure(text=f"≈ {mins}m")
            else:
                self.duration_label.configure(text="")
        except (ValueError, TypeError):
            self.duration_label.configure(text="")

    def _open_date_picker(self):
        """Open a calendar popup for start date selection."""
        self._show_calendar_popup(self._set_start_date)

    def _open_end_date_picker(self):
        """Open a calendar popup for end date selection."""
        self._show_calendar_popup(self._set_end_date)

    def _set_start_date(self, date_str):
        """Set the selected start date."""
        self.selected_date = date_str
        self.date_display.configure(state="normal")
        self.date_display.delete(0, "end")
        self.date_display.insert(0, date_str)
        self.date_display.configure(state="disabled")

    def _set_end_date(self, date_str):
        """Set the selected end date."""
        self.selected_end_date = date_str
        self.end_date_display.configure(state="normal")
        self.end_date_display.delete(0, "end")
        self.end_date_display.insert(0, date_str)
        self.end_date_display.configure(state="disabled")

    def _toggle_end_date(self):
        """Toggle end date field based on 'Within the day' checkbox."""
        if self.within_day_var.get() == "on":
            self.end_date_display.configure(state="normal")
            self.end_date_display.delete(0, "end")
            self.end_date_display.insert(0, "Same as start")
            self.end_date_display.configure(state="disabled")
            self.pick_end_date_btn.configure(state="disabled")
            self.selected_end_date = ""
        else:
            self.end_date_display.configure(state="normal")
            self.end_date_display.delete(0, "end")
            self.end_date_display.configure(state="disabled")
            self.pick_end_date_btn.configure(state="normal")

    def _show_calendar_popup(self, on_select):
        """Show a simple calendar date picker popup."""
        import calendar as cal_mod
        popup = ctk.CTkToplevel(self)
        popup.title("Pick a Date")
        popup.geometry("320x320")
        popup.configure(fg_color=COLORS['bg_dark'])
        popup.transient(self)
        popup.grab_set()

        today = datetime.today()
        year, month = today.year, today.month

        def render_month(y, m):
            for widget in cal_frame.winfo_children():
                widget.destroy()
            month_label.configure(text=f"{cal_mod.month_name[m]} {y}")
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            for c, d in enumerate(days):
                ctk.CTkLabel(cal_frame, text=d, font=get_font(9),
                              text_color=COLORS['text_muted'], width=38).grid(row=0, column=c)
            for r_idx, week in enumerate(cal_mod.monthcalendar(y, m), start=1):
                for c_idx, day in enumerate(week):
                    if day == 0:
                        ctk.CTkLabel(cal_frame, text="", width=38).grid(row=r_idx, column=c_idx)
                    else:
                        btn = ctk.CTkButton(cal_frame, text=str(day), width=38, height=32,
                                             corner_radius=8, font=get_font(10),
                                             fg_color="transparent",
                                             hover_color=COLORS['accent_dark'],
                                             text_color=COLORS['text_primary'],
                                             command=lambda d=day: pick(y, m, d))
                        btn.grid(row=r_idx, column=c_idx, padx=1, pady=1)

        def pick(y, m, d):
            on_select(f"{y:04d}-{m:02d}-{d:02d}")
            popup.destroy()

        def prev_month():
            nonlocal year, month
            month -= 1
            if month < 1:
                month = 12
                year -= 1
            render_month(year, month)

        def next_month():
            nonlocal year, month
            month += 1
            if month > 12:
                month = 1
                year += 1
            render_month(year, month)

        nav_frame = ctk.CTkFrame(popup, fg_color="transparent")
        nav_frame.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkButton(nav_frame, text="◀", width=32, fg_color="transparent",
                       hover_color=COLORS['border'], text_color=COLORS['accent'],
                       command=prev_month).pack(side="left")
        month_label = ctk.CTkLabel(nav_frame, text="", font=get_font(13, bold=True),
                                     text_color=COLORS['text_primary'])
        month_label.pack(side="left", expand=True)
        ctk.CTkButton(nav_frame, text="▶", width=32, fg_color="transparent",
                       hover_color=COLORS['border'], text_color=COLORS['accent'],
                       command=next_month).pack(side="right")

        cal_frame = ctk.CTkFrame(popup, fg_color="transparent")
        cal_frame.pack(fill="both", expand=True, padx=12, pady=8)
        render_month(year, month)

    def _toggle_more_details(self):
        """Show/hide the more details section."""
        self.more_details_visible = not self.more_details_visible
        if self.more_details_visible:
            self.more_btn.configure(text="▼  More Details")
            self.more_frame.grid(row=self.more_row, column=0, sticky="ew", pady=(0, 8))
        else:
            self.more_btn.configure(text="▶  More Details")
            self.more_frame.grid_forget()

    def _toggle_location(self, value):
        """Toggle between online and physical location fields."""
        if value == "Online":
            self.physical_frame.grid_forget()
            self.online_frame.grid(row=self.online_row, column=0, sticky="ew",
                                   padx=16, pady=(0, 8))
        else:
            self.online_frame.grid_forget()
            self.physical_frame.grid(row=self.physical_row, column=0, sticky="ew",
                                     padx=16, pady=(0, 8))

    def _toggle_fee_amount(self, value):
        """Show/hide fee amount field based on fee type."""
        if value == "Paid":
            self.fee_amount_entry.pack(side="left", padx=(12, 0))
        else:
            self.fee_amount_entry.pack_forget()

    def _populate_edit_data(self):
        """Pre-fill all fields with existing event data for editing."""
        d = self.edit_data

        # Event name
        self.event_name_entry.insert(0, d.get('event_name', ''))

        # Game
        game_name = d.get('game_name', '')
        if game_name:
            self.game_var.set(game_name)
            self._on_game_selected(game_name)

        # Theme
        self.theme_entry.insert(0, d.get('event_theme', ''))

        # Description
        self.description_text.insert("1.0", d.get('description', ''))

        # Start date
        start_date = d.get('event_date', '')
        if start_date:
            self.selected_date = start_date
            self.date_display.configure(state="normal")
            self.date_display.delete(0, "end")
            self.date_display.insert(0, start_date)
            self.date_display.configure(state="disabled")

        # End date
        end_date = d.get('end_date', '')
        if end_date and end_date != start_date:
            self.within_day_var.set("off")
            self._toggle_end_date()
            self.selected_end_date = end_date
            self.end_date_display.configure(state="normal")
            self.end_date_display.delete(0, "end")
            self.end_date_display.insert(0, end_date)
            self.end_date_display.configure(state="disabled")

        # Time
        start_time = d.get('start_time', '')
        if start_time and ':' in start_time:
            parts = start_time.split(':')
            self.start_hour_var.set(parts[0])
            self.start_min_var.set(parts[1])

        end_time = d.get('end_time', '')
        if end_time and ':' in end_time:
            parts = end_time.split(':')
            self.end_hour_var.set(parts[0])
            self.end_min_var.set(parts[1])

        # Timezone
        self.tz_var.set(d.get('source_timezone', 'UTC'))

        # Cancelled
        if d.get('status') == 'Cancelled':
            self.cancelled_var.set("on")

        # Prize pool
        self.prize_entry.insert(0, d.get('prize_pool', ''))

        # Entry fee
        fee_type = d.get('entry_fee_type', 'free')
        self.fee_type_var.set(fee_type.capitalize() if fee_type else "Free")
        if fee_type == 'paid':
            self._toggle_fee("Paid")
            self.fee_amount_entry.insert(0, d.get('entry_fee_amount', ''))

        # More details fields (location, region, etc.)
        loc_type = d.get('location_type', 'online')
        self.location_type_var.set(loc_type.capitalize() if loc_type else "Online")

        if loc_type == 'physical':
            self._toggle_location("Physical")
            self.venue_entry.insert(0, d.get('venue', ''))
        else:
            if d.get('online_platform'):
                self.platform_var.set(d.get('online_platform', 'Discord'))
            self.online_link_entry.insert(0, d.get('online_link', ''))

        self.region_var.set(d.get('region', ''))

        recurring = d.get('recurring', 'none')
        self.recurring_var.set(recurring.capitalize() if recurring else "None")

        max_p = d.get('max_participants', 0)
        if max_p and int(max_p) > 0:
            self.max_participants_entry.insert(0, str(max_p))

        self.registration_link_entry.insert(0, d.get('registration_link', ''))

        avail = d.get('availability', 'open')
        avail_map = {'open': 'Open', 'invite_only': 'Invite Only', 'members_only': 'Members Only'}
        self.availability_var.set(avail_map.get(avail, 'Open'))

    def _submit_event(self):
        """Validate and submit the new event."""
        event_name = self.event_name_entry.get().strip()
        game_name = self.game_var.get()
        event_date = self.selected_date

        # Validation
        if not event_name:
            messagebox.showwarning("Validation", "Event name is required.")
            return
        if not game_name:
            messagebox.showwarning("Validation", "Please select a game.")
            return
        if not event_date:
            messagebox.showwarning("Validation", "Please pick an event start date.")
            return

        # Find game_id
        game_id = None
        for g in self.games:
            if g['game_name'] == game_name:
                game_id = g['game_id']
                break
        if not game_id:
            messagebox.showwarning("Validation", "Selected game not found.")
            return

        # Auto-determine status based on date/time (considers end_date too)
        from datetime import date as date_cls
        try:
            ev_date = date_cls.fromisoformat(event_date)
            today = date_cls.today()

            # If end_date exists, use it to determine if event is still active
            end_date_raw = self.selected_end_date if self.within_day_var.get() == "off" else event_date
            ev_end = date_cls.fromisoformat(end_date_raw) if end_date_raw else ev_date

            if ev_end < today:
                status = "Finished"
            elif ev_date <= today <= ev_end:
                status = "Ongoing"
            else:
                status = "Upcoming"
        except (ValueError, TypeError):
            status = "Upcoming"

        if self.cancelled_var.get() == "on":
            status = "Cancelled"

        # Build event data
        session = Session.get_instance()

        start_time = f"{self.start_hour_var.get()}:{self.start_min_var.get()}"
        end_time = f"{self.end_hour_var.get()}:{self.end_min_var.get()}"
        end_date = self.selected_end_date if self.within_day_var.get() == "off" else event_date

        event_data = {
            'created_by': session.user_id,
            'game_id': game_id,
            'event_name': event_name,
            'event_theme': self.theme_entry.get().strip(),
            'description': self.description_text.get("1.0", "end-1c").strip(),
            'event_date': event_date,
            'end_date': end_date,
            'start_time': start_time,
            'end_time': end_time,
            'source_timezone': self.tz_var.get(),
            'location_type': self.location_type_var.get().lower(),
            'venue': self.venue_entry.get().strip() if self.location_type_var.get() == "Physical" else '',
            'online_platform': self.platform_var.get() if self.location_type_var.get() == "Online" else '',
            'online_link': self.online_link_entry.get().strip() if self.location_type_var.get() == "Online" else '',
            'region': self.region_var.get(),
            'status': status,
            'recurring': self.recurring_var.get().lower(),
            'max_participants': int(self.max_participants_entry.get() or 0),
            'registration_link': self.registration_link_entry.get().strip(),
            'availability': self.availability_var.get().lower().replace(" ", "_"),
            'prize_pool': self.prize_entry.get().strip(),
            'entry_fee_type': self.fee_type_var.get().lower(),
            'entry_fee_amount': self.fee_amount_entry.get().strip() if self.fee_type_var.get() == "Paid" else '',
        }

        # Submit
        try:
            if self.is_edit_mode:
                from backend.events import update_event
                success, msg = update_event(self.edit_data['event_id'], event_data)
            else:
                success, msg = create_event(event_data)

            if success:
                if self.on_event_added:
                    self.on_event_added()
                self.destroy()
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error", f"{type(e).__name__}: {e}")
