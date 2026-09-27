import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
import urllib.parse
import threading
import csv
import random
import re

from country_state_city import Country, State, City


class GoogleMapsScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Maps Scraper")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)

        self.stop_requested = False
        self.results = []

        # Location database / selection state
        self.countries = []
        self.country_map = {}
        self.states = []
        self.state_map = {}
        self.cities = []
        self.city_map = {}
        self.bulk_states = []
        self.bulk_cities = []
        self.bulk_keywords = []
        self.random_state_var = tk.BooleanVar(value=False)
        self.random_city_var = tk.BooleanVar(value=False)
        self.multi_scrape_active = False

        # ---------------------------------------------------
        # Dark theme palette
        # ---------------------------------------------------
        self.COLOR_BG = "#121317"
        self.COLOR_BG_CARD = "#1a1c22"
        self.COLOR_BG_ENTRY = "#22252c"
        self.COLOR_BORDER = "#2c2f38"
        self.COLOR_FG = "#e8e9ec"
        self.COLOR_FG_MUTED = "#8b8f99"
        self.COLOR_ACCENT = "#4f8cff"
        self.COLOR_ACCENT_HOVER = "#3f74d6"
        self.COLOR_ACCENT_ACTIVE = "#2f5cb0"
        self.COLOR_DANGER = "#e5484d"
        self.COLOR_DANGER_HOVER = "#c53d41"
        self.COLOR_ROW_ALT = "#1e2027"
        self.COLOR_SELECT = "#2a3a55"

        self.apply_dark_theme()
        self.create_widgets()

    # =========================================================
    # THEME
    # =========================================================

    def apply_dark_theme(self):
        bg = self.COLOR_BG
        bg_card = self.COLOR_BG_CARD
        bg_entry = self.COLOR_BG_ENTRY
        border = self.COLOR_BORDER
        fg = self.COLOR_FG
        fg_muted = self.COLOR_FG_MUTED
        accent = self.COLOR_ACCENT
        accent_hover = self.COLOR_ACCENT_HOVER
        accent_active = self.COLOR_ACCENT_ACTIVE
        danger = self.COLOR_DANGER
        danger_hover = self.COLOR_DANGER_HOVER
        select = self.COLOR_SELECT

        font_base = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 10, "bold")

        self.root.configure(bg=bg)

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=bg, foreground=fg, font=font_base)

        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=bg_card)

        style.configure("TLabel", background=bg, foreground=fg, font=font_base)
        style.configure("Muted.TLabel", background=bg, foreground=fg_muted)
        style.configure("Heading.TLabel", background=bg, foreground=fg, font=("Segoe UI", 22, "bold"))

        style.configure(
            "TLabelframe",
            background=bg_card,
            bordercolor=border,
            darkcolor=bg_card,
            lightcolor=bg_card,
            relief="solid",
            borderwidth=1
        )
        style.configure(
            "TLabelframe.Label",
            background=bg_card,
            foreground=accent,
            font=font_bold
        )

        # Buttons
        style.configure(
            "TButton",
            background=bg_entry,
            foreground=fg,
            borderwidth=0,
            focuscolor=bg,
            padding=(12, 8),
            font=font_bold
        )
        style.map(
            "TButton",
            background=[("active", border), ("disabled", bg_card)],
            foreground=[("disabled", fg_muted)]
        )

        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            borderwidth=0,
            focuscolor=bg,
            padding=(14, 9),
            font=font_bold
        )
        style.map(
            "Accent.TButton",
            background=[("active", accent_hover), ("pressed", accent_active), ("disabled", border)],
            foreground=[("disabled", fg_muted)]
        )

        style.configure(
            "Danger.TButton",
            background=bg_entry,
            foreground=danger,
            borderwidth=0,
            focuscolor=bg,
            padding=(14, 9),
            font=font_bold
        )
        style.map(
            "Danger.TButton",
            background=[("pressed", danger_hover), ("active", danger), ("disabled", bg_card)],
            foreground=[("active", "#ffffff"), ("disabled", fg_muted)]
        )

        # Entry / Combobox / Spinbox
        style.configure(
            "TEntry",
            fieldbackground=bg_entry,
            background=bg_entry,
            foreground=fg,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            insertcolor=fg,
            padding=6
        )
        style.map(
            "TEntry",
            bordercolor=[("focus", accent)],
            lightcolor=[("focus", accent)],
            darkcolor=[("focus", accent)]
        )

        style.configure(
            "TCombobox",
            fieldbackground=bg_entry,
            background=bg_entry,
            foreground=fg,
            arrowcolor=fg_muted,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            padding=6
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", bg_entry), ("disabled", bg_card)],
            foreground=[("disabled", fg_muted)],
            bordercolor=[("focus", accent)],
            arrowcolor=[("active", accent)]
        )

        style.configure(
            "TSpinbox",
            fieldbackground=bg_entry,
            background=bg_entry,
            foreground=fg,
            arrowcolor=fg_muted,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            padding=6
        )

        style.configure(
            "TCheckbutton",
            background=bg,
            foreground=fg,
            focuscolor=bg
        )
        style.map(
            "TCheckbutton",
            background=[("active", bg)],
            foreground=[("disabled", fg_muted)]
        )

        # Treeview (results table)
        style.configure(
            "Treeview",
            background=bg_entry,
            fieldbackground=bg_entry,
            foreground=fg,
            bordercolor=border,
            borderwidth=0,
            rowheight=26,
            font=font_base
        )
        style.map(
            "Treeview",
            background=[("selected", select)],
            foreground=[("selected", "#ffffff")]
        )
        style.configure(
            "Treeview.Heading",
            background=bg_card,
            foreground=fg,
            bordercolor=border,
            relief="flat",
            font=font_bold,
            padding=(8, 8)
        )
        style.map(
            "Treeview.Heading",
            background=[("active", border)]
        )

        # Scrollbars
        for orient in ("Vertical", "Horizontal"):
            style.configure(
                f"{orient}.TScrollbar",
                background=bg_card,
                troughcolor=bg,
                bordercolor=bg,
                arrowcolor=fg_muted,
                relief="flat"
            )
            style.map(
                f"{orient}.TScrollbar",
                background=[("active", border)]
            )

        # Combobox dropdown listbox colors (raw Tk, not ttk-themable)
        self.root.option_add("*TCombobox*Listbox.background", bg_entry)
        self.root.option_add("*TCombobox*Listbox.foreground", fg)
        self.root.option_add("*TCombobox*Listbox.selectBackground", accent)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.root.option_add("*TCombobox*Listbox.font", font_base)

    def create_widgets(self):
        header = ttk.Frame(self.root, padding=15)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Google Maps Scraper",
            style="Heading.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Search Google Maps and collect name, rating, reviews, phone, category, website, address and Maps URL",
            style="Muted.TLabel"
        ).pack(anchor="w", pady=(5, 0))

        search_frame = ttk.LabelFrame(
            self.root,
            text="Search",
            padding=15
        )
        search_frame.pack(fill="x", padx=15, pady=10)

        # Country
        ttk.Label(search_frame, text="Country:").grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.country_entry = ttk.Combobox(
            search_frame, width=25, state="readonly"
        )
        self.country_entry.grid(
            row=0, column=1, sticky="ew", pady=5
        )
        self.country_entry.bind("<<ComboboxSelected>>", self.on_country_selected)

        # State
        ttk.Label(search_frame, text="State / Province:").grid(
            row=0, column=2, padx=(20, 10), pady=5
        )
        self.state_entry = ttk.Combobox(
            search_frame, width=25, state="readonly"
        )
        self.state_entry.grid(
            row=0, column=3, sticky="ew", pady=5
        )
        self.state_entry.bind("<<ComboboxSelected>>", self.on_state_selected)

        # City
        ttk.Label(search_frame, text="City:").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.city_entry = ttk.Combobox(
            search_frame, width=25, state="readonly"
        )
        self.city_entry.grid(
            row=1, column=1, sticky="ew", pady=5
        )

        # Query
        ttk.Label(search_frame, text="What to Search:").grid(
            row=1, column=2, padx=(20, 10), pady=5
        )
        self.query_entry = ttk.Entry(search_frame, width=25)
        self.query_entry.grid(
            row=1, column=3, sticky="ew", pady=5
        )

        # Placeholder text (does not become the actual search query)
        self.query_placeholder = "Restaurants"
        self.query_entry.insert(0, self.query_placeholder)
        self.query_entry.config(foreground=self.COLOR_FG_MUTED)
        self.query_placeholder_active = True
        self.query_entry.bind("<FocusIn>", self.clear_query_placeholder)
        self.query_entry.bind("<FocusOut>", self.restore_query_placeholder)

        # Max results
        ttk.Label(search_frame, text="Max Results:").grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=5
        )
        self.max_results = ttk.Spinbox(
            search_frame, from_=1, to=1000, width=10
        )
        self.max_results.grid(
            row=2, column=1, sticky="w", pady=5
        )
        self.max_results.set(20)

        # Location options
        options_frame = ttk.Frame(search_frame)
        options_frame.grid(
            row=2, column=2, columnspan=2, sticky="w", padx=(20, 0), pady=5
        )

        ttk.Checkbutton(
            options_frame,
            text="Randomise State",
            variable=self.random_state_var
        ).pack(side="left", padx=(0, 12))

        ttk.Checkbutton(
            options_frame,
            text="Randomise City",
            variable=self.random_city_var
        ).pack(side="left")

        # Bulk location buttons
        bulk_frame = ttk.Frame(search_frame)
        bulk_frame.grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )

        ttk.Button(
            bulk_frame,
            text="Bulk States",
            command=self.open_bulk_states
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            bulk_frame,
            text="Bulk Cities",
            command=self.open_bulk_cities
        ).pack(side="left")

        ttk.Button(
            bulk_frame,
            text="Bulk Keywords",
            command=self.open_bulk_keywords
        ).pack(side="left", padx=(8, 0))

        self.location_summary = ttk.Label(
            bulk_frame,
            text="No bulk locations selected."
        )
        self.location_summary.pack(side="left", padx=12)

        search_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(3, weight=1)

        # Buttons
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(15, 0)
        )

        self.start_button = ttk.Button(
            button_frame,
            text="▶  Start Scraping",
            command=self.start_scraping,
            style="Accent.TButton"
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.stop_button = ttk.Button(
            button_frame,
            text="■  Stop",
            command=self.stop_scraping,
            state="disabled",
            style="Danger.TButton"
        )
        self.stop_button.pack(side="left")

        status_frame = ttk.Frame(self.root, padding=(15, 5))
        status_frame.pack(fill="x")

        self.status_label = ttk.Label(status_frame, text="Ready.", style="Muted.TLabel")
        self.status_label.pack(side="left")

        # Bottom bar (packed BEFORE the results frame so it always
        # reserves its own space and can never get squeezed off the
        # bottom of the window, regardless of window/screen height)
        bottom_frame = ttk.Frame(self.root, padding=15)
        bottom_frame.pack(side="bottom", fill="x")

        self.result_count = ttk.Label(bottom_frame, text="Results: 0", style="Muted.TLabel")
        self.result_count.pack(side="left")

        self.clear_button = ttk.Button(
            bottom_frame, text="Clear", command=self.clear_results
        )
        self.clear_button.pack(side="right")

        self.export_button = ttk.Button(
            bottom_frame, text="⬇  Export CSV", command=self.export_csv,
            style="Accent.TButton"
        )
        self.export_button.pack(side="right", padx=10)

        # Results
        results_frame = ttk.LabelFrame(
            self.root, text="Results", padding=10
        )
        results_frame.pack(
            fill="both", expand=True, padx=15, pady=10
        )

        columns = (
            "name", "category", "rating", "reviews",
            "phone", "website", "address", "maps_url"
        )
        self.results_table = ttk.Treeview(
            results_frame, columns=columns, show="headings"
        )

        self.results_table.heading("name", text="Business Name")
        self.results_table.heading("category", text="Category")
        self.results_table.heading("rating", text="Rating")
        self.results_table.heading("reviews", text="Reviews")
        self.results_table.heading("phone", text="Phone")
        self.results_table.heading("website", text="Website")
        self.results_table.heading("address", text="Address")
        self.results_table.heading("maps_url", text="Google Maps URL")

        self.results_table.column("name", width=180)
        self.results_table.column("category", width=140)
        self.results_table.column("rating", width=60, anchor="center")
        self.results_table.column("reviews", width=70, anchor="center")
        self.results_table.column("phone", width=130)
        self.results_table.column("website", width=220)
        self.results_table.column("address", width=220)
        self.results_table.column("maps_url", width=320)

        self.results_table.tag_configure("oddrow", background=self.COLOR_BG_ENTRY)
        self.results_table.tag_configure("evenrow", background=self.COLOR_ROW_ALT)

        scrollbar_y = ttk.Scrollbar(
            results_frame, orient="vertical", command=self.results_table.yview
        )
        scrollbar_x = ttk.Scrollbar(
            results_frame, orient="horizontal", command=self.results_table.xview
        )

        self.results_table.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        self.results_table.pack(side="top", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        # Load the location database into the dropdowns.
        self.load_countries()

    # =========================================================
    # LOCATION DATABASE / DROPDOWNS
    # =========================================================

    def load_countries(self):
        try:
            self.countries = Country.get_countries()
            self.country_map = {c.name: c for c in self.countries}
            names = [c.name for c in self.countries]
            self.country_entry["values"] = names

            if "United States" in self.country_map:
                self.country_entry.set("United States")
                self.on_country_selected()
            elif names:
                self.country_entry.current(0)
                self.on_country_selected()
        except Exception as exc:
            messagebox.showerror(
                "Location Database Error",
                f"Could not load countries.\n\n{exc}"
            )

    def get_country(self):
        return self.country_map.get(self.country_entry.get().strip())

    @staticmethod
    def get_state_code(state):
        # country_state_city 0.1.0 uses iso_code.
        return getattr(state, "iso_code", None) or getattr(state, "state_code", None) or getattr(state, "iso2", None)

    def load_states_for_country(self, country):
        self.states = []
        self.state_map = {}
        self.state_entry["values"] = []
        self.city_entry["values"] = []
        self.state_entry.set("")
        self.city_entry.set("")
        self.cities = []
        self.city_map = {}

        if not country:
            return

        states = State.get_states_of_country(country.iso2)
        self.states = states or []
        self.state_map = {s.name: s for s in self.states}
        names = [s.name for s in self.states]
        self.state_entry["values"] = names

        if names:
            preferred = "California" if country.name == "United States" and "California" in names else names[0]
            self.state_entry.set(preferred)
            self.on_state_selected()

    def on_country_selected(self, event=None):
        country = self.get_country()
        self.bulk_states = []
        self.bulk_cities = []
        self.update_location_summary()
        self.load_states_for_country(country)

    def load_cities_for_state(self, state):
        self.cities = []
        self.city_map = {}
        self.city_entry["values"] = []
        self.city_entry.set("")

        country = self.get_country()
        if not country or not state:
            return

        state_code = self.get_state_code(state)
        if not state_code:
            return

        cities = City.get_cities_of_state(country.iso2, state_code)
        self.cities = cities or []
        self.city_map = {c.name: c for c in self.cities}
        names = [c.name for c in self.cities]
        self.city_entry["values"] = names

        if names:
            preferred = "Los Angeles" if state.name == "California" and "Los Angeles" in names else names[0]
            self.city_entry.set(preferred)

    def on_state_selected(self, event=None):
        state = self.state_map.get(self.state_entry.get().strip())
        self.bulk_cities = []
        self.update_location_summary()
        self.load_cities_for_state(state)

    def update_location_summary(self):
        state_text = f"{len(self.bulk_states)} bulk states" if self.bulk_states else "No bulk states"
        city_text = f"{len(self.bulk_cities)} bulk cities" if self.bulk_cities else "No bulk cities"
        keyword_text = f"{len(self.bulk_keywords)} bulk keywords" if self.bulk_keywords else "No bulk keywords"
        self.location_summary.config(text=f"{state_text} | {city_text} | {keyword_text}")

    def clear_query_placeholder(self, event=None):
        if self.query_placeholder_active:
            self.query_entry.delete(0, "end")
            self.query_entry.config(foreground=self.COLOR_FG)
            self.query_placeholder_active = False

    def restore_query_placeholder(self, event=None):
        if not self.query_entry.get().strip():
            self.query_entry.insert(0, self.query_placeholder)
            self.query_entry.config(foreground=self.COLOR_FG_MUTED)
            self.query_placeholder_active = True

    def get_search_keywords(self):
        if self.bulk_keywords:
            return list(self.bulk_keywords)

        value = self.query_entry.get().strip()
        if not value or self.query_placeholder_active:
            return []
        return [value]

    def open_bulk_dialog(self, title, current_values, save_callback, hint):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("520x430")
        dialog.configure(bg=self.COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=hint, wraplength=480, style="Muted.TLabel").pack(
            anchor="w", padx=15, pady=(15, 8)
        )

        text = tk.Text(
            dialog, width=60, height=17,
            bg=self.COLOR_BG_ENTRY, fg=self.COLOR_FG,
            insertbackground=self.COLOR_FG,
            relief="flat", highlightthickness=1,
            highlightbackground=self.COLOR_BORDER,
            highlightcolor=self.COLOR_ACCENT,
            padx=8, pady=8
        )
        text.pack(fill="both", expand=True, padx=15, pady=5)

        if current_values:
            text.insert("1.0", "\n".join(current_values))

        button_frame = ttk.Frame(dialog, padding=15)
        button_frame.pack(fill="x")

        def save():
            values = [
                line.strip() for line in text.get("1.0", "end").splitlines()
                if line.strip()
            ]
            save_callback(values)
            dialog.destroy()

        ttk.Button(button_frame, text="Save", command=save, style="Accent.TButton").pack(side="right")
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side="right", padx=(0, 8)
        )

    def open_bulk_states(self):
        country = self.get_country()
        if not country:
            messagebox.showerror("Bulk States", "Please select a country first.")
            return

        valid_names = {s.name for s in self.states}

        def save(values):
            invalid = [v for v in values if v not in valid_names]
            if invalid:
                messagebox.showerror(
                    "Bulk States",
                    "These states were not found in the selected country:\n\n" +
                    "\n".join(invalid[:20])
                )
                return
            self.bulk_states = list(dict.fromkeys(values))
            self.update_location_summary()

        self.open_bulk_dialog(
            "Bulk States",
            self.bulk_states,
            save,
            "Enter one state/province per line. Only states from the selected country are accepted."
        )

    def open_bulk_cities(self):
        state = self.state_map.get(self.state_entry.get().strip())
        if not state:
            messagebox.showerror("Bulk Cities", "Please select a state first.")
            return

        valid_names = {c.name for c in self.cities}

        def save(values):
            invalid = [v for v in values if v not in valid_names]
            if invalid:
                messagebox.showerror(
                    "Bulk Cities",
                    "These cities were not found in the selected state:\n\n" +
                    "\n".join(invalid[:20])
                )
                return
            self.bulk_cities = list(dict.fromkeys(values))
            self.update_location_summary()

        self.open_bulk_dialog(
            "Bulk Cities",
            self.bulk_cities,
            save,
            f"Enter one city per line. Cities are checked against {state.name}."
        )

    def open_bulk_keywords(self):
        def save(values):
            self.bulk_keywords = list(dict.fromkeys(values))
            self.update_location_summary()

        self.open_bulk_dialog(
            "Bulk Keywords",
            self.bulk_keywords,
            save,
            "Enter one search keyword per line. For example: Restaurants, Cafe, Bakery, Gym."
        )

    def build_location_jobs(self):
        country = self.get_country()
        if not country:
            raise ValueError("Please select a country.")

        selected_state_name = self.state_entry.get().strip()
        selected_city_name = self.city_entry.get().strip()

        if self.bulk_states:
            state_names = list(self.bulk_states)
        elif self.random_state_var.get():
            if not self.states:
                raise ValueError("No states are available for the selected country.")
            state_names = [random.choice(self.states).name]
        else:
            state_names = [selected_state_name]

        jobs = []

        for state_name in state_names:
            state = self.state_map.get(state_name)
            if not state:
                # A bulk state may be from the current country but not in the map
                # if the dropdown was changed unexpectedly. Reload safely.
                state = next((s for s in self.states if s.name == state_name), None)
            if not state:
                continue

            state_code = self.get_state_code(state)
            if not state_code:
                continue

            country_cities = City.get_cities_of_state(country.iso2, state_code) or []
            city_names = [c.name for c in country_cities]
            city_lookup = {c.name: c for c in country_cities}

            if self.bulk_cities and not self.random_city_var.get():
                chosen_cities = list(self.bulk_cities)
            elif self.random_city_var.get():
                if not city_names:
                    continue
                chosen_cities = [random.choice(city_names)]
            else:
                chosen_cities = [selected_city_name]

            for city_name in chosen_cities:
                # If a manually selected city is not valid for this state,
                # still allow it so the original Google Maps search behaviour
                # remains available.
                if city_name:
                    jobs.append((country.name, state.name, city_name))

        if not jobs:
            raise ValueError("No valid country/state/city locations were selected.")

        # Remove duplicate location jobs while preserving order.
        return list(dict.fromkeys(jobs))

    # =========================================================
    # START
    # =========================================================

    def start_scraping(self):
        keywords = self.get_search_keywords()

        try:
            max_results = int(self.max_results.get())
        except ValueError:
            messagebox.showerror("Error", "Max Results must be a number.")
            return

        if max_results < 1:
            messagebox.showerror("Error", "Max Results must be at least 1.")
            return

        if not keywords:
            messagebox.showerror("Error", "Please enter what you want to search or add Bulk Keywords.")
            return

        try:
            location_jobs = self.build_location_jobs()
        except Exception as exc:
            messagebox.showerror("Location Error", str(exc))
            return

        self.clear_results()
        self.stop_requested = False
        # Run every selected keyword for every selected location.
        keyword_jobs = [
            (keyword, country, state, city)
            for country, state, city in location_jobs
            for keyword in keywords
        ]

        self.multi_scrape_active = len(keyword_jobs) > 1

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(
            text=f"Starting scraper for {len(keyword_jobs)} search job(s)..."
        )

        # Do not freeze Tkinter while Playwright is running.
        thread = threading.Thread(
            target=self.scrape_locations,
            args=(keyword_jobs, max_results),
            daemon=True
        )
        thread.start()

    def scrape_locations(self, keyword_jobs, max_results):
        total_jobs = len(keyword_jobs)

        for job_index, (keyword, country, state, city) in enumerate(keyword_jobs, start=1):
            if self.stop_requested:
                break

            search_text = f"{keyword}, {city}, {state}, {country}"
            encoded_search = urllib.parse.quote_plus(search_text)
            maps_url = f"https://www.google.com/maps/search/{encoded_search}"

            print(
                f"\n========== SEARCH {job_index}/{total_jobs} ==========\n"
                f"Keyword: {keyword}\n"
                f"Location: {city}, {state}, {country}"
            )

            self.root.after(
                0,
                lambda i=job_index, n=total_jobs, k=keyword, c=city, st=state:
                self.status_label.config(
                    text=f"Search {i}/{n}: {k} — {c}, {st}"
                )
            )

            self.scrape(maps_url, max_results)

            if self.stop_requested:
                break

        self.multi_scrape_active = False
        self.root.after(
            0,
            lambda: self.status_label.config(
                text=f"Finished. {len(self.results)} businesses scraped."
            )
        )
        self.root.after(0, lambda: self.start_button.config(state="normal"))
        self.root.after(0, lambda: self.stop_button.config(state="disabled"))

    # =========================================================
    # STOP
    # =========================================================

    def stop_scraping(self):
        self.stop_requested = True
        self.status_label.config(text="Stop requested...")

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def clean_text(value):
        if not value:
            return ""
        return " ".join(value.split()).strip()

    @staticmethod
    def get_business_name(card):
        selectors = [
            'a[href*="/maps/place/"][aria-label]',
            'a[href*="/maps/place/"]'
        ]

        for selector in selectors:
            link = card.locator(selector).first
            if link.count() == 0:
                continue

            name = link.get_attribute("aria-label")
            if name:
                return GoogleMapsScraperApp.clean_text(name)

            text = link.inner_text()
            if text:
                return GoogleMapsScraperApp.clean_text(text)

        return ""

    @staticmethod
    def get_business_url(card):
        link = card.locator('a[href*="/maps/place/"]').first

        if link.count() == 0:
            return ""

        href = link.get_attribute("href")
        return href or ""

    @staticmethod
    def get_address_from_card(card):
        # Google Maps result cards normally expose the address
        # inside a line containing " · ".
        try:
            lines = [
                GoogleMapsScraperApp.clean_text(line)
                for line in card.inner_text().splitlines()
                if GoogleMapsScraperApp.clean_text(line)
            ]
        except Exception:
            return ""

        for line in lines:
            if " · " not in line:
                continue

            parts = line.split(" · ", 1)
            if len(parts) != 2:
                continue

            possible = GoogleMapsScraperApp.clean_text(parts[1])
            possible = possible.replace("", "").strip()

            if not possible:
                continue

            # Ignore price ranges.
            if possible.startswith(("$", "€", "£")):
                continue

            # Ignore hours.
            if any(
                word.lower() in possible.lower()
                for word in ("opens", "closes", "closed", "open")
            ):
                continue

            return possible

        return ""

    @staticmethod
    def get_detail_address(page):
        selectors = [
            'button[data-item-id="address"]',
            '[data-item-id="address"]'
        ]

        for selector in selectors:
            locator = page.locator(selector).first

            if locator.count() == 0:
                continue

            try:
                text = locator.get_attribute("aria-label")
                if text:
                    text = text.replace("Address: ", "").strip()
                    if text:
                        return GoogleMapsScraperApp.clean_text(text)

                text = locator.inner_text()
                if text:
                    return GoogleMapsScraperApp.clean_text(text)
            except Exception:
                pass

        return ""

    @staticmethod
    def get_website(page):
        # Google Maps commonly marks the official website with
        # data-item-id="authority".
        selectors = [
            'a[data-item-id="authority"]',
            'a[href^="http"][aria-label*="Website"]',
            'a[href^="http"]'
        ]

        ignored_domains = (
            "google.com",
            "googleusercontent.com",
            "gstatic.com",
            "googleadservices.com"
        )

        for selector in selectors:
            links = page.locator(selector)

            try:
                count = links.count()
            except Exception:
                continue

            for i in range(count):
                try:
                    href = links.nth(i).get_attribute("href")
                except Exception:
                    continue

                if not href or not href.startswith("http"):
                    continue

                parsed = urllib.parse.urlparse(href)
                domain = parsed.netloc.lower()

                if any(
                    domain == d or domain.endswith("." + d)
                    for d in ignored_domains
                ):
                    continue

                return href

        return ""

    @staticmethod
    def get_detail_rating(page):
        selectors = [
            'div.F7nice span[aria-hidden="true"]',
            'span[aria-label*="stars" i]'
        ]

        for selector in selectors:
            locator = page.locator(selector).first

            if locator.count() == 0:
                continue

            try:
                text = locator.inner_text()
                if text:
                    match = re.search(r"[\d.,]+", text)
                    if match:
                        return match.group(0)

                label = locator.get_attribute("aria-label")
                if label:
                    match = re.search(r"[\d.,]+", label)
                    if match:
                        return match.group(0)
            except Exception:
                pass

        return ""

    @staticmethod
    def get_detail_review_count(page):
        selectors = [
            'div.F7nice span[aria-label*="review" i]',
            'button[aria-label*="review" i]'
        ]

        for selector in selectors:
            locator = page.locator(selector).first

            if locator.count() == 0:
                continue

            try:
                label = locator.get_attribute("aria-label") or locator.inner_text()
                if label:
                    digits = re.sub(r"[^\d]", "", label)
                    if digits:
                        return digits
            except Exception:
                pass

        return ""

    @staticmethod
    def get_detail_phone(page):
        selectors = [
            'button[data-item-id^="phone:tel:"]',
            '[data-item-id^="phone:tel:"]'
        ]

        for selector in selectors:
            locator = page.locator(selector).first

            if locator.count() == 0:
                continue

            try:
                text = locator.get_attribute("aria-label")
                if text:
                    text = text.replace("Phone: ", "").strip()
                    if text:
                        return GoogleMapsScraperApp.clean_text(text)

                text = locator.inner_text()
                if text:
                    return GoogleMapsScraperApp.clean_text(text)
            except Exception:
                pass

        return ""

    @staticmethod
    def get_detail_category(page):
        selectors = [
            'button[jsaction*="pane.rating.category"]',
            'button.DkEaL'
        ]

        for selector in selectors:
            locator = page.locator(selector).first

            if locator.count() == 0:
                continue

            try:
                text = locator.inner_text()
                if text:
                    return GoogleMapsScraperApp.clean_text(text)
            except Exception:
                pass

        return ""

    # =========================================================
    # SCRAPER
    # =========================================================

    def goto_with_retry(self, page, url, attempts=4):
        """Navigate reliably through temporary network changes."""
        last_error = None

        for attempt in range(1, attempts + 1):
            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                return True
            except PlaywrightError as exc:
                last_error = str(exc)
                print(f"Navigation attempt {attempt}/{attempts} failed: {exc}")

                if attempt < attempts:
                    page.wait_for_timeout(3000 * attempt)

        raise RuntimeError(
            "Could not open Google Maps after "
            f"{attempts} attempts. Last error: {last_error}"
        )

    def scrape(self, maps_url, max_results):
        results = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, channel="chrome")

                # Keep the search page alive.
                search_page = browser.new_page(
                    viewport={"width": 1400, "height": 900}
                )

                print("\nOpening Google Maps...")
                self.goto_with_retry(search_page, maps_url)
                search_page.wait_for_timeout(5000)

                print("Google Maps opened.")

                feed = search_page.locator('div[role="feed"]').first

                if feed.count() == 0:
                    self.ui_error("Could not find Google Maps results.")
                    browser.close()
                    return

                # -------------------------------------------------
                # Load as many result cards as possible
                # -------------------------------------------------

                previous_count = 0
                unchanged_count = 0
                max_scroll_attempts = 40

                for _ in range(max_scroll_attempts):
                    if self.stop_requested:
                        break

                    cards = search_page.locator(
                        'div[role="feed"] div[role="article"]'
                    )
                    current_count = cards.count()

                    print(f"Loaded businesses: {current_count}")

                    self.root.after(
                        0,
                        lambda c=current_count: self.status_label.config(
                            text=f"Loaded {c} businesses..."
                        )
                    )

                    if current_count >= max_results:
                        print("Target number reached.")
                        break

                    if current_count == previous_count:
                        unchanged_count += 1
                    else:
                        unchanged_count = 0

                    if unchanged_count >= 6:
                        print("No more businesses loading.")
                        break

                    previous_count = current_count

                    # Scroll the feed.
                    feed.evaluate(
                        """element => {
                            element.scrollTop = element.scrollHeight;
                        }"""
                    )

                    search_page.wait_for_timeout(2200)

                # -------------------------------------------------
                # Collect all cards BEFORE opening detail pages.
                # This is the important fix.
                # -------------------------------------------------

                cards = search_page.locator(
                    'div[role="feed"] div[role="article"]'
                )

                total_cards = min(cards.count(), max_results)

                businesses = []
                seen_urls = set()

                print(f"\nCollecting {total_cards} business cards...")

                for i in range(total_cards):
                    if self.stop_requested:
                        break

                    card = cards.nth(i)

                    try:
                        name = self.get_business_name(card)
                        href = self.get_business_url(card)
                        address = self.get_address_from_card(card)

                        if not name or not href:
                            continue

                        # Normalize URL enough to remove obvious duplicates.
                        base_url = href.split("?")[0]

                        if base_url in seen_urls:
                            continue

                        seen_urls.add(base_url)

                        businesses.append({
                            "name": name,
                            "address": address,
                            "maps_url": href
                        })

                        print(f"  {len(businesses)}. {name}")

                    except Exception as e:
                        print(f"Error reading card {i + 1}: {e}")

                print(f"\nFound {len(businesses)} unique businesses.")

                # -------------------------------------------------
                # Open each business in a NEW PAGE.
                # Search results page stays intact.
                # -------------------------------------------------

                detail_page = browser.new_page(
                    viewport={"width": 1400, "height": 900}
                )

                for index, business in enumerate(businesses, start=1):
                    if self.stop_requested:
                        print("Scraping stopped.")
                        break

                    print(
                        f"\nProcessing {index}/{len(businesses)}: "
                        f"{business['name']}"
                    )

                    self.root.after(
                        0,
                        lambda i=index, n=len(businesses):
                        self.status_label.config(
                            text=f"Processing {i}/{n}..."
                        )
                    )

                    try:
                        self.goto_with_retry(detail_page, business["maps_url"])

                        detail_page.wait_for_timeout(1800)

                        # Google may redirect to a cleaner Maps URL.
                        actual_maps_url = detail_page.url

                        # Always prefer the full address from the business detail page.
                        # Google Maps search cards often contain only a shortened street address.
                        address = self.get_detail_address(detail_page)

                        # Fallback to the search-card address if the detail page
                        # does not expose an address.
                        if not address:
                            address = business["address"]

                        if not address:
                            address = "N/A"

                        website = self.get_website(detail_page)

                        if not website:
                            website = "N/A"

                        rating = self.get_detail_rating(detail_page) or "N/A"
                        review_count = self.get_detail_review_count(detail_page) or "N/A"
                        phone = self.get_detail_phone(detail_page) or "N/A"
                        category = self.get_detail_category(detail_page) or "N/A"

                        result = {
                            "name": business["name"],
                            "category": category,
                            "rating": rating,
                            "reviews": review_count,
                            "phone": phone,
                            "website": website,
                            "address": address,
                            "maps_url": actual_maps_url
                        }

                        results.append(result)

                        print(f"✓ {result['name']}")
                        print(f"  Category: {result['category']}")
                        print(f"  Rating: {result['rating']} ({result['reviews']} reviews)")
                        print(f"  Phone: {result['phone']}")
                        print(f"  Address: {result['address']}")
                        print(f"  Website: {result['website']}")

                        self.root.after(
                            0,
                            lambda r=result: self.add_result(r)
                        )

                        self.root.after(
                            0,
                            lambda n=len(results):
                            self.status_label.config(
                                text=f"Scraped {n} businesses..."
                            )
                        )

                    except PlaywrightTimeoutError:
                        print(
                            f"Timeout while processing "
                            f"{business['name']}"
                        )

                    except Exception as e:
                        print(
                            f"Error processing "
                            f"{business['name']}: {e}"
                        )

                detail_page.close()
                browser.close()

                print("\n================================")
                print("SCRAPING COMPLETE")
                print("================================")
                print(f"Total scraped: {len(results)}")

                self.root.after(
                    0,
                    lambda n=len(results):
                    self.status_label.config(
                        text=f"Finished. {n} businesses scraped."
                    )
                )

        except Exception as exc:
            error_message = str(exc)
            print("\nSCRAPER ERROR:")
            print(error_message)

            self.root.after(
                0,
                lambda err=error_message: messagebox.showerror(
                    "Scraper Error",
                    err
                )
            )

        finally:
            if not self.multi_scrape_active:
                self.root.after(
                    0,
                    lambda: self.start_button.config(state="normal")
                )
                self.root.after(
                    0,
                    lambda: self.stop_button.config(state="disabled")
                )

    # =========================================================
    # GUI RESULT
    # =========================================================

    def add_result(self, result):
        self.results.append(result)

        count_before = len(self.results_table.get_children())
        tag = "evenrow" if count_before % 2 == 0 else "oddrow"

        self.results_table.insert(
            "",
            "end",
            values=(
                result["name"],
                result.get("category", "N/A"),
                result.get("rating", "N/A"),
                result.get("reviews", "N/A"),
                result.get("phone", "N/A"),
                result["website"],
                result["address"],
                result["maps_url"]
            ),
            tags=(tag,)
        )

        count = len(self.results_table.get_children())

        self.result_count.config(
            text=f"Results: {count}"
        )

    # =========================================================
    # CLEAR
    # =========================================================

    def clear_results(self):
        self.results = []

        for item in self.results_table.get_children():
            self.results_table.delete(item)

        self.result_count.config(text="Results: 0")

    # =========================================================
    # EXPORT
    # =========================================================

    def export_csv(self):
        if not self.results:
            messagebox.showinfo(
                "Export",
                "There are no results to export."
            )
            return

        filepath = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not filepath:
            return

        try:
            with open(
                filepath,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "name",
                        "category",
                        "rating",
                        "reviews",
                        "phone",
                        "website",
                        "address",
                        "maps_url"
                    ]
                )

                writer.writeheader()
                writer.writerows(self.results)

            messagebox.showinfo(
                "Export Complete",
                f"Saved {len(self.results)} businesses."
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                str(e)
            )

    # =========================================================
    # UI ERROR
    # =========================================================

    def ui_error(self, message):
        self.root.after(
            0,
            lambda: messagebox.showerror(
                "Scraper Error",
                message
            )
        )


def main():
    root = tk.Tk()
    app = GoogleMapsScraperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()