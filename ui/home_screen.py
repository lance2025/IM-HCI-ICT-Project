"""
home_screen.py — Main dashboard using CustomTkinter.
Sidebar with mini calendar + action buttons, main area with event cards.
"""

import customtkinter as ctk
import calendar
from datetime import datetime, date
from ui.components import COLORS, get_font, EventCard, StyledButton, get_game_logo_ctk
from backend.auth import Session
from backend.events import get_active_events, get_archived_events, get_events_for_month, delete_event
from backend.archive import run_auto_archive


class HomeScreen(ctk.CTkFrame):
    """Main dashboard with sidebar and event list."""

    def __init__(self, parent, on_logout=None):
        super().__init__(parent, fg_color=COLORS['bg_dark'])
        self.parent = parent
        self.on_logout = on_logout
        self.session = Session.get_instance()
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.selected_date = None

        self._build_ui()
        self._refresh_events()

    def _build_ui(self):
        """Build the dashboard layout."""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ─── SIDEBAR ─────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0,
                                     fg_color=COLORS['bg_dark'])
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(16, 0), pady=16)
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Add Event button (admin only)
        if self.session.is_admin:
            self.add_btn = ctk.CTkButton(
                self.sidebar, text="＋  Add Game Event",
                height=48, corner_radius=24,
                font=get_font(14, bold=True),
                fg_color=COLORS['accent'],
                hover_color=COLORS['accent_hover'],
                text_color=COLORS['bg_dark'],
                command=self._open_add_event
            )
            self.add_btn.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        # Mini Calendar
        self.calendar_frame = ctk.CTkFrame(self.sidebar, corner_radius=16,
                                            fg_color=COLORS['bg_medium'],
                                            border_width=1,
                                            border_color=COLORS['border'])
        self.calendar_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        self.calendar_frame.grid_columnconfigure(0, weight=1)
        self._build_calendar()

        # Quick stats
        self.stats_frame = ctk.CTkFrame(self.sidebar, corner_radius=16,
                                         fg_color=COLORS['bg_medium'],
                                         border_width=1,
                                         border_color=COLORS['border'])
        self.stats_frame.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        self._build_stats()

        # User info + Logout at bottom
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.grid(row=3, column=0, sticky="sew", pady=(8, 0))
        self.sidebar.grid_rowconfigure(3, weight=1)

        role_badge = "👑 Admin" if self.session.is_admin else "👤 User"
        user_label = ctk.CTkLabel(user_frame,
                                   text=f"{role_badge}  •  {self.session.username}",
                                   font=get_font(11),
                                   text_color=COLORS['text_secondary'])
        user_label.pack(anchor="w", pady=(0, 8))

        logout_btn = ctk.CTkButton(user_frame, text="Logout",
                                    height=32, corner_radius=16,
                                    font=get_font(11),
                                    fg_color=COLORS['border'],
                                    hover_color=COLORS['text_muted'],
                                    text_color=COLORS['text_primary'],
                                    width=80,
                                    command=self._logout)
        logout_btn.pack(anchor="w")

        # ─── MAIN CONTENT ────────────────────────────────────────
        self.main_frame = ctk.CTkFrame(self, corner_radius=24,
                                        fg_color=COLORS['bg_medium'])
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Top bar: Search + filter
        top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        top_bar.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(top_bar, placeholder_text="🔍  Search events...",
                                          height=42, corner_radius=21,
                                          font=get_font(13),
                                          fg_color=COLORS['bg_input'],
                                          border_width=0,
                                          text_color=COLORS['text_primary'])
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.search_entry.bind("<Return>", lambda e: self._refresh_events())
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_type())

        refresh_btn = ctk.CTkButton(top_bar, text="↻", width=42, height=42,
                                     corner_radius=21,
                                     font=get_font(16),
                                     fg_color=COLORS['bg_input'],
                                     hover_color=COLORS['border'],
                                     text_color=COLORS['accent'],
                                     command=self._refresh_events)
        refresh_btn.grid(row=0, column=1)

        # Tabs: Ongoing / Past Events
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=16,
                                       fg_color=COLORS['bg_dark'],
                                       segmented_button_fg_color=COLORS['bg_input'],
                                       segmented_button_selected_color=COLORS['accent'],
                                       segmented_button_selected_hover_color=COLORS['accent_hover'],
                                       segmented_button_unselected_color=COLORS['bg_input'],
                                       segmented_button_unselected_hover_color=COLORS['border'],
                                       text_color=COLORS['bg_dark'],
                                       text_color_disabled=COLORS['text_muted'])
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))

        self.tab_ongoing = self.tabview.add("⚡ Ongoing")
        self.tab_archive = self.tabview.add("📁 Past Events")
        self.tabview.set("⚡ Ongoing")

        # Ongoing events scroll area
        self.ongoing_scroll = ctk.CTkScrollableFrame(self.tab_ongoing,
                                                      fg_color="transparent",
                                                      corner_radius=0)
        self.ongoing_scroll.pack(fill="both", expand=True)
        self.ongoing_scroll.grid_columnconfigure(0, weight=1)

        # Archive events scroll area
        self.archive_scroll = ctk.CTkScrollableFrame(self.tab_archive,
                                                      fg_color="transparent",
                                                      corner_radius=0)
        self.archive_scroll.pack(fill="both", expand=True)
        self.archive_scroll.grid_columnconfigure(0, weight=1)

    def _build_calendar(self):
        """Build the mini calendar widget."""
        # Clear previous
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        # Header with navigation
        header = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 8))

        prev_btn = ctk.CTkButton(header, text="◀", width=28, height=28,
                                  corner_radius=8, font=get_font(11),
                                  fg_color="transparent",
                                  hover_color=COLORS['border'],
                                  text_color=COLORS['text_secondary'],
                                  command=self._prev_month)
        prev_btn.pack(side="left")

        month_name = f"{calendar.month_name[self.current_month]} {self.current_year}"
        month_label = ctk.CTkLabel(header, text=month_name,
                                    font=get_font(12, bold=True),
                                    text_color=COLORS['accent'])
        month_label.pack(side="left", expand=True)

        next_btn = ctk.CTkButton(header, text="▶", width=28, height=28,
                                  corner_radius=8, font=get_font(11),
                                  fg_color="transparent",
                                  hover_color=COLORS['border'],
                                  text_color=COLORS['text_secondary'],
                                  command=self._next_month)
        next_btn.pack(side="right")

        # Day names
        days_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
        days_frame.pack(fill="x", padx=12)

        for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            ctk.CTkLabel(days_frame, text=day, width=32,
                          font=get_font(10),
                          text_color=COLORS['text_muted']).pack(side="left", expand=True)

        # Get event dates for this month
        event_dates = get_events_for_month(self.current_year, self.current_month)
        event_day_set = set()
        for d in event_dates:
            try:
                event_day_set.add(int(d.split('-')[2]))
            except (IndexError, ValueError):
                pass

        # Day grid
        today = date.today()
        cal = calendar.monthcalendar(self.current_year, self.current_month)

        grid_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=8, pady=(4, 12))

        for week in cal:
            week_frame = ctk.CTkFrame(grid_frame, fg_color="transparent", height=32)
            week_frame.pack(fill="x")

            for day_num in week:
                if day_num == 0:
                    # Empty cell
                    ctk.CTkLabel(week_frame, text="", width=32, height=30).pack(side="left", expand=True)
                else:
                    is_today = (day_num == today.day and
                                self.current_month == today.month and
                                self.current_year == today.year)
                    has_event = day_num in event_day_set
                    is_selected = (self.selected_date == 
                                   f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}")

                    # Determine styling
                    if is_selected:
                        fg = COLORS['bg_dark']
                        bg = COLORS['accent']
                        border_color = COLORS['accent']
                        border_width = 2
                    elif is_today:
                        fg = COLORS['accent']
                        bg = COLORS['accent_dark']
                        border_color = COLORS['accent']
                        border_width = 2
                    elif has_event:
                        fg = COLORS['text_primary']
                        bg = "transparent"
                        border_color = None
                        border_width = 0
                    else:
                        fg = COLORS['text_secondary']
                        bg = "transparent"
                        border_color = None
                        border_width = 0

                    # Wrap each day in a small frame for button + dot
                    day_cell = ctk.CTkFrame(week_frame, fg_color="transparent", width=34, height=38)
                    day_cell.pack(side="left", expand=True, padx=1, pady=1)
                    day_cell.pack_propagate(False)

                    day_btn = ctk.CTkButton(
                        day_cell, text=str(day_num), width=32, height=26,
                        corner_radius=8, font=get_font(10, bold=is_today or has_event or is_selected),
                        fg_color=bg,
                        hover_color=COLORS['border'],
                        text_color=fg,
                        border_width=border_width,
                        border_color=border_color if border_color else COLORS['border'],
                        command=lambda d=day_num: self._select_date(d)
                    )
                    day_btn.pack(side="top")

                    # Event dot indicator
                    if has_event and not is_today:
                        dot = ctk.CTkLabel(
                            day_cell, text="●", font=get_font(6),
                            text_color=COLORS['accent'], height=8
                        )
                        dot.pack(side="top")

    def _build_stats(self):
        """Build quick stats panel."""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        active = get_active_events()
        archived = get_archived_events()

        upcoming_count = sum(1 for e in active if e.get('status') == 'Upcoming')
        ongoing_count = sum(1 for e in active if e.get('status') == 'Ongoing')
        finished_count = sum(1 for e in active if e.get('status') == 'Finished')

        stats_title = ctk.CTkLabel(self.stats_frame, text="Quick Stats",
                                    font=get_font(11, bold=True),
                                    text_color=COLORS['text_secondary'])
        stats_title.pack(anchor="w", padx=16, pady=(12, 8))

        stats_data = [
            ("Upcoming", upcoming_count, COLORS['status_upcoming']),
            ("Ongoing", ongoing_count, COLORS['status_ongoing']),
            ("Recently Finished", finished_count, COLORS['status_finished']),
            ("Archived", len(archived), COLORS['text_muted']),
        ]

        for label, count, color in stats_data:
            row = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(row, text=label, font=get_font(11),
                          text_color=COLORS['text_secondary']).pack(side="left")
            ctk.CTkLabel(row, text=str(count), font=get_font(11, bold=True),
                          text_color=color).pack(side="right")

        # Padding at bottom
        ctk.CTkLabel(self.stats_frame, text="", height=8).pack()

    def _refresh_events(self):
        """Refresh the event lists."""
        # Run auto-archive
        try:
            run_auto_archive()
        except Exception:
            pass

        search = self.search_entry.get().strip() if hasattr(self, 'search_entry') else None
        if not search:
            search = None

        # Date filter from calendar selection
        date_filter = getattr(self, 'selected_date', None)

        # Clear ongoing scroll
        for widget in self.ongoing_scroll.winfo_children():
            widget.destroy()

        # Clear archive scroll
        for widget in self.archive_scroll.winfo_children():
            widget.destroy()

        # Load ongoing events
        active = get_active_events(search_query=search, date_filter=date_filter)

        # Show date filter indicator
        if date_filter:
            self._show_date_filter_bar(date_filter)

        row_offset = 1 if date_filter else 0
        if active:
            for i, event in enumerate(active):
                card = EventCard(self.ongoing_scroll, event,
                                 on_click=self._on_event_click)
                card.grid(row=i + row_offset, column=0, sticky="ew", pady=(0, 8), padx=4)
        else:
            empty_msg = "No events on this date" if date_filter else "No current ongoing events"
            empty_sub = "Try selecting a different day or clear the filter." if date_filter else "Events will appear here once the admin creates them."
            empty_frame = ctk.CTkFrame(self.ongoing_scroll, fg_color="transparent")
            empty_frame.grid(row=row_offset, column=0, sticky="nsew", pady=60)
            ctk.CTkLabel(empty_frame, text="📭", font=get_font(40)).pack()
            ctk.CTkLabel(empty_frame, text=empty_msg, font=get_font(16, bold=True),
                          text_color=COLORS['text_secondary']).pack(pady=(8, 4))
            ctk.CTkLabel(empty_frame, text=empty_sub, font=get_font(12),
                          text_color=COLORS['text_muted']).pack()

        # Load archived events
        archived = get_archived_events(search_query=search, date_filter=date_filter)
        if archived:
            for i, event in enumerate(archived):
                card = EventCard(self.archive_scroll, event,
                                 on_click=self._on_event_click)
                card.grid(row=i, column=0, sticky="ew", pady=(0, 8), padx=4)
        else:
            self._show_empty_state(self.archive_scroll,
                                   "No archived events",
                                   "Past events that are more than a week old will appear here.")

        # Refresh stats and calendar
        self._build_stats()
        self._build_calendar()

    def _show_empty_state(self, parent, title, subtitle):
        """Show an empty placeholder state."""
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", pady=60)

        icon = ctk.CTkLabel(container, text="📭",
                             font=get_font(48))
        icon.pack(pady=(0, 16))

        title_label = ctk.CTkLabel(container, text=title,
                                    font=get_font(16, bold=True),
                                    text_color=COLORS['text_secondary'])
        title_label.pack(pady=(0, 8))

        sub_label = ctk.CTkLabel(container, text=subtitle,
                                  font=get_font(12),
                                  text_color=COLORS['text_muted'])
        sub_label.pack()

    def _on_search_type(self):
        """Debounced search on key release."""
        # Simple refresh on each keystroke (could debounce if slow)
        if hasattr(self, '_search_after_id'):
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(400, self._refresh_events)

    def _on_event_click(self, event_data):
        """Handle clicking on an event card — show detail popup."""
        self._show_event_detail(event_data)

    def _show_event_detail(self, event_data):
        """Show event detail in a popup."""
        popup = ctk.CTkToplevel(self)
        popup.title(event_data.get('event_name', 'Event Details'))
        popup.geometry("500x550")
        popup.configure(fg_color=COLORS['bg_dark'])
        popup.transient(self.winfo_toplevel())
        popup.grab_set()

        scroll = ctk.CTkScrollableFrame(popup, fg_color=COLORS['bg_dark'])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        game_name = event_data.get('game_name', 'Unknown')
        event_name = event_data.get('event_name', '')

        # Logo + title row
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 16))

        logo = get_game_logo_ctk(game_name, size=56)
        ctk.CTkLabel(header, image=logo, text="").pack(side="left", padx=(0, 12))

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(title_frame, text=event_name,
                      font=get_font(18, bold=True),
                      text_color=COLORS['text_primary']).pack(anchor="w")
        ctk.CTkLabel(title_frame, text=game_name,
                      font=get_font(12),
                      text_color=COLORS['accent']).pack(anchor="w")

        # Divider
        ctk.CTkFrame(scroll, height=1, fg_color=COLORS['border']).pack(fill="x", pady=12)

        # Details
        details = [
            ("Status", event_data.get('status', '')),
            ("Date", event_data.get('event_date', '')),
            ("Time", f"{event_data.get('start_time', '')} – {event_data.get('end_time', '')}" if event_data.get('end_time') else event_data.get('start_time', '')),
            ("Timezone", event_data.get('source_timezone', '')),
            ("Theme", event_data.get('event_theme', '')),
            ("Description", event_data.get('description', '')),
            ("Location", event_data.get('venue', '') or event_data.get('online_platform', '')),
            ("Link", event_data.get('online_link', '')),
            ("Region", event_data.get('region', '')),
            ("Prize Pool", event_data.get('prize_pool', '')),
            ("Entry Fee", f"{event_data.get('entry_fee_type', 'free')}" + (f" — {event_data.get('entry_fee_amount', '')}" if event_data.get('entry_fee_amount') else '')),
            ("Max Participants", str(event_data.get('max_participants', 0)) if event_data.get('max_participants', 0) > 0 else ''),
            ("Availability", event_data.get('availability', '')),
            ("Recurring", event_data.get('recurring', 'none')),
        ]

        for label, value in details:
            if value and value not in ('', '0', 'none', 'free'):
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(row, text=f"{label}:", font=get_font(11, bold=True),
                              text_color=COLORS['text_secondary'], width=120,
                              anchor="w").pack(side="left")
                ctk.CTkLabel(row, text=str(value), font=get_font(11),
                              text_color=COLORS['text_primary'],
                              anchor="w", wraplength=300).pack(side="left", fill="x", expand=True)

        # Admin actions
        if self.session.is_admin:
            ctk.CTkFrame(scroll, height=1, fg_color=COLORS['border']).pack(fill="x", pady=16)

            btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_frame.pack(fill="x")

            edit_btn = ctk.CTkButton(btn_frame, text="✏️ Edit Event",
                                      height=36, corner_radius=18,
                                      font=get_font(12),
                                      fg_color=COLORS['accent_dark'],
                                      hover_color=COLORS['accent'],
                                      text_color=COLORS['accent'],
                                      command=lambda: self._edit_event(event_data, popup))
            edit_btn.pack(side="left")

            delete_btn = ctk.CTkButton(btn_frame, text="🗑️ Delete Event",
                                        height=36, corner_radius=18,
                                        font=get_font(12),
                                        fg_color=COLORS['error'],
                                        hover_color="#cc3333",
                                        text_color="#ffffff",
                                        command=lambda: self._delete_event(event_data, popup))
            delete_btn.pack(side="right")

    def _edit_event(self, event_data, popup):
        """Open the edit event window pre-filled with existing data."""
        popup.destroy()
        try:
            from ui.add_event_window import AddEventWindow
            AddEventWindow(self.winfo_toplevel(),
                           on_event_added=self._refresh_events,
                           edit_data=event_data)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error Opening Edit", f"{type(e).__name__}: {e}")

    def _delete_event(self, event_data, popup):
        """Delete an event after confirmation."""
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Delete",
                               f"Delete '{event_data.get('event_name')}'?\nThis cannot be undone."):
            delete_event(event_data['event_id'])
            popup.destroy()
            self._refresh_events()

    def _open_add_event(self):
        """Open the Add Game Event window."""
        try:
            from ui.add_event_window import AddEventWindow
            AddEventWindow(self.winfo_toplevel(), on_event_added=self._refresh_events)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error Opening Add Event", f"{type(e).__name__}: {e}")

    def _prev_month(self):
        """Navigate to previous month."""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._build_calendar()

    def _next_month(self):
        """Navigate to next month."""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._build_calendar()

    def _select_date(self, day):
        """Handle clicking a date on the calendar."""
        self.selected_date = f"{self.current_year:04d}-{self.current_month:02d}-{day:02d}"
        self._refresh_events()

    def _clear_date_filter(self):
        """Clear date filter and show all events."""
        self.selected_date = None
        if hasattr(self, 'search_entry'):
            self.search_entry.delete(0, "end")
        self._refresh_events()

    def _show_date_filter_bar(self, date_str):
        """Show a small indicator above events showing which date is filtered."""
        filter_frame = ctk.CTkFrame(self.ongoing_scroll, fg_color=COLORS['accent_dark'],
                                     corner_radius=10, height=32)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8), padx=4)
        ctk.CTkLabel(filter_frame, text=f"📅 Showing events for: {date_str}",
                      font=get_font(11), text_color=COLORS['accent']).pack(
            side="left", padx=12, pady=4)
        ctk.CTkButton(filter_frame, text="✕ Clear", width=60, height=24,
                       corner_radius=8, font=get_font(10),
                       fg_color="transparent", hover_color=COLORS['border'],
                       text_color=COLORS['text_secondary'],
                       command=self._clear_date_filter).pack(side="right", padx=8, pady=4)

    def _logout(self):
        """Log out and return to login screen."""
        session = Session.get_instance()
        session.logout()
        if self.on_logout:
            self.on_logout()
