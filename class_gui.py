#!/usr/bin/env python3
"""
Cryptorial's Lazy Arch Setup Script (CLASS) - Graphical GTK4 Wizard
Developed by Cryptorial
"""

import sys
import os
import json
import subprocess
import threading
import argparse
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Pango, Gdk

# -------------------------------------------------------------
# Desktop Environment & GPU Hardware Auto-Detection
# -------------------------------------------------------------

def get_desktop_environment():
    xdg_current = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session_desktop = os.environ.get("XDG_SESSION_DESKTOP", "").lower()
    combined = f"{xdg_current} {session_desktop}"
    if "kde" in combined or "plasma" in combined:
        return "kde"
    elif "gnome" in combined:
        return "gnome"
    elif "cinnamon" in combined:
        return "cinnamon"
    return "other"


def detect_gpus():
    detected_gpus = []
    gpu_pkgs = set()

    try:
        lspci_out = subprocess.check_output("lspci -k", shell=True, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        lspci_out = ""

    vga_lines = [
        line for line in lspci_out.splitlines()
        if any(kw in line for kw in ["VGA compatible controller", "3D controller", "Display controller"])
    ]
    combined_text = "\n".join(vga_lines).lower()

    has_amd = any(kw in combined_text for kw in ["amd", "advanced micro devices", "ati"])
    has_nvidia = "nvidia" in combined_text
    has_intel = "intel" in combined_text

    # Fallback to sysfs vendor IDs if lspci is empty or unavailable
    if not (has_amd or has_nvidia or has_intel):
        for vpath in ["/sys/class/drm/card0/device/vendor", "/sys/class/drm/card1/device/vendor"]:
            if os.path.exists(vpath):
                try:
                    with open(vpath) as f:
                        vid = f.read().strip()
                        if vid == "0x1002": has_amd = True
                        elif vid == "0x10de": has_nvidia = True
                        elif vid == "0x8086": has_intel = True
                except Exception:
                    pass

    if has_amd:
        detected_gpus.append("AMD Radeon (Mesa / RADV)")
        gpu_pkgs.update(["vulkan-radeon", "lib32-vulkan-radeon", "mesa", "lib32-mesa"])

    if has_nvidia:
        detected_gpus.append("NVIDIA (Proprietary Drivers)")
        res = subprocess.run(["pacman", "-Qq", "nvidia-utils"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            gpu_pkgs.update(["lib32-nvidia-utils", "nvidia-settings"])
        else:
            gpu_pkgs.update(["nvidia", "nvidia-utils", "lib32-nvidia-utils", "nvidia-settings"])

    if has_intel:
        detected_gpus.append("Intel Graphics (Mesa / Vulkan / Arc)")
        gpu_pkgs.update(["mesa", "lib32-mesa", "vulkan-intel", "lib32-vulkan-intel", "intel-media-driver"])

    if not detected_gpus:
        detected_gpus.append("Generic / Virtual GPU (Mesa)")
        gpu_pkgs.update(["mesa", "lib32-mesa"])

    return " + ".join(detected_gpus), sorted(gpu_pkgs)


# -------------------------------------------------------------
# Configuration Data (Faithfully retrieved from Arch / AUR)
# -------------------------------------------------------------

EMULATOR_PKGS_SET = {
    "pcsx2-git", "rpcs3-git", "dolphin-emu", "ppsspp",
    "retroarch", "mame", "duckstation-gpl", "eden-git"
}

# Categories ordered with Emulators as the last category
BASE_CATEGORIES = [
    (
        "Gaming & Compatibility",
        [
            ("steam", "Steam", "Valve's digital software delivery platform & store"),
            ("gamescope", "Gamescope", "SteamOS session compositing micro-compositor window manager"),
            ("protonplus", "ProtonPlus", "Modern compatibility tools manager for Proton, Wine, and GE"),
            ("protonup-qt", "ProtonUp-Qt", "Install and manage GE-Proton, Luxtorpeda & custom tools"),
            ("winetricks", "Winetricks", "Script to install runtime libraries and workarounds in Wine"),
            ("protontricks", "Protontricks", "Wrapper to run Winetricks commands for Steam Play/Proton games"),
            ("hydra-launcher-bin", "Hydra Launcher", "Open-source gaming platform to manage your game library"),
            ("xodus-nexus-bin", "Xodus Nexus", "Xbox-inspired launcher for Microsoft Store PC games on Linux"),
            ("portproton", "PortProton", "Software for playing Windows games and emulators with Proton"),
            ("r2modman-bin", "r2modman", "Thunderstore mod manager for Unity and Steam games"),
            ("prismlauncher", "Prism Launcher", "Minecraft launcher with multi-instance & modpack support"),
        ]
    ),
    (
        "Performance, Overlays & Hardware",
        [
            ("gamemode", "GameMode", "Feral Interactive daemon to optimize system performance on demand"),
            ("goverlay", "Goverlay", "GUI to configure Vulkan/OpenGL overlays (auto-installs preview tools)"),
            ("mangohud", "MangoHud", "Vulkan & OpenGL overlay for monitoring FPS, temperatures, CPU/GPU load"),
            ("mangojuice", "MangoJuice", "Companion launcher helper for configuring MangoHud"),
            ("vkbasalt", "vkBasalt", "Vulkan post-processing layer (CAS, FXAA, SMAA, deband)"),
            ("corectrl", "CoreCtrl", "Hardware performance control application for CPU and GPU"),
            ("lact", "LACT", "Linux AMDGPU controller and overclocking GUI"),
            ("openrgb", "OpenRGB", "Open-source RGB lighting control without vendor software"),
        ]
    ),
    (
        "Communication & Social",
        [
            ("discord", "Discord", "All-in-one voice, video, and text communication platform"),
            ("zapzap", "ZapZap", "WhatsApp desktop application written in PyQt6"),
            ("rootapp-bin", "Root App", "Discord alternative for gaming communities and groups"),
        ]
    ),
    (
        "Media, Audio & Recording",
        [
            ("vice-clipper", "Vice Clipper", "Medal.tv-style game clip recorder for Linux: instant replay and session recording"),
            ("vlc", "VLC Media Player", "Free and open-source cross-platform multimedia player"),
            ("stremio", "Stremio", "One-stop video streaming hub for movies, series, and channels"),
            ("spotify", "Spotify", "Desktop digital music streaming service client"),
            ("parabolic", "Parabolic", "Web video and audio media downloader"),
            ("losslesscut-bin", "LosslessCut", "Cross-platform GUI tool for lossless video/audio trimming"),
            ("songrec", "Songrec", "Open-source, unofficial Shazam audio identifier client"),
        ]
    ),
    (
        "Productivity, Utilities & System",
        [
            ("baobab", "Baobab", "Graphical disk usage analyzer and directory tree browser"),
            ("flatseal", "Flatseal", "Permissions manager for Flatpak applications"),
            ("ventoy-bin", "Ventoy USB", "Bootable multi-ISO USB creator solution"),
            ("kdeconnect", "KDE Connect", "Seamless wireless phone and desktop integration"),
            ("localsend-bin", "LocalSend", "Cross-platform local network file sharing (AirDrop alternative)"),
            ("iriunwebcam-bin", "Iriun Webcam", "Use your phone's camera as a wireless webcam on PC"),
            ("qbittorrent", "qBittorrent", "Fast, lightweight BitTorrent client in Qt and C++"),
            ("btop", "btop", "Modern terminal resource monitor and process viewer"),
            ("fastfetch", "fastfetch", "Feature-rich and performance-oriented system information tool"),
            ("bazaar", "Bazaar", "Modern application store for Flatpaks and Flathub"),
        ]
    ),
    (
        "Emulators & Retro Gaming",
        [
            ("pcsx2-git", "PCSX2", "PlayStation 2 emulator"),
            ("rpcs3-git", "RPCS3", "PlayStation 3 emulator"),
            ("dolphin-emu", "Dolphin", "GameCube and Wii emulator"),
            ("ppsspp", "PPSSPP", "PlayStation Portable (PSP) emulator written in C++"),
            ("retroarch", "RetroArch", "Reference frontend for libretro multi-system emulation"),
            ("mame", "MAME", "Multiple Arcade Machine Emulator using SDL with OpenGL support"),
            ("duckstation-gpl", "DuckStation", "Fast PlayStation 1 (PSX) emulator focusing on playability and speed"),
            ("eden-git", "Eden", "Nintendo Switch emulator fork"),
        ]
    ),
]

def get_categorized_apps():
    categories = []
    de = get_desktop_environment()
    for cat_name, items in BASE_CATEGORIES:
        new_items = list(items)
        if cat_name == "Productivity, Utilities & System" and de in ("kde", "gnome"):
            new_items.insert(0, ("waywallen", "Waywallen", "Wallpaper manager for Wayland (with display daemon & DE plugin)"))
        categories.append((cat_name, new_items))
    return categories

# Strict browser selection list
BROWSERS = [
    ("brave-origin-bin", "Brave Origin (Recommended)", "The minimalist browser from the makers of Brave"),
    ("firefox", "Firefox", "Fast, private and safe open-source browser by Mozilla"),
    ("chromium", "Chromium", "Open-source web browser project developed by Google"),
    ("vivaldi", "Vivaldi", "Advanced, feature-rich browser built for power users"),
    ("other", "Other (Search Repositories / AUR)", "Search and install any browser package"),
]

# Curated browser extensions list
BROWSER_EXTENSIONS = [
    (
        "return-youtube-dislike",
        "Return YouTube Dislike",
        "Restores the dislike count display on YouTube videos",
        "gebbhagfogifgggkldgodflihgfeippi",
        "{762f9885-5a13-4abd-9c77-433dcd38b8fd}",
        "https://addons.mozilla.org/firefox/downloads/latest/return-youtube-dislikes/latest.xpi",
        True
    ),
    (
        "sponsorblock",
        "SponsorBlock",
        "Skip sponsor segments, intros, outros, and subscription reminders on YouTube",
        "mnjggcdmjocbbbhaepdhchncahnbgone",
        "sponsorBlocker@ajay.app",
        "https://addons.mozilla.org/firefox/downloads/latest/sponsorblock/latest.xpi",
        True
    ),
    (
        "adblock-for-youtube",
        "Adblock for YouTube",
        "Removes pre-roll video ads, banners, and popups on YouTube",
        "cmedhionkhpnakcndndgjdbohmhepckk",
        "jid1-q4sG8pYhq8KGHs@jetpack",
        "https://addons.mozilla.org/firefox/downloads/latest/adblock-for-youtube/latest.xpi",
        True
    ),
    (
        "darkreader",
        "Dark Reader",
        "Inverts brightness and applies high-contrast dark themes to every website",
        "eimadpbcbfnmbkopoojfekhnkhdbieeh",
        "addon@darkreader.org",
        "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi",
        True
    ),
    (
        "consent-o-matic",
        "Consent-O-Matic",
        "Automatically fills out and rejects GDPR / ePrivacy cookie popups in the background",
        "mljpablpbeekflopdjnioimmkigebmhi",
        "gdpr@cavi.au.dk",
        "https://addons.mozilla.org/firefox/downloads/latest/consent-o-matic/latest.xpi",
        True
    ),
    (
        "adnauseam",
        "AdNauseam",
        "Blocks ads while clicking them in the background to obfuscate your browsing profile",
        "",
        "adnauseam@rednoise.org",
        "https://addons.mozilla.org/firefox/downloads/latest/adnauseam/latest.xpi",
        True
    ),
    (
        "microsoft-to-microslop",
        "Microsoft to Microslop",
        "Replaces every visual occurrence of 'Microsoft' on web pages with 'Microslop'",
        "hlkljlkdinjnbfmclionhbefbnefcgll",
        "microsoft-to-microslop@example.com",
        "https://addons.mozilla.org/firefox/downloads/latest/microsoft-to-microslop/latest.xpi",
        True
    ),
    (
        "hola-vpn",
        "Hola VPN",
        "Website unblocker and proxy extension",
        "gkojfkhlekighikafcpjkiklfbnlmeio",
        "",
        "",
        True
    ),
]

# Flatpak applications section
FLATPAK_APPS = [
    (
        "com.dec05eba.gpu_screen_recorder",
        "GPU Screen Recorder (GSR)",
        "A shadowplay-like screen recorder for Linux with instant replay and minimal performance overhead",
        True  # Selected by default, can be ticked off
    ),
]

# Custom Setup & Management Scripts section (Optional / Opt-in)
SCRIPTS = [
    (
        "slssteam",
        "SLSsteam Manager (slssteam)",
        "CLI manager and auto-updater for SLSsteam. Unlocks DLCs and manages achievements for Steam and Flatpak Steam.",
        False  # Opt-in by default
    ),
    (
        "vencord",
        "Vencord Discord Mod (vencord)",
        "Automated installer and restarter utility for the Vencord client enhancement suite on Discord.",
        False  # Opt-in by default
    ),
    (
        "fix-ntfs",
        "NTFS Disk Repair & Auto-Mounter (fix-ntfs)",
        "Repairs dirty/unmountable NTFS drives, resets journal flags via ntfsfix, and permanently configures udisks2 for forced mounting.",
        False  # Opt-in by default
    ),
]


# -----------------------------
# UI Helpers (Safe Markup Escaping - Prevents Empty Labels)
# -----------------------------

def make_check_button(title, desc="", group=None):
    btn = Gtk.CheckButton()
    lbl = Gtk.Label()
    safe_title = GLib.markup_escape_text(title)
    if desc:
        safe_desc = GLib.markup_escape_text(desc)
        lbl.set_markup(f"<b>{safe_title}</b>\n<span size='small' alpha='65%'>{safe_desc}</span>")
    else:
        lbl.set_markup(f"<b>{safe_title}</b>")
    lbl.set_xalign(0)
    lbl.set_wrap(True)
    btn.set_child(lbl)
    if group is not None:
        btn.set_group(group)
    return btn


def load_custom_css():
    css = Gtk.CssProvider()
    css_data = """
    progressbar.large-progress > trough {
        min-height: 24px;
        border-radius: 8px;
    }
    progressbar.large-progress > trough > progress {
        min-height: 24px;
        border-radius: 8px;
    }
    textview.log-viewer text {
        background-color: #181825;
        color: #cdd6f4;
        font-family: monospace;
        font-size: 10pt;
    }
    """
    try:
        css.load_from_string(css_data)
    except AttributeError:
        css.load_from_data(css_data.encode("utf-8"))

    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


# -----------------------------
# Main Application Window
# -----------------------------

class CLASSWizardWindow(Gtk.ApplicationWindow):
    def __init__(self, app, output_file, status_file=None):
        super().__init__(application=app)
        self.output_file = output_file
        self.status_file = status_file

        self.set_title("Cryptorial's Lazy Arch Setup Script (CLASS)")
        # Spacious, open, comfortable window size
        self.set_default_size(940, 720)

        # Hardware Auto-Detection
        self.gpu_display_name, self.detected_gpu_pkgs = detect_gpus()

        # State storage
        self.install_gpu_drivers = False
        self.selected_browser = "brave-origin-bin"
        self.selected_extensions = {ext_id for ext_id, _, _, _, _, _, default_active in BROWSER_EXTENSIONS if default_active}
        self.selected_apps = set()
        self.selected_flatpaks = {pkg for pkg, _, _, default_active in FLATPAK_APPS if default_active}
        self.selected_scripts = {s_id for s_id, _, _, default_active in SCRIPTS if default_active}
        self.queued_aur = set()

        # Step tracking:
        # 0: Drivers (1/6), 1: Browser (2/6), 2: Extensions (3/6), 3: Apps (4/6), 4: Flatpaks (5/6), 5: Scripts (6/6), 6: Summary
        self.current_step = 0
        self.total_steps = 7
        self.is_installing = False

        # Connect window close (titlebar X) to cleanly halt the setup
        self.connect("close-request", self.on_window_close_request)

        self.build_ui()

    def build_ui(self):
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root_box)

        # Header Title Area
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header_box.set_margin_top(18)
        header_box.set_margin_bottom(14)
        header_box.set_margin_start(32)
        header_box.set_margin_end(32)

        # Top row: Titles on left, Halt Cross Button on dead right
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        top_row.set_hexpand(True)

        titles_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        titles_box.set_hexpand(True)
        titles_box.set_halign(Gtk.Align.START)

        self.title_label = Gtk.Label()
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_markup("<span size='x-large' weight='bold'>Cryptorial's Lazy Arch Setup Script</span>")
        titles_box.append(self.title_label)

        self.subtitle_label = Gtk.Label()
        self.subtitle_label.set_halign(Gtk.Align.START)
        self.subtitle_label.set_markup(f"<span size='small' alpha='65%'>Auto-detected GPU: <b>{self.gpu_display_name}</b> | Driver packages ready</span>")
        titles_box.append(self.subtitle_label)

        top_row.append(titles_box)

        # Cross button in top right that halts the whole thing
        self.btn_halt = Gtk.Button(label="X")
        self.btn_halt.set_tooltip_text("Halt Setup and Exit")
        self.btn_halt.set_halign(Gtk.Align.END)
        self.btn_halt.set_valign(Gtk.Align.START)
        self.btn_halt.set_size_request(38, 38)
        self.btn_halt.add_css_class("destructive-action")
        self.btn_halt.connect("clicked", self.on_halt_clicked)
        top_row.append(self.btn_halt)

        header_box.append(top_row)

        # Progress bar for wizard steps
        self.wizard_prog_bar = Gtk.ProgressBar()
        self.wizard_prog_bar.set_fraction(1.0 / self.total_steps)
        self.wizard_prog_bar.set_margin_top(10)
        header_box.append(self.wizard_prog_bar)

        root_box.append(header_box)

        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        root_box.append(sep1)

        # Content Area - Gtk.Stack for smooth page transitions
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_vexpand(True)
        self.stack.set_hexpand(True)
        self.stack.set_margin_start(32)
        self.stack.set_margin_end(32)
        self.stack.set_margin_top(16)
        self.stack.set_margin_bottom(12)
        root_box.append(self.stack)

        # Build each page:
        # GPU Drivers -> Browser -> Browser Extensions -> Applications -> Flatpaks -> Scripts -> Summary -> Installation Progress
        self.build_drivers_page()
        self.build_browser_page()
        self.build_extensions_page()
        self.build_apps_page()
        self.build_flatpaks_page()
        self.build_scripts_page()
        self.build_summary_page()
        self.build_progress_page()

        # Separator
        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        root_box.append(sep2)

        # Bottom Navigation Bar
        # Layout rule: Previous dead left, Skip dead center, Next dead right
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        nav_box.set_margin_top(16)
        nav_box.set_margin_bottom(18)
        nav_box.set_margin_start(32)
        nav_box.set_margin_end(32)

        # Left box: Previous (Dead Left)
        self.left_nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.left_nav_box.set_hexpand(True)
        self.left_nav_box.set_halign(Gtk.Align.START)
        self.btn_prev = Gtk.Button(label="Previous")
        self.btn_prev.set_size_request(135, 42)
        self.btn_prev.connect("clicked", self.on_prev_clicked)
        self.left_nav_box.append(self.btn_prev)
        nav_box.append(self.left_nav_box)

        # Center box: Skip (Dead Center)
        self.center_nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.center_nav_box.set_hexpand(True)
        self.center_nav_box.set_halign(Gtk.Align.CENTER)
        self.btn_skip = Gtk.Button(label="Skip Step")
        self.btn_skip.set_size_request(125, 42)
        self.btn_skip.connect("clicked", self.on_skip_clicked)
        self.center_nav_box.append(self.btn_skip)
        nav_box.append(self.center_nav_box)

        # Right box: Next (Dead Right)
        self.right_nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.right_nav_box.set_hexpand(True)
        self.right_nav_box.set_halign(Gtk.Align.END)
        self.btn_next = Gtk.Button(label="Next")
        self.btn_next.set_size_request(145, 42)
        self.btn_next.add_css_class("suggested-action")
        self.btn_next.connect("clicked", self.on_next_clicked)
        self.right_nav_box.append(self.btn_next)
        nav_box.append(self.right_nav_box)

        root_box.append(nav_box)

        # Initial display
        self.update_step_view()

    # -------------------------------------------------------------
    # Step 1: Graphics & GPU Drivers
    # -------------------------------------------------------------
    def build_drivers_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Graphics & GPU Driver Configuration (Optional):</b>\n<span size='small' alpha='65%'>GPU drivers are opt-in. Check the box below if you want to install hardware-accelerated drivers and 32-bit Vulkan libraries for your detected graphics hardware.</span>")
        page.append(info)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_margin_start(8)
        content_box.set_margin_end(8)

        pkgs_text = ", ".join(self.detected_gpu_pkgs) if self.detected_gpu_pkgs else "None"
        desc = f"Detected: {self.gpu_display_name}\nPackages: {pkgs_text}\nInstalls 32-bit & 64-bit Mesa/Vulkan runtimes and hardware acceleration."

        self.chk_gpu_drivers = make_check_button(
            f"Install GPU Drivers ({self.gpu_display_name})",
            desc
        )
        self.chk_gpu_drivers.set_active(False)  # Opt-in by default
        self.chk_gpu_drivers.connect("toggled", self.on_gpu_drivers_toggled)
        content_box.append(self.chk_gpu_drivers)

        scrolled.set_child(content_box)
        page.append(scrolled)
        self.stack.add_named(page, "page_drivers")

    def on_gpu_drivers_toggled(self, btn):
        self.install_gpu_drivers = btn.get_active()

    # -------------------------------------------------------------
    # Page 2: Browser Selection
    # -------------------------------------------------------------
    def build_browser_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Choose a primary web browser to install:</b>\n<span size='small' alpha='65%'>Select one from the options below, or search the repositories.</span>")
        page.append(info)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        radio_box.set_margin_top(8)
        radio_box.set_margin_bottom(8)

        self.browser_radios = {}
        first_b = None

        for bid, title, desc in BROWSERS:
            r = make_check_button(title, desc, group=first_b)
            if first_b is None:
                first_b = r
                r.set_active(True)
            self.browser_radios[bid] = r
            radio_box.append(r)

        # "Other" search section embedded
        self.other_search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.other_search_box.set_margin_top(8)
        self.other_search_box.set_margin_start(28)
        self.other_search_box.set_visible(False)

        search_entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.browser_search_entry = Gtk.Entry()
        self.browser_search_entry.set_placeholder_text("Enter browser package name (e.g. librewolf, floorp)...")
        self.browser_search_entry.set_hexpand(True)
        self.browser_search_entry.connect("activate", self.on_search_browser)

        btn_search_b = Gtk.Button(label="Search Repos")
        btn_search_b.connect("clicked", self.on_search_browser)

        search_entry_box.append(self.browser_search_entry)
        search_entry_box.append(btn_search_b)
        self.other_search_box.append(search_entry_box)

        self.browser_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.other_search_box.append(self.browser_results_box)

        radio_box.append(self.other_search_box)

        # Connect "Other" radio button toggle
        self.browser_radios["other"].connect("toggled", self.on_browser_other_toggled)

        scrolled.set_child(radio_box)
        page.append(scrolled)
        self.stack.add_named(page, "page_browser")

    def on_browser_other_toggled(self, btn):
        self.other_search_box.set_visible(btn.get_active())

    def on_search_browser(self, widget):
        query = self.browser_search_entry.get_text().strip()
        if not query:
            return

        while child := self.browser_results_box.get_first_child():
            self.browser_results_box.remove(child)

        lbl = Gtk.Label(label="Searching repositories...")
        self.browser_results_box.append(lbl)

        def search_thread():
            try:
                cmd = f"yay -Slq | grep -i '{query}' | head -n 25 | sort -u"
                res = subprocess.check_output(cmd, shell=True, text=True).splitlines()
            except Exception:
                res = []

            def update_ui():
                while child := self.browser_results_box.get_first_child():
                    self.browser_results_box.remove(child)
                if not res:
                    self.browser_results_box.append(Gtk.Label(label=f"No packages found for '{query}'."))
                    return

                res_label = Gtk.Label()
                res_label.set_markup("<b>Search Results (Click to select):</b>")
                res_label.set_halign(Gtk.Align.START)
                self.browser_results_box.append(res_label)

                first_r = None
                self.custom_browser_radios = []
                for pkg in res:
                    rb = make_check_button(pkg, group=first_r)
                    if first_r is None:
                        first_r = rb
                        rb.set_active(True)
                    self.custom_browser_radios.append((pkg, rb))
                    self.browser_results_box.append(rb)

            GLib.idle_add(update_ui)

        threading.Thread(target=search_thread, daemon=True).start()

    # -------------------------------------------------------------
    # Step 3: Browser Extensions
    # -------------------------------------------------------------
    def build_extensions_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Select curated browser extensions to provision:</b>\n<span size='small' alpha='65%'>Automatically pre-configured for your chosen browser (Brave, Chromium, Firefox, etc.). Extensions will be ready when you launch the browser.</span>")
        page.append(info)

        # Top bar with Master Select All / Unselect All
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        top_bar.set_margin_top(6)
        top_bar.set_margin_bottom(8)

        self.extensions_master_select_all = make_check_button("Select / Unselect All Extensions")
        self.extensions_master_select_all.set_active(True)
        self.extensions_master_select_all.connect("toggled", self.on_master_extensions_toggled)
        top_bar.append(self.extensions_master_select_all)
        page.append(top_bar)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        grid = Gtk.Grid()
        grid.set_column_spacing(24)
        grid.set_row_spacing(12)
        grid.set_margin_top(8)
        grid.set_margin_bottom(12)
        grid.set_margin_start(8)
        grid.set_margin_end(8)

        self.extensions_checkboxes = {}
        self.ext_selection_updating = False

        half = (len(BROWSER_EXTENSIONS) + 1) // 2
        for idx, (ext_id, name, desc, _, _, _, default_active) in enumerate(BROWSER_EXTENSIONS):
            c = make_check_button(name, desc)
            c.set_active(default_active)
            c.connect("toggled", lambda b, e=ext_id: self.on_extension_toggled(b, e))
            self.extensions_checkboxes[ext_id] = c

            col = 0 if idx < half else 1
            row = idx if idx < half else idx - half
            grid.attach(c, col, row, 1, 1)

        scrolled.set_child(grid)
        page.append(scrolled)
        self.stack.add_named(page, "page_extensions")

    def on_master_extensions_toggled(self, btn):
        if getattr(self, "ext_selection_updating", False):
            return
        self.ext_selection_updating = True
        active = btn.get_active()
        for ext_id, chk in self.extensions_checkboxes.items():
            chk.set_active(active)
            if active:
                self.selected_extensions.add(ext_id)
            else:
                self.selected_extensions.discard(ext_id)
        self.ext_selection_updating = False

    def on_extension_toggled(self, btn, ext_id):
        if btn.get_active():
            self.selected_extensions.add(ext_id)
        else:
            self.selected_extensions.discard(ext_id)

        if not getattr(self, "ext_selection_updating", False):
            self.ext_selection_updating = True
            all_active = all(chk.get_active() for chk in self.extensions_checkboxes.values())
            self.extensions_master_select_all.set_active(all_active)
            self.ext_selection_updating = False

    # -------------------------------------------------------------
    # Page 4: Application Selection (with Extra AUR Search at bottom)
    # -------------------------------------------------------------
    def build_apps_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Select applications, emulators, and tools to install:</b>\n<span size='small' alpha='65%'>Organized by category. You can tick an entire category or select individual items.</span>")
        page.append(info)

        # Top bar with Master Select All tick box + filter search entry
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        top_bar.set_margin_top(6)
        top_bar.set_margin_bottom(8)

        self.apps_master_select_all = make_check_button("Select / Unselect All Applications")
        self.apps_master_select_all.set_active(False)
        self.apps_master_select_all.connect("toggled", self.on_master_select_all_toggled)
        top_bar.append(self.apps_master_select_all)

        # Generic, clean placeholder
        self.filter_entry = Gtk.SearchEntry()
        self.filter_entry.set_placeholder_text("Search applications (e.g. steam, vlc, discord, spotify)...")
        self.filter_entry.set_hexpand(True)
        self.filter_entry.connect("search-changed", self.on_filter_changed)
        top_bar.append(self.filter_entry)

        page.append(top_bar)

        # Scrolled container for categorized sections and bottom AUR search
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        categories_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        categories_container.set_margin_top(6)
        categories_container.set_margin_bottom(14)
        categories_container.set_margin_start(4)
        categories_container.set_margin_end(4)

        self.category_groups = []
        self.apps_checkboxes = {}
        self.selection_updating = False

        categories = get_categorized_apps()

        for cat_name, items in categories:
            cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

            # Category Header with its own Select-Whole-Category Checkbox
            cat_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            cat_check = make_check_button(cat_name)
            cat_check.set_active(False)
            cat_check.add_css_class("heading")
            cat_header_box.append(cat_check)
            cat_box.append(cat_header_box)

            cat_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            cat_box.append(cat_sep)

            # 2-column grid for this category
            grid = Gtk.Grid()
            grid.set_column_spacing(24)
            grid.set_row_spacing(10)
            grid.set_margin_top(4)
            grid.set_margin_bottom(8)
            grid.set_margin_start(16)

            cat_item_buttons = []
            half = (len(items) + 1) // 2
            for idx, (pkg, name, desc) in enumerate(items):
                c = make_check_button(name, desc)
                c.set_active(False)
                c.connect("toggled", lambda b, cn=cat_name: self.on_app_item_toggled(b, cn))
                self.apps_checkboxes[pkg] = (c, name, desc, cat_name)
                cat_item_buttons.append((pkg, c))

                col = 0 if idx < half else 1
                row = idx if idx < half else idx - half
                grid.attach(c, col, row, 1, 1)

            # Connect category checkbox to toggle the whole category
            cat_check.connect("toggled", lambda b, buttons=cat_item_buttons: self.on_category_toggled(b, buttons))

            cat_box.append(grid)
            categories_container.append(cat_box)
            self.category_groups.append((cat_box, cat_name, cat_check, cat_item_buttons))

        # -------------------------------------------------------------
        # Extra Packages (AUR Search) - Bottom of Package Selection
        # -------------------------------------------------------------
        aur_sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        aur_sep.set_margin_top(16)
        aur_sep.set_margin_bottom(10)
        categories_container.append(aur_sep)

        aur_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        aur_box.set_margin_start(4)
        aur_box.set_margin_end(4)
        aur_box.set_margin_bottom(16)

        aur_title = Gtk.Label()
        aur_title.set_halign(Gtk.Align.START)
        aur_title.set_markup("<span size='medium' weight='bold'>Extra Packages (Search Repositories / AUR)</span>")
        aur_box.append(aur_title)

        aur_desc = Gtk.Label()
        aur_desc.set_halign(Gtk.Align.START)
        aur_desc.set_markup("<span size='small' alpha='65%'>Can't find a package above? Search the Arch User Repository or enter package names directly to add them to your installation queue.</span>")
        aur_box.append(aur_desc)

        # Search / Add row
        search_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        search_row.set_margin_top(4)

        self.aur_search_entry = Gtk.Entry()
        self.aur_search_entry.set_placeholder_text("Search AUR packages (e.g. visual-studio-code-bin, obs-studio)...")
        self.aur_search_entry.set_hexpand(True)
        self.aur_search_entry.connect("activate", self.on_search_aur)
        search_row.append(self.aur_search_entry)

        btn_aur_search = Gtk.Button(label="Search AUR")
        btn_aur_search.connect("clicked", self.on_search_aur)
        search_row.append(btn_aur_search)

        self.manual_pkg_entry = Gtk.Entry()
        self.manual_pkg_entry.set_placeholder_text("Manual package name...")
        self.manual_pkg_entry.set_size_request(210, -1)
        self.manual_pkg_entry.connect("activate", self.on_manual_add)
        search_row.append(self.manual_pkg_entry)

        btn_manual_add = Gtk.Button(label="+ Add")
        btn_manual_add.connect("clicked", self.on_manual_add)
        search_row.append(btn_manual_add)

        aur_box.append(search_row)

        # Live AUR search results container (shown when search is made)
        self.aur_results_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.aur_results_frame.set_margin_top(6)
        self.aur_results_frame.set_visible(False)

        res_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl_res = Gtk.Label()
        lbl_res.set_markup("<b>AUR Search Results (Click checkbox to queue):</b>")
        lbl_res.set_hexpand(True)
        lbl_res.set_halign(Gtk.Align.START)
        res_header_box.append(lbl_res)

        btn_add_selected = Gtk.Button(label="+ Add Checked to Queue")
        btn_add_selected.add_css_class("suggested-action")
        btn_add_selected.connect("clicked", self.on_add_checked_aur)
        res_header_box.append(btn_add_selected)

        btn_close_res = Gtk.Button(label="Close")
        btn_close_res.connect("clicked", lambda _: self.aur_results_frame.set_visible(False))
        res_header_box.append(btn_close_res)

        self.aur_results_frame.append(res_header_box)

        # Scrolled flow/list for search results
        self.aur_results_scroll = Gtk.ScrolledWindow()
        self.aur_results_scroll.set_size_request(-1, 150)
        self.aur_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.aur_results_box.set_margin_top(4)
        self.aur_results_box.set_margin_bottom(4)
        self.aur_results_scroll.set_child(self.aur_results_box)
        self.aur_results_frame.append(self.aur_results_scroll)

        aur_box.append(self.aur_results_frame)

        # Queued packages display
        self.queued_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.queued_frame.set_margin_top(6)

        queue_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.queued_count_label = Gtk.Label()
        self.queued_count_label.set_markup("<b>Queued Extra Packages (0):</b>")
        self.queued_count_label.set_hexpand(True)
        self.queued_count_label.set_halign(Gtk.Align.START)
        queue_header_box.append(self.queued_count_label)

        btn_clear = Gtk.Button(label="Clear Queue")
        btn_clear.connect("clicked", self.on_clear_queue)
        queue_header_box.append(btn_clear)
        self.queued_frame.append(queue_header_box)

        self.queue_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.queue_list_box.set_margin_top(4)
        self.queued_frame.append(self.queue_list_box)

        aur_box.append(self.queued_frame)
        categories_container.append(aur_box)

        scrolled.set_child(categories_container)
        page.append(scrolled)
        self.stack.add_named(page, "page_apps")

        # Initial queue UI update
        self.update_queue_ui()

    def on_master_select_all_toggled(self, btn):
        if self.selection_updating:
            return
        self.selection_updating = True
        state = btn.get_active()
        for cat_box, cat_name, cat_check, cat_item_buttons in self.category_groups:
            if cat_box.get_visible():
                cat_check.set_active(state)
                for pkg, c in cat_item_buttons:
                    if c.get_visible():
                        c.set_active(state)
        self.selection_updating = False

    def on_category_toggled(self, cat_btn, cat_item_buttons):
        if self.selection_updating:
            return
        self.selection_updating = True
        state = cat_btn.get_active()
        for pkg, c in cat_item_buttons:
            if c.get_visible():
                c.set_active(state)
        
        # Update master checkbox status
        visible_boxes = [c for c, _, _, _ in self.apps_checkboxes.values() if c.get_visible()]
        all_checked = all(c.get_active() for c in visible_boxes) if visible_boxes else False
        self.apps_master_select_all.set_active(all_checked)
        self.selection_updating = False

    def on_app_item_toggled(self, btn, cat_name):
        if self.selection_updating:
            return
        self.selection_updating = True

        for cat_box, name, cat_check, cat_item_buttons in self.category_groups:
            if name == cat_name:
                vis_items = [c for pkg, c in cat_item_buttons if c.get_visible()]
                cat_all = all(c.get_active() for c in vis_items) if vis_items else False
                cat_check.set_active(cat_all)
                break

        visible_boxes = [c for c, _, _, _ in self.apps_checkboxes.values() if c.get_visible()]
        all_checked = all(c.get_active() for c in visible_boxes) if visible_boxes else False
        self.apps_master_select_all.set_active(all_checked)
        self.selection_updating = False

    def on_filter_changed(self, entry):
        term = entry.get_text().strip().lower()
        for cat_box, cat_name, cat_check, cat_item_buttons in self.category_groups:
            any_cat_match = False
            for pkg, c in cat_item_buttons:
                _, name, desc, _ = self.apps_checkboxes[pkg]
                matches = (term in pkg.lower()) or (term in name.lower()) or (term in desc.lower()) or (term in cat_name.lower())
                c.set_visible(matches if term else True)
                if matches:
                    any_cat_match = True
            cat_box.set_visible(any_cat_match if term else True)

    def on_search_aur(self, widget):
        query = self.aur_search_entry.get_text().strip()
        if not query:
            return

        self.aur_results_frame.set_visible(True)
        while child := self.aur_results_box.get_first_child():
            self.aur_results_box.remove(child)

        lbl = Gtk.Label(label="Searching AUR...")
        self.aur_results_box.append(lbl)

        def thread_task():
            try:
                cmd = f"yay -Slqa | grep -i '{query}' | head -n 30"
                pkgs = subprocess.check_output(cmd, shell=True, text=True).splitlines()
            except Exception:
                pkgs = []

            def update_ui():
                while child := self.aur_results_box.get_first_child():
                    self.aur_results_box.remove(child)
                self.aur_check_items = []
                if not pkgs:
                    self.aur_results_box.append(Gtk.Label(label=f"No AUR packages found for '{query}'."))
                    return

                for p in pkgs:
                    p = p.strip()
                    if not p:
                        continue
                    chk = make_check_button(p)
                    self.aur_check_items.append((p, chk))
                    self.aur_results_box.append(chk)

            GLib.idle_add(update_ui)

        threading.Thread(target=thread_task, daemon=True).start()

    def on_add_checked_aur(self, widget):
        if not hasattr(self, "aur_check_items"):
            return
        for pkg, chk in self.aur_check_items:
            if chk.get_active():
                self.queued_aur.add(pkg)
                chk.set_active(False)
        self.update_queue_ui()
        self.aur_results_frame.set_visible(False)

    def on_manual_add(self, widget):
        text = self.manual_pkg_entry.get_text().strip()
        for p in text.split():
            if p:
                self.queued_aur.add(p)
        self.manual_pkg_entry.set_text("")
        self.update_queue_ui()

    def on_clear_queue(self, widget):
        self.queued_aur.clear()
        self.update_queue_ui()

    def update_queue_ui(self):
        while child := self.queue_list_box.get_first_child():
            self.queue_list_box.remove(child)

        self.queued_count_label.set_markup(f"<b>Queued Extra Packages ({len(self.queued_aur)}):</b>")

        if not self.queued_aur:
            self.queue_list_box.append(Gtk.Label(label="   No extra packages queued."))
            return

        for p in sorted(self.queued_aur):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            lbl = Gtk.Label(label=f"• {p}")
            lbl.set_hexpand(True)
            lbl.set_halign(Gtk.Align.START)

            btn_del = Gtk.Button(label="Remove")
            btn_del.set_tooltip_text(f"Remove {p}")
            btn_del.connect("clicked", lambda _, pkg_name=p: self.remove_queued_pkg(pkg_name))

            row.append(lbl)
            row.append(btn_del)
            self.queue_list_box.append(row)

    def remove_queued_pkg(self, pkg):
        self.queued_aur.discard(pkg)
        self.update_queue_ui()

    # -------------------------------------------------------------
    # Page 3: Flatpak Applications
    # -------------------------------------------------------------
    def build_flatpaks_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Select Flatpak applications to install:</b>\n<span size='small' alpha='65%'>Sandboxed software packages from Flathub. Flathub will be automatically configured.</span>")
        page.append(info)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_margin_start(8)
        content_box.set_margin_end(8)

        self.flatpak_checkboxes = {}
        for pkg_id, name, desc, default_active in FLATPAK_APPS:
            chk = make_check_button(name, desc)
            chk.set_active(default_active)
            chk.connect("toggled", lambda b, p=pkg_id: self.on_flatpak_toggled(b, p))
            self.flatpak_checkboxes[pkg_id] = chk
            content_box.append(chk)

        scrolled.set_child(content_box)
        page.append(scrolled)
        self.stack.add_named(page, "page_flatpaks")

    def on_flatpak_toggled(self, btn, pkg_id):
        if btn.get_active():
            self.selected_flatpaks.add(pkg_id)
        else:
            self.selected_flatpaks.discard(pkg_id)

    # -------------------------------------------------------------
    # Step 4: Custom Setup & Management Scripts
    # -------------------------------------------------------------
    def build_scripts_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Select custom setup and management scripts to install (Optional):</b>\n<span size='small' alpha='65%'>Standalone helper tools and utility managers that can be launched from the terminal or application menu. All scripts are opt-in.</span>")
        page.append(info)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_margin_start(8)
        content_box.set_margin_end(8)

        self.scripts_checkboxes = {}
        for script_id, name, desc, default_active in SCRIPTS:
            chk = make_check_button(name, desc)
            chk.set_active(default_active)
            chk.connect("toggled", lambda b, s=script_id: self.on_script_toggled(b, s))
            self.scripts_checkboxes[script_id] = chk
            content_box.append(chk)

        scrolled.set_child(content_box)
        page.append(scrolled)
        self.stack.add_named(page, "page_scripts")

    def on_script_toggled(self, btn, script_id):
        if btn.get_active():
            self.selected_scripts.add(script_id)
        else:
            self.selected_scripts.discard(script_id)

    # -------------------------------------------------------------
    # Step 5: Summary & Confirmation
    # -------------------------------------------------------------
    def build_summary_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_margin_top(8)

        info = Gtk.Label()
        info.set_halign(Gtk.Align.START)
        info.set_markup("<b>Installation Plan Summary:</b>\n<span size='small' alpha='65%'>Review your selections below. Click 'Install Now' to proceed, or 'Previous' to adjust anything.</span>")
        page.append(info)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.summary_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.summary_content_box.set_margin_top(8)
        self.summary_content_box.set_margin_bottom(8)

        scrolled.set_child(self.summary_content_box)
        page.append(scrolled)
        self.stack.add_named(page, "page_summary")

    def update_summary_content(self):
        while child := self.summary_content_box.get_first_child():
            self.summary_content_box.remove(child)

        self.save_current_step_state()

        def add_card(title, content_list):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.set_margin_bottom(6)

            header = Gtk.Label()
            header.set_halign(Gtk.Align.START)
            safe_title = GLib.markup_escape_text(title)
            header.set_markup(f"<b>{safe_title}</b>")
            card.append(header)

            if isinstance(content_list, (list, set)):
                items = sorted(list(content_list))
                if not items:
                    item_lbl = Gtk.Label(label="   None selected (Skipped)")
                    item_lbl.set_halign(Gtk.Align.START)
                    card.append(item_lbl)
                else:
                    item_lbl = Gtk.Label(label="   " + ", ".join(items))
                    item_lbl.set_wrap(True)
                    item_lbl.set_halign(Gtk.Align.START)
                    card.append(item_lbl)
            else:
                item_lbl = Gtk.Label(label=f"   {content_list}")
                item_lbl.set_halign(Gtk.Align.START)
                card.append(item_lbl)

            self.summary_content_box.append(card)

        # GPU summary (Auto-detected hardware)
        if self.install_gpu_drivers and self.detected_gpu_pkgs:
            add_card("GPU Drivers (Opted In)", f"{self.gpu_display_name}\n   Driver packages: {', '.join(self.detected_gpu_pkgs)}")
        else:
            add_card("GPU Drivers", f"{self.gpu_display_name}\n   Status: Skipped (Not opted in)")

        # Browser summary
        add_card("Web Browser", self.selected_browser if self.selected_browser else "Skipped")

        # Browser Extensions summary
        ext_names = [name for ext_id, name, _, _, _, _, _ in BROWSER_EXTENSIONS if ext_id in self.selected_extensions]
        add_card(f"Browser Extensions ({len(self.selected_extensions)})", ext_names)

        # Applications vs Emulators breakdown
        selected_main = sorted([pkg for pkg in self.selected_apps if pkg not in EMULATOR_PKGS_SET])
        selected_emus = sorted([pkg for pkg in self.selected_apps if pkg in EMULATOR_PKGS_SET])

        annotated_main = []
        de = get_desktop_environment()
        for item in selected_main:
            if item == "goverlay":
                annotated_main.append("goverlay (+ mesa-utils & preview tools)")
            elif item == "waywallen":
                plugin = "plasma-wallpaper-waywallen" if de == "kde" else "gnome-shell-extension-waywallen"
                annotated_main.append(f"waywallen (+ waywallen-display, {plugin})")
            else:
                annotated_main.append(item)
        add_card(f"Applications & Tools ({len(selected_main)})", annotated_main)

        add_card(f"Emulators ({len(selected_emus)})", selected_emus)

        # Flatpaks summary
        flatpak_display = []
        for p in self.selected_flatpaks:
            if p == "com.dec05eba.gpu_screen_recorder":
                flatpak_display.append("GPU Screen Recorder (GSR)")
            else:
                flatpak_display.append(p)
        add_card(f"Flatpak Applications ({len(self.selected_flatpaks)})", flatpak_display)

        # Custom Scripts summary
        scripts_display = []
        for s in sorted(list(self.selected_scripts)):
            if s == "slssteam":
                scripts_display.append("SLSsteam Manager (slssteam)")
            elif s == "vencord":
                scripts_display.append("Vencord Discord Mod (vencord)")
            elif s == "fix-ntfs":
                scripts_display.append("NTFS Disk Repair & Auto-Mounter (fix-ntfs)")
            else:
                scripts_display.append(s)
        add_card(f"Setup Scripts ({len(self.selected_scripts)})", scripts_display)

        # Extra AUR apps summary
        add_card(f"Custom AUR Packages ({len(self.queued_aur)})", sorted(self.queued_aur))

        # Core summary
        core_summary = "Flatpak"
        if de == "kde":
            core_summary += ", Plasma Browser Integration"
        add_card("Core System", core_summary)

    # -------------------------------------------------------------
    # Live Descriptive Progress Screen
    # -------------------------------------------------------------
    def build_progress_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        page.set_margin_top(8)

        # Status Card Box
        status_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        status_card.set_margin_top(6)
        status_card.set_margin_bottom(6)

        self.install_spinner = Gtk.Spinner()
        self.install_spinner.set_spinning(True)
        self.install_spinner.set_size_request(32, 32)
        self.install_spinner.set_valign(Gtk.Align.CENTER)
        status_card.append(self.install_spinner)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        text_box.set_hexpand(True)
        text_box.set_halign(Gtk.Align.START)

        self.install_step_title = Gtk.Label()
        self.install_step_title.set_markup("<span size='large' weight='bold'>Preparing Installation...</span>")
        self.install_step_title.set_halign(Gtk.Align.START)
        text_box.append(self.install_step_title)

        self.install_step_desc = Gtk.Label()
        self.install_step_desc.set_markup("<span size='small' alpha='65%'>Initializing package queues and configuration...</span>")
        self.install_step_desc.set_halign(Gtk.Align.START)
        self.install_step_desc.set_wrap(True)
        text_box.append(self.install_step_desc)

        status_card.append(text_box)
        page.append(status_card)

        # Descriptive Progress Bar
        self.install_prog_bar = Gtk.ProgressBar()
        self.install_prog_bar.set_fraction(0.0)
        self.install_prog_bar.set_show_text(True)
        self.install_prog_bar.set_text("0% - Starting")
        self.install_prog_bar.add_css_class("large-progress")
        self.install_prog_bar.set_margin_top(4)
        self.install_prog_bar.set_margin_bottom(8)
        page.append(self.install_prog_bar)

        # Log Section Header
        log_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_log = Gtk.Label()
        lbl_log.set_markup("<b>Live Installation Output:</b>")
        lbl_log.set_hexpand(True)
        lbl_log.set_halign(Gtk.Align.START)
        log_header.append(lbl_log)

        self.log_autoscroll = Gtk.CheckButton(label="Auto-scroll")
        self.log_autoscroll.set_active(True)
        log_header.append(self.log_autoscroll)
        page.append(log_header)

        # Scrolled Text View for Terminal Output
        scrolled_log = Gtk.ScrolledWindow()
        scrolled_log.set_vexpand(True)
        scrolled_log.set_hexpand(True)
        scrolled_log.set_size_request(-1, 280)

        self.log_text_view = Gtk.TextView()
        self.log_text_view.set_editable(False)
        self.log_text_view.set_cursor_visible(False)
        self.log_text_view.set_monospace(True)
        self.log_text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.log_text_view.add_css_class("log-viewer")
        self.log_text_view.set_left_margin(12)
        self.log_text_view.set_right_margin(12)
        self.log_text_view.set_top_margin(10)
        self.log_text_view.set_bottom_margin(10)

        self.log_buffer = self.log_text_view.get_buffer()
        scrolled_log.set_child(self.log_text_view)
        page.append(scrolled_log)

        self.stack.add_named(page, "page_progress")

    # -------------------------------------------------------------
    # Navigation Logic (Previous / Skip / Next)
    # -------------------------------------------------------------
    def save_current_step_state(self):
        if self.current_step == 0:
            self.install_gpu_drivers = self.chk_gpu_drivers.get_active()

        elif self.current_step == 1:
            for bid, r in self.browser_radios.items():
                if r.get_active():
                    if bid == "other":
                        chosen = None
                        if hasattr(self, "custom_browser_radios"):
                            for pkg, rb in self.custom_browser_radios:
                                if rb.get_active():
                                    chosen = pkg
                                    break
                        if not chosen:
                            chosen = self.browser_search_entry.get_text().strip()
                        self.selected_browser = chosen if chosen else ""
                    else:
                        self.selected_browser = bid
                    break

        elif self.current_step == 2:
            self.selected_extensions = {
                ext_id for ext_id, chk in self.extensions_checkboxes.items() if chk.get_active()
            }

        elif self.current_step == 3:
            self.selected_apps = {
                pkg for pkg, (c, _, _, _) in self.apps_checkboxes.items() if c.get_active()
            }

        elif self.current_step == 4:
            self.selected_flatpaks = {
                pkg for pkg, chk in self.flatpak_checkboxes.items() if chk.get_active()
            }

        elif self.current_step == 5:
            self.selected_scripts = {
                s_id for s_id, chk in self.scripts_checkboxes.items() if chk.get_active()
            }

    def update_step_view(self):
        page_names = ["page_drivers", "page_browser", "page_extensions", "page_apps", "page_flatpaks", "page_scripts", "page_summary"]
        self.stack.set_visible_child_name(page_names[self.current_step])

        # Progress bar
        self.wizard_prog_bar.set_fraction((self.current_step + 1) / self.total_steps)

        # Update step titles (6 main configuration steps + summary)
        step_titles = [
            "GPU Driver Selection (Step 1/6)",
            "Browser Selection (Step 2/6)",
            "Browser Extensions (Step 3/6)",
            "Application Selection (Step 4/6)",
            "Flatpak Applications (Step 5/6)",
            "Setup Scripts (Step 6/6)",
            "Installation Plan Summary",
        ]
        self.title_label.set_markup(f"<span size='x-large' weight='bold'>{step_titles[self.current_step]}</span>")

        # Previous disabled on step 0
        self.btn_prev.set_sensitive(self.current_step > 0)

        # Last page (Summary):
        if self.current_step == 6:
            self.btn_skip.set_label("Abort Setup")
            self.btn_next.set_label("Install Now")
            self.btn_next.remove_css_class("suggested-action")
            self.btn_next.add_css_class("suggested-action")
            self.update_summary_content()
        else:
            self.btn_skip.set_label("Skip Step")
            self.btn_next.set_label("Next")

    def on_halt_clicked(self, widget):
        self.get_application().quit()
        sys.exit(1)

    def on_window_close_request(self, win):
        self.get_application().quit()
        sys.exit(1)

    def on_prev_clicked(self, btn):
        if self.current_step > 0:
            self.save_current_step_state()
            self.current_step -= 1
            self.update_step_view()

    def on_skip_clicked(self, btn):
        if self.current_step == 6:
            # Abort on summary page
            self.get_application().quit()
            sys.exit(1)

        # Skip current step selections
        if self.current_step == 0:
            self.chk_gpu_drivers.set_active(False)
            self.install_gpu_drivers = False
        elif self.current_step == 1:
            self.selected_browser = ""
        elif self.current_step == 2:
            self.selected_extensions.clear()
            for chk in self.extensions_checkboxes.values():
                chk.set_active(False)
            self.extensions_master_select_all.set_active(False)
        elif self.current_step == 3:
            self.selected_apps.clear()
            for c, _, _, _ in self.apps_checkboxes.values():
                c.set_active(False)
            for _, _, cat_check, _ in self.category_groups:
                cat_check.set_active(False)
            self.apps_master_select_all.set_active(False)
            self.queued_aur.clear()
            self.update_queue_ui()
        elif self.current_step == 4:
            self.selected_flatpaks.clear()
            for chk in self.flatpak_checkboxes.values():
                chk.set_active(False)
        elif self.current_step == 5:
            self.selected_scripts.clear()
            for chk in self.scripts_checkboxes.values():
                chk.set_active(False)

        self.current_step += 1
        self.update_step_view()

    def on_next_clicked(self, btn):
        self.save_current_step_state()

        if self.current_step == 6:
            self.start_installation()
        else:
            self.current_step += 1
            self.update_step_view()
            self.update_step_view()

    def write_config_file(self):
        browser_pkgs = [self.selected_browser] if self.selected_browser else []

        selected_emus = sorted([pkg for pkg in self.selected_apps if pkg in EMULATOR_PKGS_SET])
        main_pkgs_list = sorted([pkg for pkg in self.selected_apps if pkg not in EMULATOR_PKGS_SET])
        extra_aur_list = sorted(self.queued_aur)

        # Goverlay auto-installation of requirements:
        if "goverlay" in main_pkgs_list:
            if "mesa-utils" not in main_pkgs_list:
                main_pkgs_list.append("mesa-utils")

        # Waywallen auto-installation of requirements & DE integration:
        if "waywallen" in main_pkgs_list:
            if "waywallen-display" not in extra_aur_list and "waywallen-display" not in main_pkgs_list:
                extra_aur_list.append("waywallen-display")
            de = get_desktop_environment()
            if de == "kde":
                plugin = "plasma-wallpaper-waywallen"
                if plugin not in extra_aur_list and plugin not in main_pkgs_list:
                    extra_aur_list.append(plugin)
            elif de == "gnome":
                plugin = "gnome-shell-extension-waywallen"
                if plugin not in extra_aur_list and plugin not in main_pkgs_list:
                    extra_aur_list.append(plugin)

        # If no browser was selected (skipped), extensions shouldn't be installed
        effective_extensions = sorted(list(self.selected_extensions)) if browser_pkgs else []

        data = {
            "gpu": self.gpu_display_name if self.install_gpu_drivers else "skip",
            "gpu_pkgs": self.detected_gpu_pkgs if self.install_gpu_drivers else [],
            "browser_pkg": browser_pkgs,
            "browser_extensions": effective_extensions,
            "emu_pkgs": selected_emus,
            "main_pkgs": main_pkgs_list,
            "flatpak_pkgs": sorted(self.selected_flatpaks),
            "script_pkgs": sorted(self.selected_scripts),
            "aur_pkgs": extra_aur_list,
        }

        try:
            with open(self.output_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error writing config: {e}", file=sys.stderr)

    def start_installation(self):
        # 1. Write the configuration JSON file for CLASS.sh
        self.write_config_file()

        # If running in standalone test mode without a status-file argument
        if not self.status_file:
            self.get_application().quit()
            sys.exit(0)

        # 2. Replace the wizard with the descriptive progress bar screen!
        self.is_installing = True
        self.wizard_prog_bar.set_visible(False)
        self.btn_halt.set_visible(False)

        self.title_label.set_markup("<span size='x-large' weight='bold'>Installing System Configuration</span>")
        self.subtitle_label.set_markup("<span size='small' alpha='65%'>Executing installation tasks. Please do not close this window.</span>")

        # Configure navigation bar for installation mode
        self.btn_prev.set_visible(False)
        self.btn_skip.set_visible(False)
        self.btn_next.set_label("Installing...")
        self.btn_next.set_sensitive(False)

        # Switch to the progress screen
        self.stack.set_visible_child_name("page_progress")

        # Set up log tracking
        self.log_file_path = os.path.expanduser("~/class-install.log")
        self.log_file_offset = 0
        if os.path.exists(self.log_file_path):
            try:
                self.log_file_offset = os.path.getsize(self.log_file_path)
            except Exception:
                self.log_file_offset = 0

        # Start background polling timer (every 150ms)
        GLib.timeout_add(150, self.on_poll_install_progress)

    def on_poll_install_progress(self):
        # 1. Read status file if available
        if self.status_file and os.path.exists(self.status_file):
            try:
                with open(self.status_file, "r") as f:
                    data = json.load(f)

                percent = float(data.get("percent", 0.0))
                title = data.get("title", "")
                desc = data.get("desc", "")
                status = data.get("status", "running")

                self.install_prog_bar.set_fraction(max(0.0, min(1.0, percent)))
                pct_str = f"{int(percent * 100)}%"
                self.install_prog_bar.set_text(f"{pct_str} - {title}" if title else pct_str)

                safe_title = GLib.markup_escape_text(title)
                safe_desc = GLib.markup_escape_text(desc)
                self.install_step_title.set_markup(f"<span size='large' weight='bold'>{safe_title}</span>")
                self.install_step_desc.set_markup(f"<span size='small' alpha='65%'>{safe_desc}</span>")

                if status == "complete":
                    self.on_installation_complete()
                    return GLib.SOURCE_REMOVE
                elif status == "error":
                    self.on_installation_error(desc)
                    return GLib.SOURCE_REMOVE
            except Exception:
                pass

        # 2. Tail log file to display real-time terminal output
        if os.path.exists(self.log_file_path):
            try:
                curr_size = os.path.getsize(self.log_file_path)
                if curr_size > self.log_file_offset:
                    with open(self.log_file_path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(self.log_file_offset)
                        new_content = f.read()
                        self.log_file_offset = f.tell()

                    end_iter = self.log_buffer.get_end_iter()
                    self.log_buffer.insert(end_iter, new_content)

                    if self.log_autoscroll.get_active():
                        end_mark = self.log_buffer.create_mark(None, self.log_buffer.get_end_iter(), False)
                        self.log_text_view.scroll_to_mark(end_mark, 0.0, True, 0.0, 1.0)
            except Exception:
                pass

        return GLib.SOURCE_CONTINUE

    def on_installation_complete(self):
        # Final tail of log
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self.log_file_offset)
                    new_content = f.read()
                    if new_content:
                        end_iter = self.log_buffer.get_end_iter()
                        self.log_buffer.insert(end_iter, new_content)
        except Exception:
            pass

        self.install_spinner.set_spinning(False)
        self.install_spinner.set_visible(False)
        self.install_step_title.set_markup("<span size='large' weight='bold' foreground='#2ecc71'>Installation Complete!</span>")
        self.install_step_desc.set_markup("<span size='small' alpha='65%'>All requested packages and configurations have been deployed successfully.</span>")
        self.install_prog_bar.set_fraction(1.0)
        self.install_prog_bar.set_text("100% - Setup Complete")

        # Configure action buttons
        self.btn_prev.set_label("Reboot System")
        self.btn_prev.remove_css_class("suggested-action")
        self.btn_prev.add_css_class("destructive-action")
        self.btn_prev.set_visible(True)
        self.btn_prev.set_sensitive(True)
        try:
            self.btn_prev.disconnect_by_func(self.on_prev_clicked)
        except Exception:
            pass
        self.btn_prev.connect("clicked", self.on_reboot_clicked)

        self.btn_next.set_label("Finish & Close")
        self.btn_next.remove_css_class("suggested-action")
        self.btn_next.add_css_class("suggested-action")
        self.btn_next.set_visible(True)
        self.btn_next.set_sensitive(True)
        try:
            self.btn_next.disconnect_by_func(self.on_next_clicked)
        except Exception:
            pass
        self.btn_next.connect("clicked", self.on_finish_clicked)

    def on_installation_error(self, err_msg):
        self.install_spinner.set_spinning(False)
        self.install_spinner.set_visible(False)
        self.install_step_title.set_markup("<span size='large' weight='bold' foreground='#e74c3c'>Installation Finished with Warnings/Errors</span>")
        self.install_step_desc.set_markup(f"<span size='small' alpha='65%'>{GLib.markup_escape_text(err_msg)}</span>")

        self.btn_next.set_label("Close")
        self.btn_next.set_visible(True)
        self.btn_next.set_sensitive(True)
        try:
            self.btn_next.disconnect_by_func(self.on_next_clicked)
        except Exception:
            pass
        self.btn_next.connect("clicked", self.on_finish_clicked)

    def on_reboot_clicked(self, widget):
        self.get_application().quit()
        subprocess.run(["systemctl", "reboot"])
        sys.exit(0)

    def on_finish_clicked(self, widget):
        self.get_application().quit()
        sys.exit(0)


# -----------------------------
# Entrypoint
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Cryptorial's Lazy Arch Setup Script (CLASS) - GTK4 Wizard")
    parser.add_argument("output_file", nargs="?", default="/tmp/class_config.json", help="Path to write configuration JSON")
    parser.add_argument("--status-file", default=None, help="Path to installation progress status JSON")
    args = parser.parse_args()

    app = Gtk.Application(application_id="com.cryptorial.class.wizard")

    def on_activate(app):
        load_custom_css()
        win = CLASSWizardWindow(app, args.output_file, status_file=args.status_file)
        win.present()

    app.connect("activate", on_activate)
    app.run(None)

if __name__ == "__main__":
    main()
