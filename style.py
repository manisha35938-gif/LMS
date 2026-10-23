"""
style.py
---------
Central place for colors, fonts and ttk styling so every window in the
application looks consistent. Import COLORS / FONTS for raw values, or
call setup_style() once per Tk root to configure ttk widget styles.
"""

import tkinter as tk
from tkinter import ttk

COLORS = {
    "primary": "#1a5276",       # dark blue - sidebar / headers
    "primary_dark": "#123a54",
    "accent": "#2e86c1",        # buttons / highlights
    "success": "#1e8449",
    "danger": "#c0392b",
    "warning": "#b9770e",
    "background": "#f4f6f7",
    "surface": "#ffffff",
    "text": "#1c2833",
    "text_light": "#ffffff",
    "muted": "#7b7d7d",
    "border": "#d5d8dc",
}

FONTS = {
    "title": ("Segoe UI", 20, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "label": ("Segoe UI", 10),
    "label_bold": ("Segoe UI", 10, "bold"),
    "entry": ("Segoe UI", 10),
    "button": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "stat_number": ("Segoe UI", 22, "bold"),
    "stat_label": ("Segoe UI", 10),
}


def setup_style(root):
    """Configure ttk styles used throughout the app. Call once per root/Toplevel
    hierarchy (ttk styles are process-wide, but this keeps intent explicit)."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=COLORS["background"])

    style.configure("TFrame", background=COLORS["background"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("Sidebar.TFrame", background=COLORS["primary"])

    style.configure(
        "TLabel", background=COLORS["background"], foreground=COLORS["text"], font=FONTS["label"]
    )
    style.configure(
        "Surface.TLabel", background=COLORS["surface"], foreground=COLORS["text"], font=FONTS["label"]
    )
    style.configure(
        "Heading.TLabel",
        background=COLORS["background"],
        foreground=COLORS["primary"],
        font=FONTS["heading"],
    )
    style.configure(
        "Title.TLabel",
        background=COLORS["primary"],
        foreground=COLORS["text_light"],
        font=FONTS["title"],
    )

    style.configure("TEntry", font=FONTS["entry"], padding=4)
    style.configure("TCombobox", font=FONTS["entry"], padding=4)

    style.configure(
        "TButton",
        font=FONTS["button"],
        padding=6,
        background=COLORS["accent"],
        foreground=COLORS["text_light"],
    )
    style.map(
        "TButton",
        background=[("active", COLORS["primary_dark"])],
        foreground=[("active", COLORS["text_light"])],
    )

    style.configure("Success.TButton", background=COLORS["success"], foreground=COLORS["text_light"])
    style.map("Success.TButton", background=[("active", "#166a38")])

    style.configure("Danger.TButton", background=COLORS["danger"], foreground=COLORS["text_light"])
    style.map("Danger.TButton", background=[("active", "#96271d")])

    style.configure("Muted.TButton", background=COLORS["muted"], foreground=COLORS["text_light"])
    style.map("Muted.TButton", background=[("active", "#5f6161")])

    style.configure(
        "Treeview",
        font=FONTS["label"],
        rowheight=26,
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
    )
    style.configure(
        "Treeview.Heading",
        font=FONTS["label_bold"],
        background=COLORS["primary"],
        foreground=COLORS["text_light"],
    )
    style.map("Treeview", background=[("selected", COLORS["accent"])], foreground=[("selected", "white")])

    return style
