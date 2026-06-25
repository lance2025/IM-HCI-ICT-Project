# 🎮 Game Event Calendar — Desktop Edition

A desktop application for organizing and tracking game events, built with Python and CustomTkinter.

---

## Requirements

- **Python 3.9+**
- **customtkinter** — modern UI framework
- **Pillow** — image handling for game logos

## Installation

```bash
cd "D:\IM PROJECT\game-event-desktop"
pip install -r requirements.txt
```

## Running the App

```bash
python main.py
```

---

## Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| User | *(sign up from login screen)* | *(your choice)* |

- **Admin** can create game events, add new games, and manage all events.
- **Users** can view ongoing and past events.

---

## Game Logo Images

Place logo images in the `game_logos/` folder. The app matches filenames **exactly** (case-sensitive, spaces included) to the game name in the database.

### Naming Format

```
game_logos/{Game Name}.png
game_logos/{Game Name}.jpg
game_logos/{Game Name}.jpeg
```

The app checks for `.png` first, then `.jpg`, then `.jpeg`.

### Pre-seeded Games and Expected Filenames

| Game | Expected filename |
|------|-------------------|
| Minecraft | `Minecraft.png` |
| Valorant | `Valorant.png` |
| League of Legends | `League of Legends.png` |
| Genshin Impact | `Genshin Impact.png` |
| Roblox | `Roblox.png` |
| Tekken | `Tekken.png` |
| Counter-Strike 2 | `Counter-Strike 2.png` |
| Dota 2 | `Dota 2.png` |
| Fortnite | `Fortnite.png` |
| Apex Legends | `Apex Legends.png` |
| PUBG | `PUBG.png` |
| Overwatch 2 | `Overwatch 2.png` |
| Rocket League | `Rocket League.png` |
| Street Fighter 6 | `Street Fighter 6.png` |

> **Note:** If a logo file is not found, a placeholder icon is displayed instead. You can add logos at any time — the app picks them up automatically.

### Adding Logos for New Games

When the admin adds a new game (e.g., "Elden Ring"), simply place a file named `Elden Ring.png` (or `.jpg`/`.jpeg`) in the `game_logos/` folder. The logo will appear on event cards and in the creation form.

---

## Project Structure

```
game-event-desktop/
├── main.py                 ← Entry point (launches the app)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── gameevents_desktop.db   ← SQLite database (auto-created on first run)
├── game_logos/             ← Drop game logo images here
│   └── README.txt
├── backend/
│   ├── __init__.py
│   ├── database.py         ← SQLite connection, table creation, seeding
│   ├── auth.py             ← Login, signup, session management
│   ├── events.py           ← Event CRUD operations
│   ├── games.py            ← Game CRUD + logo path lookup
│   └── archive.py          ← Auto-archiving logic
└── ui/
    ├── __init__.py
    ├── components.py       ← Reusable widgets (EventCard, colors, fonts)
    ├── login_screen.py     ← Login + signup screen
    ├── home_screen.py      ← Dashboard (sidebar, calendar, event list)
    └── add_event_window.py ← "Add Game Event" modal (admin only)
```

---

## Features

- **Role-based access** — Admin creates events, users view them
- **Dark theme** with lime green accents (matching the original web app)
- **Mini calendar** with dot indicators for days with events
- **Auto-archiving** — events older than 7 days are automatically archived
- **Game logos** — auto-loaded from the `game_logos/` folder
- **Event creation** with collapsible "More Details" section for optional fields
- **Search and filter** events
- **Ongoing / Past Events** tabs

---

## Database

The SQLite database (`gameevents_desktop.db`) is created automatically on first run. To reset the app, simply delete this file and restart — it will be re-created with fresh data.
