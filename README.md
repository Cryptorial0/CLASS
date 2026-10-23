# Cryptorial's Lazy Arch Setup Script (CLASS)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

```
 ██████╗██╗      █████╗ ███████╗███████╗
██╔════╝██║     ██╔══██╗██╔════╝██╔════╝
██║     ██║     ███████║███████╗███████╗
██║     ██║     ██╔══██║╚════██║╚════██║
╚██████╗███████╗██║  ██║███████║███████║
 ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝
```

Quick post-install setup script for fresh Arch Linux installs. Sets up GPU drivers, gaming essentials, emulators, flatpaks, and desktop tools without needing to manually hunt down dozens of packages.

Launches a GTK4 wizard if you are running in Wayland or X11, or drops into an interactive terminal menu if you are on a TTY or SSH session.

## Run

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Cryptorial0/CLASS/master/CLASS.sh)"
```

Pass flags directly if needed:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Cryptorial0/CLASS/master/CLASS.sh)" --no-update
```

## Flags

| Flag | What it does |
| :--- | :--- |
| `(none)` | Auto-detects session. Starts GTK4 wizard on desktop, terminal UI in TTY/SSH. |
| `--gui` | Force launch GTK4 graphical interface. |
| `--tui`, `--no-gui` | Force launch terminal interface. |
| `--skip-update`, `--no-update` | Skip initial system update. |
| `-h`, `--help` | Show options and exit. |

## Manual Clone

```bash
git clone https://github.com/Cryptorial0/CLASS.git
cd CLASS
chmod +x CLASS.sh
./CLASS.sh
```

## What's Included

### GPU Drivers (Optional / Opt-In)
Detects your graphics hardware via `lspci` and allows you to optionally install the recommended 32-bit and 64-bit Mesa / Vulkan packages:
- AMD: `mesa`, `lib32-mesa`, `vulkan-radeon`, `lib32-vulkan-radeon`
- NVIDIA: `nvidia-utils`, `lib32-nvidia-utils`, `nvidia-settings` (plus `nvidia` driver packages if missing)
- Intel: `mesa`, `lib32-mesa`, `vulkan-intel`, `lib32-vulkan-intel`, `intel-media-driver`
- Generic / VM: `mesa`, `lib32-mesa`

### Browsers
Choose one primary browser or search the repos for another:
- Brave Origin (`brave-origin-bin`, recommended default)
- Firefox
- Chromium
- Vivaldi
- Custom (search Arch repos and AUR)

### Browser Extensions
Pre-configures a curated suite of extensions via enterprise policy, so they are ready as soon as you launch your browser:
- **Return YouTube Dislike**: Restores dislike count indicators on YouTube
- **SponsorBlock**: Crowdsourced skip for sponsor segments, intros, and reminders
- **Adblock for YouTube**: Removes pre-roll and display ads on YouTube
- **Dark Reader**: Real-time dark mode for all websites
- **Consent-O-Matic**: Automatically fills out and rejects GDPR/cookie consent popups
- **AdNauseam**: Obfuscates tracking profiles while blocking ads (AMO for Firefox, unpacked sideload package for Chromium/Brave)
- **Microsoft to Microslop**: Replaces occurrences of "Microsoft" with "Microslop"
- **Hola VPN**: Web proxy and unblocker extension

### Software & Packages
Grouped into toggleable categories (you can select a whole category with one click, or pick individual items):
- Gaming & Compatibility: Steam, Gamescope micro-compositor, ProtonPlus, ProtonUp-Qt, Winetricks, Protontricks, Hydra Launcher, Xodus Nexus, PortProton, r2modman, Prism Launcher
- Performance & Overlays: GameMode, Goverlay (auto-pulls mesa-utils for previews), MangoHud, MangoJuice, vkBasalt, CoreCtrl, LACT, OpenRGB
- Communication: Discord, ZapZap WhatsApp client, Root App
- Media & Capture: Vice Clipper (instant replay game clipper), VLC, Stremio, Spotify, Parabolic, LosslessCut, Songrec
- Utilities & System: Baobab, Flatseal, Ventoy, KDE Connect, LocalSend, Iriun Webcam, qBittorrent, btop, fastfetch, Bazaar, Waywallen (auto-configures wallpaper daemon & DE plugin for KDE/GNOME)
- Emulators: PCSX2, RPCS3, Dolphin, PPSSPP, RetroArch, MAME, DuckStation, Eden

Need something not listed? The bottom of the apps page has an embedded AUR search bar to search and queue extra packages directly.

### Flatpaks
Flathub is configured automatically. Includes GPU Screen Recorder (`com.dec05eba.gpu_screen_recorder`) pre-selected by default with a toggle to turn it off.

### Custom Scripts
Installs standalone helper tools directly to `/usr/local/bin` and `~/.local/bin`:
- `slssteam`: CLI manager and auto-updater for SLSsteam DLC/achievement integration on Steam and Flatpak Steam
- `vencord`: Automated installer and restarter utility for Vencord on Discord
- `yayf`: Interactive fuzzy finder helper (`fzf`) for searching and previewing AUR packages

## How It Works

- Multi-arch & Chaotic-AUR: Enables the `[multilib]` repo for 32-bit gaming libraries and sets up `[chaotic-aur]` for precompiled binaries so you don't spend hours compiling large packages from source.
- AUR Helper: Installs `yay` if you don't already have an AUR helper installed.
- Progress & Logs: Shows live stage descriptions and auto-scrolling output during installation. Full log output is mirrored to `~/class-install.log`.

## License

GPL-3.0 License. See [LICENSE](LICENSE) for details.
