#!/usr/bin/env bash

# ============================================
# Cryptorial's Lazy Arch Setup Script (CLASS)
# Made by Cryptorial
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# ============================================

set -euo pipefail

LOG_FILE="$HOME/class-install.log"

SKIP_UPDATE=0
GUI_MODE="auto"

all_args=("$@")
if [[ "$0" == -* ]]; then
    all_args=("$0" "${all_args[@]}")
fi

for arg in "${all_args[@]}"; do
    case "$arg" in
        --skip-update|--no-update)
            SKIP_UPDATE=1
            ;;
        --gui)
            GUI_MODE="yes"
            ;;
        --tui|--no-gui)
            GUI_MODE="no"
            ;;
        -h|--help)
            echo "Cryptorial's Lazy Arch Setup Script (CLASS)"
            echo "Usage: ./CLASS.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --gui                       Launch GTK4 GUI interface"
            echo "  --tui                       Launch terminal interface (no GUI)"
            echo "  --no-gui                    Alias for --tui"
            echo "  --skip-update, --no-update  Skip initial system update"
            echo "  -h, --help                  Show this help message"
            exit 0
            ;;
    esac
done

# Detect whether to run in GUI or TUI mode
USE_GUI=0
if [ "$GUI_MODE" = "yes" ]; then
    USE_GUI=1
elif [ "$GUI_MODE" = "no" ]; then
    USE_GUI=0
else
    # Auto-detect display server (X11 or Wayland)
    if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
        USE_GUI=1
    fi
fi

# Initialize log file with a starting timestamp banner
echo "================================================================" > "$LOG_FILE"
echo " Cryptorial's Lazy Arch Setup Script (CLASS) - Installation Log " >> "$LOG_FILE"
echo " Timestamp: $(date)                                             " >> "$LOG_FILE"
echo "================================================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# -----------------------------
# Color definitions & Styling
# -----------------------------
NC='\033[0m'
BOLD='\033[1m'
ITALIC='\033[3m'
UNDERLINE='\033[4m'

# Foreground Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'

# Bold Colors
BRED='\033[1;31m'
BGREEN='\033[1;32m'
BYELLOW='\033[1;33m'
BBLUE='\033[1;34m'
BMAGENTA='\033[1;35m'
BCYAN='\033[1;36m'
BWHITE='\033[1;37m'
BORANGE='\033[1;38;5;208m'

# -----------------------------
# TUI Printing Functions
# -----------------------------
print_header() {
    clear 2>/dev/null || true
    echo -e "${BCYAN}================================================================${NC}"
    echo -e " ${BMAGENTA}██████╗██╗      █████╗ ███████╗███████╗${NC}   ${BWHITE}Cryptorial's Lazy Arch Setup Script (CLASS)${NC}"
    echo -e " ${BMAGENTA}██╔════╝██║     ██╔══██╗██╔════╝██╔════╝${NC}   ${BBLUE}Made by Cryptorial${NC}"
    echo -e " ${BMAGENTA}██║     ██║     ███████║███████╗███████╗${NC}"
    echo -e " ${BMAGENTA}██║     ██║     ██╔══██║╚════██║╚════██║${NC}"
    echo -e " ${BMAGENTA}╚██████╗███████╗██║  ██║███████║███████║${NC}"
    echo -e " ${BMAGENTA} ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝${NC}"
    echo -e "${BCYAN}================================================================${NC}"
    echo ""
}

print_step() {
    local title="$1"
    echo -e "\n${BCYAN}┌──────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BCYAN}│${NC} ${BWHITE}:: ${title}${NC}"
    echo -e "${BCYAN}└──────────────────────────────────────────────────────────────┘${NC}\n"
    echo -e "\n--- STEP: ${title} ---" >> "$LOG_FILE"
}

print_success() {
    echo -e "${BGREEN}[OK]${NC} $1"
    echo "[OK] $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${BYELLOW}[!]${NC} ${BOLD}WARNING:${NC} $1"
    echo "[!] WARNING: $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${BRED}[x]${NC} ${BOLD}ERROR:${NC} $1"
    echo "[x] ERROR: $1" >> "$LOG_FILE"
}

print_info() {
    echo -e "${BBLUE}[i]${NC} $1"
    echo "[i] $1" >> "$LOG_FILE"
}

# -----------------------------
# Initial Startup Banner
# -----------------------------
print_header

# -----------------------------
# Safety checks
# -----------------------------
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run as root."
    exit 1
fi

# -----------------------------
# Helper function for installing
# -----------------------------
run_install() {
    if [ "$#" -eq 0 ]; then return 0; fi
    
    # Filter out packages already installed on the system to prevent unnecessary partial upgrades
    local to_install=()
    for pkg in "$@"; do
        if pacman -Qq "$pkg" &>/dev/null; then
            print_info "$pkg is already installed -- skipping."
        else
            to_install+=("$pkg")
        fi
    done

    if [ ${#to_install[@]} -eq 0 ]; then
        return 0
    fi

    echo -e "\n--- Installing packages: ${to_install[*]} ---" >> "$LOG_FILE"
    
    # Try to install all packages together first for efficiency
    if yay -S --needed --noconfirm --cleanmenu=false --diffmenu=false "${to_install[@]}" 2>&1 | tee -a "$LOG_FILE"; then
        return 0
    fi
    
    # If batch installation fails, fall back to installing individually
    print_warning "Batch installation failed. Attempting to install packages individually..."
    local failed_pkgs=()
    for pkg in "${to_install[@]}"; do
        print_info "Installing $pkg..."
        if ! yay -S --needed --noconfirm --cleanmenu=false --diffmenu=false "$pkg" 2>&1 | tee -a "$LOG_FILE"; then
            print_error "Failed to install $pkg"
            failed_pkgs+=("$pkg")
        fi
    done
    
    if [ ${#failed_pkgs[@]} -gt 0 ]; then
        print_warning "The following packages failed to install: ${failed_pkgs[*]}"
        return 1
    fi
    return 0
}

# -----------------------------
# Base setup & Repositories
# -----------------------------
print_step "Configuring Repositories"

# 1. Enable multilib
if grep -q "#\[multilib\]" /etc/pacman.conf; then
    print_info "Enabling [multilib] repository..."
    sudo sed -i '/\[multilib\]/,/Include/s/^#//' /etc/pacman.conf
    print_success "[multilib] repository enabled."
else
    print_info "[multilib] repository is already active or not found."
fi

# 2. Speed Optimizations: Parallel Downloads & Multi-Core Compiling
if grep -q "#ParallelDownloads" /etc/pacman.conf; then
    print_info "Enabling parallel downloads in pacman.conf..."
    sudo sed -i 's/#ParallelDownloads = .*/ParallelDownloads = 10/' /etc/pacman.conf
    print_success "Parallel downloads enabled (set to 10 concurrent streams)."
elif grep -q "ParallelDownloads" /etc/pacman.conf; then
    print_info "Optimizing parallel downloads to 10 streams..."
    sudo sed -i 's/ParallelDownloads = .*/ParallelDownloads = 10/' /etc/pacman.conf
    print_success "Parallel downloads optimized."
fi

if [ -f /etc/makepkg.conf ] && grep -q "#MAKEFLAGS=" /etc/makepkg.conf; then
    cores=$(nproc)
    print_info "Configuring compiler to use all $cores CPU threads..."
    sudo sed -i "s/#MAKEFLAGS=.*/MAKEFLAGS=\"-j$cores\"/" /etc/makepkg.conf
    print_success "Compilation flags optimized for multi-threading (-j$cores)."
fi

# 3. Enable chaotic-aur
if ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
    print_info "Configuring [chaotic-aur] repository..."
    print_info "Importing and signing chaotic-aur keys..."
    sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
    sudo pacman-key --lsign-key 3056513887B78AEB
    print_info "Installing keyring and mirrorlist..."
    sudo pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-mirrorlist.pkg.tar.zst'
    print_info "Adding chaotic-aur to /etc/pacman.conf..."
    sudo bash -c 'cat >> /etc/pacman.conf <<EOF

[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist
EOF'
    print_success "[chaotic-aur] repository added successfully."
else
    print_info "[chaotic-aur] repository is already active."
fi

print_step "Installing Base System Tools"
if [ "$SKIP_UPDATE" -eq 1 ]; then
    if [ ! -f /var/lib/pacman/sync/chaotic-aur.db ] && grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
        print_info "Synchronizing chaotic-aur database..."
        sudo pacman -Sy 2>&1 | tee -a "$LOG_FILE"
    fi
    print_info "Skipping system update. Installing git, base-devel, curl, wget, unzip, tar, fzf, python, python-gobject, gtk4..."
    sudo pacman -S --needed git base-devel curl wget unzip tar fzf python python-gobject gtk4 2>&1 | tee -a "$LOG_FILE"
else
    print_info "Updating system and installing git, base-devel, curl, wget, unzip, tar, fzf, python, python-gobject, gtk4..."
    sudo pacman -Syu --needed git base-devel curl wget unzip tar fzf python python-gobject gtk4 2>&1 | tee -a "$LOG_FILE"
fi

if ! command -v yay &> /dev/null; then
    print_info "Installing yay AUR helper..."
    cd /tmp
    rm -rf yay
    git clone https://aur.archlinux.org/yay.git
    cd yay
    makepkg -si --noconfirm 2>&1 | tee -a "$LOG_FILE"
    cd ~
    print_success "yay installed successfully."
else
    print_info "yay is already installed."
fi

# -----------------------------
# Desktop Environment Auto-Detection
# -----------------------------
print_step "Desktop Environment Auto-Detection"
print_info "Detecting Desktop Environment..."
DE="unknown"

if [[ "${XDG_CURRENT_DESKTOP,,}" == *"kde"* || "${XDG_CURRENT_DESKTOP,,}" == *"plasma"* ]]; then
    DE="kde"
    print_success "Detected KDE Plasma (or Garuda Mokka)"
elif [[ "${XDG_CURRENT_DESKTOP,,}" == *"gnome"* ]]; then
    DE="gnome"
    print_success "Detected GNOME"
elif [[ "${XDG_CURRENT_DESKTOP,,}" == *"cinnamon"* ]]; then
    DE="cinnamon"
    print_success "Detected Cinnamon"
else
    DE="other"
    print_info "Detected other DE or TTY: ${XDG_CURRENT_DESKTOP:-None}"
fi

core_pkgs=(
    flatpak
)

if [[ "$DE" == "kde" ]]; then
    core_pkgs+=(plasma-browser-integration)
fi

# -----------------------------
# Configuration Wizard Setup
# -----------------------------
gpu="skip"
gpu_pkgs=()
browser_pkg=()
emu_pkgs=()
main_pkgs=()
flatpak_pkgs=()
script_pkgs=()
aur_pkgs=()
WIZARD_DONE=0

STATUS_FILE="/tmp/class_status.json"

PYTHON_BIN="python3"
if [ -x "/usr/bin/python3" ]; then
    PYTHON_BIN="/usr/bin/python3"
fi

set_gui_progress() {
    local percent="$1"
    local title="$2"
    local desc="$3"
    local status="${4:-running}"
    if [ "$USE_GUI" -eq 1 ] && [ -n "${STATUS_FILE:-}" ]; then
        "$PYTHON_BIN" -c "
import json, os
data = {'percent': $percent, 'title': '''$title''', 'desc': '''$desc''', 'status': '''$status'''}
with open('$STATUS_FILE.tmp', 'w') as f:
    json.dump(data, f)
os.replace('$STATUS_FILE.tmp', '$STATUS_FILE')
" 2>/dev/null || true
    fi
}

if [ "$USE_GUI" -eq 1 ]; then
    SCRIPT_DIR=""
    if [ -n "${BASH_SOURCE[0]:-}" ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd || true)"
    fi
    if [ -z "$SCRIPT_DIR" ]; then
        SCRIPT_DIR="$(pwd)"
    fi

    GUI_SCRIPT="$SCRIPT_DIR/class_gui.py"
    if [ ! -s "$GUI_SCRIPT" ]; then
        GUI_SCRIPT="/tmp/class_gui.py"
        print_info "Downloading graphical wizard..."
        curl -sL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/Cryptorial0/CLASS/master/class_gui.py?$(date +%s)" -o "$GUI_SCRIPT" 2>/dev/null || true
    fi

    gtk_err=$("$PYTHON_BIN" -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk" 2>&1 || true)
    if [ -s "$GUI_SCRIPT" ] && [ -z "$gtk_err" ]; then
        CONFIG_FILE="/tmp/class_config.json"
        rm -f "$CONFIG_FILE" "$STATUS_FILE"

        print_info "Launching Cryptorial's Lazy Arch Setup Script Graphical Wizard..."
        "$PYTHON_BIN" "$GUI_SCRIPT" "$CONFIG_FILE" --status-file "$STATUS_FILE" &
        GUI_PID=$!

        # Wait for the user to configure and proceed (or close/halt)
        while [ ! -f "$CONFIG_FILE" ]; do
            if ! kill -0 "$GUI_PID" 2>/dev/null; then
                print_warning "Setup was halted or cancelled by user. Exiting."
                exit 0
            fi
            sleep 0.2
        done

        # Load selections from JSON
        gpu=$("$PYTHON_BIN" -c "import json; print(json.load(open('$CONFIG_FILE')).get('gpu', 'skip'))")
        mapfile -t gpu_pkgs < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('gpu_pkgs', [])]")
        mapfile -t browser_pkg < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('browser_pkg', [])]")
        mapfile -t browser_extensions < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('browser_extensions', [])]")
        mapfile -t emu_pkgs < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('emu_pkgs', [])]")
        mapfile -t main_pkgs < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('main_pkgs', [])]")
        mapfile -t flatpak_pkgs < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('flatpak_pkgs', [])]")
        mapfile -t script_pkgs < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('script_pkgs', json.load(open('$CONFIG_FILE')).get('scripts', []))]")
        mapfile -t aur_pkgs < <("$PYTHON_BIN" -c "import json; [print(x) for x in json.load(open('$CONFIG_FILE')).get('aur_pkgs', [])]")

        print_success "Configuration loaded from Graphical Wizard."
        WIZARD_DONE=1
    else
        if [ ! -s "$GUI_SCRIPT" ]; then
            print_warning "GTK4 graphical wizard unavailable (could not download class_gui.py). Falling back to Terminal interface."
        else
            print_warning "GTK4 graphical wizard unavailable ($gtk_err). Falling back to Terminal interface."
        fi
        USE_GUI=0
        WIZARD_DONE=0
    fi
fi

if [ "$WIZARD_DONE" -eq 0 ]; then
    # -----------------------------
    # Terminal TUI: GPU Auto-Detection (No manual section)
    # -----------------------------
    print_step "GPU Hardware Auto-Detection"
    print_info "Detecting graphics hardware via lspci..."
    lspci_out=""
    if command -v lspci &>/dev/null; then
        lspci_out=$(lspci -k 2>/dev/null || true)
    fi
    combined="${lspci_out,,}"
    
    has_amd=0
    has_nvidia=0
    has_intel=0

    if [[ "$combined" =~ (amd|advanced micro devices|ati) ]]; then has_amd=1; fi
    if [[ "$combined" =~ nvidia ]]; then has_nvidia=1; fi
    if [[ "$combined" =~ intel ]]; then has_intel=1; fi

    if [ "$has_amd" -eq 0 ] && [ "$has_nvidia" -eq 0 ] && [ "$has_intel" -eq 0 ]; then
        for vpath in /sys/class/drm/card*/device/vendor; do
            if [ -f "$vpath" ]; then
                vid=$(cat "$vpath" 2>/dev/null || true)
                case "$vid" in
                    0x1002) has_amd=1 ;;
                    0x10de) has_nvidia=1 ;;
                    0x8086) has_intel=1 ;;
                esac
            fi
        done
    fi

    detected_gpus=()
    detected_gpu_pkgs=()
    detected_gpu_tag="skip"

    if [ "$has_amd" -eq 1 ]; then
        detected_gpus+=("AMD Radeon (Mesa / RADV)")
        detected_gpu_pkgs+=(vulkan-radeon lib32-vulkan-radeon mesa lib32-mesa)
        detected_gpu_tag="amd"
    fi
    if [ "$has_nvidia" -eq 1 ]; then
        detected_gpus+=("NVIDIA Proprietary")
        if pacman -Qq nvidia-utils &>/dev/null; then
            detected_gpu_pkgs+=(lib32-nvidia-utils nvidia-settings)
        else
            detected_gpu_pkgs+=(nvidia nvidia-utils lib32-nvidia-utils nvidia-settings)
        fi
        detected_gpu_tag="nvidia"
    fi
    if [ "$has_intel" -eq 1 ]; then
        detected_gpus+=("Intel Graphics (Mesa / Vulkan / Arc)")
        detected_gpu_pkgs+=(mesa lib32-mesa vulkan-intel lib32-vulkan-intel intel-media-driver)
        detected_gpu_tag="intel"
    fi
    if [ ${#detected_gpus[@]} -eq 0 ]; then
        detected_gpus+=("Generic / Virtual GPU (Mesa)")
        detected_gpu_pkgs+=(mesa lib32-mesa)
        detected_gpu_tag="generic"
    fi

    gpu="skip"
    gpu_pkgs=()

    print_success "Auto-detected GPU: ${detected_gpus[*]}"
    print_info "Available driver packages: ${detected_gpu_pkgs[*]}"

    # -----------------------------
    # Terminal TUI Packages Setup
    # -----------------------------
    app_names=(
        "Steam" "Gamescope" "ProtonPlus" "ProtonUp-Qt" "Winetricks"
        "Protontricks" "Hydra Launcher" "Xodus Nexus" "PortProton" "r2modman" "Prism Launcher"
        "GameMode" "Goverlay" "MangoHud" "MangoJuice" "vkBasalt" "CoreCtrl" "LACT (AMDGPU)"
        "OpenRGB" "Discord" "ZapZap (WhatsApp)" "Root App" "Vice Clipper"
        "VLC Media Player" "Stremio" "Spotify" "Parabolic" "LosslessCut" "Songrec (Shazam)"
        "Baobab" "Flatseal" "Ventoy USB" "KDE Connect" "LocalSend" "Iriun Webcam"
        "qBittorrent" "btop" "fastfetch" "Bazaar"
        "PCSX2 (PS2)" "RPCS3 (PS3)" "Dolphin (GameCube/Wii)" "PPSSPP (PSP)"
        "RetroArch (Multi-system)" "MAME (Arcade)" "DuckStation (PS1)" "Eden (Switch)"
    )
    app_pkgs=(
        "steam" "gamescope" "protonplus" "protonup-qt" "winetricks"
        "protontricks" "hydra-launcher-bin" "xodus-nexus-bin" "portproton" "r2modman-bin" "prismlauncher"
        "gamemode" "goverlay" "mangohud" "mangojuice" "vkbasalt" "corectrl" "lact"
        "openrgb" "discord" "zapzap" "rootapp-bin" "vice-clipper"
        "vlc" "stremio" "spotify" "parabolic" "losslesscut-bin" "songrec"
        "baobab" "flatseal" "ventoy-bin" "kdeconnect" "localsend-bin" "iriunwebcam-bin"
        "qbittorrent" "btop" "fastfetch" "bazaar"
        "pcsx2-git" "rpcs3-git" "dolphin-emu" "ppsspp"
        "retroarch" "mame" "duckstation-gpl" "eden-git"
    )

    if [[ "$DE" == "kde" || "$DE" == "gnome" ]]; then
        app_names=("Waywallen" "${app_names[@]}")
        app_pkgs=("waywallen" "${app_pkgs[@]}")
    fi

    num_apps=${#app_names[@]}
    app_selections=()
    for ((i=0; i<num_apps; i++)); do
        app_selections+=(0)
    done

    # Browser Extensions: Curated list selected by default
    ext_ids=(
        "return-youtube-dislike"
        "sponsorblock"
        "adblock-for-youtube"
        "darkreader"
        "consent-o-matic"
        "adnauseam"
        "microsoft-to-microslop"
        "hola-vpn"
    )
    ext_names=(
        "Return YouTube Dislike"
        "SponsorBlock"
        "Adblock for YouTube"
        "Dark Reader"
        "Consent-O-Matic"
        "AdNauseam"
        "Microsoft to Microslop"
        "Hola VPN"
    )
    num_extensions=${#ext_ids[@]}
    ext_selections=()
    for ((i=0; i<num_extensions; i++)); do
        ext_selections+=(1)
    done
    browser_extensions=("${ext_ids[@]}")

    # Flatpaks: GSR selected by default
    flatpak_names=("GPU Screen Recorder (GSR)")
    flatpak_list_pkgs=("com.dec05eba.gpu_screen_recorder")
    flatpak_selections=(1)

    # Setup Scripts: Standalone tools (Opt-in by default)
    script_names=(
        "SLSsteam Manager (slssteam)"
        "Vencord Discord Mod (vencord)"
        "NTFS Disk Repair & Auto-Mounter (fix-ntfs)"
    )
    script_descs=(
        "Unlocks DLCs and manages achievements for Steam & Flatpak Steam."
        "Installs and auto-updates the Vencord client mod for Discord."
        "Repairs dirty NTFS drives and configures udisks2 for forced mounting."
    )
    script_list_pkgs=("slssteam" "vencord" "fix-ntfs")
    num_scripts=${#script_list_pkgs[@]}
    script_selections=(0 0 0)

    current_step=1
    while [ "$current_step" -le 7 ]; do
        case "$current_step" in
            1)
                print_step "GPU Driver Selection (Step 1/6)"
                echo -e "${BWHITE}Hardware Detected:${NC} ${BMAGENTA}${detected_gpus[*]}${NC}"
                echo -e "${BWHITE}Driver Packages:${NC}   ${BCYAN}${detected_gpu_pkgs[*]}${NC}"
                echo ""
                echo -e "GPU driver installation is ${BOLD}optional (opt-in)${NC}."
                echo -e "  ${BCYAN}1)${NC} Skip GPU Drivers ${BGREEN}[Default]${NC}"
                echo -e "  ${BCYAN}2)${NC} Install Auto-Detected GPU Drivers (${detected_gpus[*]})"
                echo ""
                read -p "  Your Choice [1-2, default=1]: " gpu_choice

                case "${gpu_choice:-1}" in
                    2|[yY]|[yY][eE][sS])
                        gpu_pkgs=("${detected_gpu_pkgs[@]}")
                        gpu="$detected_gpu_tag"
                        print_success "Selected GPU drivers for installation."
                        ;;
                    *)
                        gpu_pkgs=()
                        gpu="skip"
                        print_info "Skipping GPU driver installation."
                        ;;
                esac
                current_step=2
                ;;

            2)
                print_step "Browser Selection (Step 2/6)"
                echo -e "${BWHITE}Select web browser to install:${NC}"
                echo -e "  ${BCYAN}1)${NC} Brave Origin ${BGREEN}[Recommended]${NC}"
                echo -e "  ${BCYAN}2)${NC} Firefox"
                echo -e "  ${BCYAN}3)${NC} Chromium"
                echo -e "  ${BCYAN}4)${NC} Vivaldi"
                echo -e "  ${BCYAN}5)${NC} Other (Search Repositories / AUR)"
                echo -e "  ${BCYAN}6)${NC} Skip"
                echo -e "  ${BCYAN}p)${NC} Previous Step (GPU Drivers)"
                echo ""
                read -p "  Your Choice [1-6, 'p'=Prev, default=1]: " browser_choice

                if [[ "${browser_choice,,}" = "p" || "${browser_choice,,}" = "prev" || "${browser_choice,,}" = "back" ]]; then
                    current_step=1
                    continue
                fi

                case "${browser_choice:-1}" in
                    1) browser_pkg=(brave-origin-bin); print_success "Selected Brave Origin." ;;
                    2) browser_pkg=(firefox); print_success "Selected Firefox." ;;
                    3) browser_pkg=(chromium); print_success "Selected Chromium." ;;
                    4) browser_pkg=(vivaldi); print_success "Selected Vivaldi." ;;
                    5|other|Other)
                        print_info "Searching for a browser..."
                        if ! command -v fzf &>/dev/null; then
                            print_info "Installing fzf for interactive search..."
                            sudo pacman -S --needed --noconfirm fzf 2>&1 | tee -a "$LOG_FILE"
                        fi
                        fzf_args=(
                            --prompt="Browser Search > "
                            --header="[ENTER]: Select Browser | [ESC]: Cancel/Manual entry | [ALT-P]: Toggle Info"
                            --preview="yay -Sii {1}"
                            --preview-label="alt-p: toggle description, alt-j/k: scroll"
                            --preview-label-pos="bottom"
                            --preview-window="down:65%:wrap"
                            --bind="alt-p:toggle-preview"
                            --bind="alt-d:preview-half-page-down,alt-u:preview-half-page-up"
                            --bind="alt-k:preview-up,alt-j:preview-down"
                            --color="pointer:green,marker:green"
                        )
                        chosen_browser=$(yay -Slq | sort -u | fzf "${fzf_args[@]}" --query="browser" || true)
                        if [ -n "$chosen_browser" ]; then
                            browser_pkg=("$chosen_browser")
                            print_success "Selected browser: $chosen_browser"
                        else
                            echo ""
                            read -p "  No package selected. Enter browser package manually (or Enter to skip): " manual_browser
                            if [ -n "$manual_browser" ]; then
                                browser_pkg=("$manual_browser")
                                print_success "Selected browser: $manual_browser"
                            else
                                browser_pkg=()
                                print_info "Skipping browser installation."
                            fi
                        fi
                        ;;
                    *)
                        browser_pkg=()
                        print_info "Skipping browser installation."
                        ;;
                esac
                current_step=3
                ;;

            3)
                print_step "Browser Extensions (Step 3/6)"
                echo -e "${BWHITE}Select curated browser extensions to provision:${NC}"
                echo -e "  - ${BGREEN}[*]${NC} indicates the extension is selected."
                echo -e "  - Enter numbers (1-$num_extensions) separated by spaces to ${BOLD}toggle${NC} checkmarks."
                echo -e "  - Type ${BCYAN}'a'${NC} or ${BCYAN}'all'${NC} to ${BOLD}SELECT ALL${NC} extensions."
                echo -e "  - Type ${BCYAN}'n'${NC} or ${BCYAN}'none'${NC} to ${BOLD}UNSELECT ALL${NC} extensions."
                echo -e "  - Type ${BCYAN}'p'${NC} to go to ${BOLD}PREVIOUS STEP${NC} (Browser Selection)."
                echo -e "  - Press ${BCYAN}[Enter]${NC} (empty input) to confirm and continue."
                echo ""

                while true; do
                    for ((i=0; i<num_extensions; i++)); do
                        num=$((i + 1))
                        char=" "
                        [ "${ext_selections[i]}" -eq 1 ] && char="${BGREEN}*${NC}"
                        printf "  %2d) [%b] %s\n" "$num" "$char" "${ext_names[i]}"
                    done
                    echo ""
                    read -p "  Selection (1-$num_extensions, 'a'=All, 'n'=None, 'p'=Prev, Enter=Confirm): " ext_input

                    if [[ "${ext_input,,}" = "p" || "${ext_input,,}" = "prev" || "${ext_input,,}" = "back" ]]; then
                        current_step=2
                        break
                    fi

                    if [ -z "$ext_input" ]; then
                        browser_extensions=()
                        for ((i=0; i<num_extensions; i++)); do
                            if [ "${ext_selections[i]}" -eq 1 ]; then
                                browser_extensions+=("${ext_ids[i]}")
                            fi
                        done
                        if [ ${#browser_extensions[@]} -gt 0 ]; then
                            print_success "Selected browser extensions: ${#browser_extensions[@]} extension(s)."
                        else
                            print_info "Skipping browser extensions."
                        fi
                        current_step=4
                        break
                    fi

                    if [[ "${ext_input,,}" = "a" || "${ext_input,,}" = "all" ]]; then
                        for ((i=0; i<num_extensions; i++)); do
                            ext_selections[i]=1
                        done
                        clear 2>/dev/null || true
                        print_header
                        print_step "Browser Extensions (Step 3/6)"
                        continue
                    fi

                    if [[ "${ext_input,,}" = "n" || "${ext_input,,}" = "none" || "$ext_input" = "0" ]]; then
                        for ((i=0; i<num_extensions; i++)); do
                            ext_selections[i]=0
                        done
                        clear 2>/dev/null || true
                        print_header
                        print_step "Browser Extensions (Step 3/6)"
                        continue
                    fi

                    for val in $ext_input; do
                        if [[ "$val" =~ ^[0-9]+$ ]] && [ "$val" -ge 1 ] && [ "$val" -le "$num_extensions" ]; then
                            idx=$((val - 1))
                            if [ "${ext_selections[idx]}" -eq 1 ]; then
                                ext_selections[idx]=0
                            else
                                ext_selections[idx]=1
                            fi
                        else
                            print_warning "Invalid input: $val. Skipping..."
                            sleep 1
                        fi
                    done

                    clear 2>/dev/null || true
                    print_header
                    print_step "Browser Extensions (Step 3/6)"
                done
                ;;

            4)
                print_step "Application Selection (Step 4/6)"
                is_first_prompt=1
                while true; do
                    if [ "$is_first_prompt" -eq 0 ]; then
                        clear 2>/dev/null || true
                        print_header
                        print_step "Application Selection (Step 4/6)"
                    fi
                    is_first_prompt=0

                    echo -e "${BWHITE}Select applications, emulators, and tools to install:${NC}"
                    echo -e "  - ${BGREEN}[*]${NC} indicates the package is selected."
                    echo -e "  - Enter numbers (separated by spaces) to ${BOLD}toggle${NC} checkmarks."
                    echo -e "  - Type ${BCYAN}'a'${NC} or ${BCYAN}'all'${NC} to ${BOLD}SELECT ALL${NC} packages."
                    echo -e "  - Type ${BCYAN}'n'${NC} or ${BCYAN}'none'${NC} (or ${BCYAN}0${NC}) to ${BOLD}UNSELECT ALL${NC} packages."
                    echo -e "  - Type ${BCYAN}'s'${NC} to ${BOLD}Search AUR${NC} for extra packages."
                    echo -e "  - Type ${BCYAN}'m'${NC} to add extra packages ${BOLD}manually${NC}."
                    echo -e "  - Type ${BCYAN}'p'${NC} to go to ${BOLD}PREVIOUS STEP${NC} (Browser Extensions)."
                    echo -e "  - Press ${BCYAN}[Enter]${NC} (empty input) to confirm and continue."
                    echo ""

                    half=$(( (num_apps + 1) / 2 ))
                    for ((i=0; i<half; i++)); do
                        idx1=$i
                        num1=$((idx1 + 1))
                        char1=" "
                        [ "${app_selections[idx1]}" -eq 1 ] && char1="${BGREEN}*${NC}"
                        col1_text=$(printf "%2d) [%b] %-25s" "$num1" "$char1" "${app_names[idx1]}")
                        
                        idx2=$((i + half))
                        if [ "$idx2" -lt "$num_apps" ]; then
                            num2=$((idx2 + 1))
                            char2=" "
                            [ "${app_selections[idx2]}" -eq 1 ] && char2="${BGREEN}*${NC}"
                            col2_text=$(printf "%2d) [%b] %s" "$num2" "$char2" "${app_names[idx2]}")
                            echo -e "  $col1_text    $col2_text"
                        else
                            echo -e "  $col1_text"
                        fi
                    done

                    echo ""
                    if [ ${#aur_pkgs[@]} -gt 0 ]; then
                        echo -e "  ${BWHITE}Queued Extra Packages:${NC} ${BGREEN}${aur_pkgs[*]}${NC}"
                        echo ""
                    fi

                    read -p "  Selection (Numbers, 's'=Search AUR, 'm'=Manual, 'a'=All, 'n'=None, 'p'=Prev, Enter=Confirm): " selection_input

                    if [[ "${selection_input,,}" = "p" || "${selection_input,,}" = "prev" || "${selection_input,,}" = "back" ]]; then
                        current_step=3
                        break
                    fi

                    if [[ "${selection_input,,}" = "s" || "${selection_input,,}" = "search" ]]; then
                        if ! command -v fzf &>/dev/null; then
                            sudo pacman -S --needed --noconfirm fzf 2>&1 | tee -a "$LOG_FILE"
                        fi
                        fzf_args=(
                            --multi
                            --prompt="Extra Apps Search > "
                            --header="[TAB]: Multi-select | [ENTER]: Add selected packages | [ESC]: Close | [ALT-P]: Info"
                            --preview="yay -Siia {1}"
                            --preview-label="alt-p: toggle description, alt-b/B: toggle PKGBUILD, alt-j/k: scroll, tab: multi-select"
                            --preview-label-pos="bottom"
                            --preview-window="down:65%:wrap"
                            --bind="alt-p:toggle-preview"
                            --bind="alt-d:preview-half-page-down,alt-u:preview-half-page-up"
                            --bind="alt-k:preview-up,alt-j:preview-down"
                            --color="pointer:green,marker:green"
                        )
                        selected_aur=$(yay -Slqa | fzf "${fzf_args[@]}" || true)
                        if [ -n "$selected_aur" ]; then
                            while IFS= read -r pkg; do
                                [ -z "$pkg" ] && continue
                                already=0
                                for ex in "${aur_pkgs[@]:-}"; do
                                    if [ "$ex" = "$pkg" ]; then already=1; break; fi
                                done
                                [ "$already" -eq 0 ] && aur_pkgs+=("$pkg")
                            done <<< "$selected_aur"
                        fi
                        continue
                    fi

                    if [[ "${selection_input,,}" = "m" || "${selection_input,,}" = "manual" ]]; then
                        read -p "  Enter package name(s) separated by spaces: " manual_pkgs
                        for pkg in $manual_pkgs; do
                            already=0
                            for ex in "${aur_pkgs[@]:-}"; do
                                if [ "$ex" = "$pkg" ]; then already=1; break; fi
                            done
                            [ "$already" -eq 0 ] && aur_pkgs+=("$pkg")
                        done
                        continue
                    fi

                    if [ -z "$selection_input" ]; then
                        main_pkgs=()
                        emu_pkgs=()
                        for ((i=0; i<num_apps; i++)); do
                            if [ "${app_selections[i]}" -eq 1 ]; then
                                pkg_cand="${app_pkgs[i]}"
                                case "$pkg_cand" in
                                    pcsx2-git|rpcs3-git|dolphin-emu|ppsspp|retroarch|mame|duckstation-gpl|eden-git)
                                        emu_pkgs+=("$pkg_cand")
                                        ;;
                                    *)
                                        main_pkgs+=("$pkg_cand")
                                        ;;
                                esac
                            fi
                        done

                        # Auto-handle Goverlay requirements
                        if [[ " ${main_pkgs[*]} " =~ " goverlay " ]]; then
                            if [[ ! " ${main_pkgs[*]} " =~ " mesa-utils " ]]; then
                                main_pkgs+=(mesa-utils)
                            fi
                        fi

                        # Auto-handle Waywallen requirements
                        if [[ " ${main_pkgs[*]} " =~ " waywallen " ]]; then
                            aur_pkgs+=(waywallen-display)
                            if [[ "$DE" == "kde" ]]; then
                                aur_pkgs+=(plasma-wallpaper-waywallen)
                            elif [[ "$DE" == "gnome" ]]; then
                                aur_pkgs+=(gnome-shell-extension-waywallen)
                            fi
                        fi

                        print_success "Selected applications: ${#main_pkgs[@]} apps, ${#emu_pkgs[@]} emulators, ${#aur_pkgs[@]} extra AUR."
                        current_step=5
                        break
                    fi

                    if [[ "${selection_input,,}" = "a" || "${selection_input,,}" = "all" ]]; then
                        for ((i=0; i<num_apps; i++)); do
                            app_selections[i]=1
                        done
                        continue
                    fi

                    if [[ "${selection_input,,}" = "n" || "${selection_input,,}" = "none" || "$selection_input" = "0" ]]; then
                        for ((i=0; i<num_apps; i++)); do
                            app_selections[i]=0
                        done
                        aur_pkgs=()
                        continue
                    fi

                    for val in $selection_input; do
                        if [[ "$val" =~ ^[0-9]+$ ]] && [ "$val" -ge 1 ] && [ "$val" -le "$num_apps" ]; then
                            idx=$((val - 1))
                            if [ "${app_selections[idx]}" -eq 1 ]; then
                                app_selections[idx]=0
                            else
                                app_selections[idx]=1
                            fi
                        else
                            print_warning "Invalid input: $val. Skipping..."
                            sleep 1
                        fi
                    done
                done
                ;;

            5)
                print_step "Flatpak Applications (Step 5/6)"
                echo -e "${BWHITE}Select Flatpak applications to install:${NC}"
                echo -e "  - Enter number to toggle selection."
                echo -e "  - Press ${BCYAN}[Enter]${NC} to confirm and continue."
                echo -e "  - Type ${BCYAN}'p'${NC} to go to ${BOLD}PREVIOUS STEP${NC} (Application Selection)."
                echo ""

                while true; do
                    char=" "
                    [ "${flatpak_selections[0]}" -eq 1 ] && char="${BGREEN}*${NC}"
                    echo -e "  1) [${char}] ${flatpak_names[0]} (Selected by default)"
                    echo ""
                    read -p "  Selection (1=Toggle, 'p'=Previous, Enter=Confirm): " fp_input

                    if [[ "${fp_input,,}" = "p" || "${fp_input,,}" = "prev" || "${fp_input,,}" = "back" ]]; then
                        current_step=4
                        break
                    fi

                    if [ -z "$fp_input" ]; then
                        flatpak_pkgs=()
                        if [ "${flatpak_selections[0]}" -eq 1 ]; then
                            flatpak_pkgs+=("${flatpak_list_pkgs[0]}")
                            print_success "Selected Flatpak: ${flatpak_names[0]}"
                        else
                            print_info "Skipping Flatpak applications."
                        fi
                        current_step=6
                        break
                    fi

                    if [ "$fp_input" = "1" ]; then
                        if [ "${flatpak_selections[0]}" -eq 1 ]; then
                            flatpak_selections[0]=0
                        else
                            flatpak_selections[0]=1
                        fi
                    fi
                done
                ;;

            6)
                print_step "Setup Scripts (Step 6/6)"
                echo -e "${BWHITE}Select custom setup and management scripts to install (Optional):${NC}"
                echo -e "  - ${BGREEN}[*]${NC} indicates the script is selected."
                echo -e "  - Enter numbers (1-$num_scripts) to ${BOLD}toggle${NC} checkmarks."
                echo -e "  - Type ${BCYAN}'a'${NC} to select all, ${BCYAN}'n'${NC} to unselect all."
                echo -e "  - Type ${BCYAN}'p'${NC} to go to ${BOLD}PREVIOUS STEP${NC} (Flatpaks)."
                echo -e "  - Press ${BCYAN}[Enter]${NC} (empty input) to confirm and continue."
                echo ""

                while true; do
                    for ((i=0; i<num_scripts; i++)); do
                        num=$((i + 1))
                        char=" "
                        [ "${script_selections[i]}" -eq 1 ] && char="${BGREEN}*${NC}"
                        echo -e "  $num) [${char}] ${BWHITE}${script_names[i]}${NC}"
                        echo -e "         ${ITALIC}${script_descs[i]}${NC}"
                    done
                    echo ""
                    read -p "  Selection (1-$num_scripts, 'a'=All, 'n'=None, 'p'=Previous, Enter=Confirm): " sc_input

                    if [[ "${sc_input,,}" = "p" || "${sc_input,,}" = "prev" || "${sc_input,,}" = "back" ]]; then
                        current_step=5
                        break
                    fi

                    if [ -z "$sc_input" ]; then
                        script_pkgs=()
                        for ((i=0; i<num_scripts; i++)); do
                            [ "${script_selections[i]}" -eq 1 ] && script_pkgs+=("${script_list_pkgs[i]}")
                        done
                        if [ ${#script_pkgs[@]} -gt 0 ]; then
                            print_success "Selected Scripts: ${script_pkgs[*]}"
                        else
                            print_info "Skipping custom setup scripts."
                        fi
                        current_step=7
                        break
                    fi

                    if [[ "${sc_input,,}" = "a" || "${sc_input,,}" = "all" ]]; then
                        for ((i=0; i<num_scripts; i++)); do
                            script_selections[i]=1
                        done
                    elif [[ "${sc_input,,}" = "n" || "${sc_input,,}" = "none" || "$sc_input" = "0" ]]; then
                        for ((i=0; i<num_scripts; i++)); do
                            script_selections[i]=0
                        done
                    else
                        for token in $sc_input; do
                            if [[ "$token" =~ ^[0-9]+$ ]] && [ "$token" -ge 1 ] && [ "$token" -le "$num_scripts" ]; then
                                idx=$((token - 1))
                                script_selections[idx]=$(( 1 - script_selections[idx] ))
                            fi
                        done
                    fi

                    clear 2>/dev/null || true
                    print_header
                    print_step "Setup Scripts (Step 6/6)"
                done
                ;;

            7)
                print_step "Installation Summary"
                echo -e "${BCYAN}┌──────────────────────────────────────────────────────────────┐${NC}"
                echo -e "${BCYAN}│${NC}               ${BWHITE}INSTALLATION PLAN SUMMARY${NC}                      ${BCYAN}│${NC}"
                echo -e "${BCYAN}└──────────────────────────────────────────────────────────────┘${NC}"
                echo -e " ${BOLD}The script will install the following components:${NC}"
                echo ""
                echo -e "  ${BWHITE}• GPU Drivers:${NC}   ${BMAGENTA}${gpu:-skip}${NC} (${gpu_pkgs[*]:-Skipped})"
                echo -e "  ${BWHITE}• Browser:${NC}       ${BCYAN}${browser_pkg[*]:-None}${NC}"
                echo -e "  ${BWHITE}• Extensions:${NC}    ${BCYAN}${browser_extensions[*]:-None}${NC}"
                echo -e "  ${BWHITE}• Core System:${NC}   ${BWHITE}${core_pkgs[*]}${NC}"
                echo -e "  ${BWHITE}• Main Apps:${NC}     ${BWHITE}${main_pkgs[*]:-None}${NC}"
                echo -e "  ${BWHITE}• Emulators:${NC}     ${BWHITE}${emu_pkgs[*]:-None}${NC}"
                echo -e "  ${BWHITE}• Flatpaks:${NC}      ${BWHITE}${flatpak_pkgs[*]:-None}${NC}"
                echo -e "  ${BWHITE}• Setup Scripts:${NC} ${BWHITE}${script_pkgs[*]:-None}${NC}"
                if [ ${#aur_pkgs[@]} -gt 0 ]; then
                    echo -e "  ${BWHITE}• Custom AUR:${NC}    ${BGREEN}${aur_pkgs[*]}${NC}"
                fi
                echo ""

                echo -e "${BWHITE}Actions:${NC}"
                echo -e "  - Press ${BCYAN}[Enter]${NC} to begin installation"
                echo -e "  - Type ${BCYAN}'p'${NC} to go back to previous step (Setup Scripts)"
                echo -e "  - Press ${BCYAN}[Ctrl+C]${NC} to abort"
                echo ""
                read -p "  Confirm action [Enter=Install, 'p'=Previous]: " confirm_choice
                if [[ "${confirm_choice,,}" = "p" || "${confirm_choice,,}" = "prev" || "${confirm_choice,,}" = "back" ]]; then
                    current_step=6
                    continue
                fi
                break
                ;;
        esac
    done
fi

# -----------------------------
# Browser Extensions Provisioning
# -----------------------------
configure_browser_extensions() {
    if [ ${#browser_extensions[@]} -eq 0 ]; then
        print_info "No browser extensions selected. Skipping extension provisioning."
        return 0
    fi

    local chosen_b="${browser_pkg[0]:-}"
    local target_browsers=()

    if [ -n "$chosen_b" ]; then
        # User explicitly selected a browser in CLASS
        case "$chosen_b" in
            brave*|*brave*) target_browsers+=(brave) ;;
            firefox*) target_browsers+=(firefox) ;;
            chromium*) target_browsers+=(chromium) ;;
            vivaldi*) target_browsers+=(vivaldi) ;;
            *chrome*) target_browsers+=(chrome) ;;
            *edge*) target_browsers+=(edge) ;;
            *)
                if [[ "$chosen_b" =~ (librewolf|floorp|waterfox|zen) ]]; then
                    target_browsers+=(firefox)
                elif [[ "$chosen_b" =~ (opera|thorium|ungoogled) ]]; then
                    target_browsers+=(chromium)
                fi
                ;;
        esac
    else
        # Browser selection was skipped: auto-detect installed browsers on the system
        if command -v brave &>/dev/null || command -v brave-browser &>/dev/null || pacman -Qq brave-bin &>/dev/null 2>&1 || pacman -Qq brave-origin-bin &>/dev/null 2>&1 || (flatpak list --app 2>/dev/null | grep -qi "com.brave.Browser"); then
            target_browsers+=(brave)
        fi
        if command -v firefox &>/dev/null || pacman -Qq firefox &>/dev/null 2>&1 || (flatpak list --app 2>/dev/null | grep -qi "org.mozilla.firefox"); then
            target_browsers+=(firefox)
        fi
        if command -v chromium &>/dev/null || pacman -Qq chromium &>/dev/null 2>&1 || (flatpak list --app 2>/dev/null | grep -qi "org.chromium.Chromium"); then
            target_browsers+=(chromium)
        fi
        if command -v vivaldi &>/dev/null || command -v vivaldi-stable &>/dev/null || pacman -Qq vivaldi &>/dev/null 2>&1 || (flatpak list --app 2>/dev/null | grep -qi "com.vivaldi.Vivaldi"); then
            target_browsers+=(vivaldi)
        fi
        if command -v google-chrome &>/dev/null || command -v google-chrome-stable &>/dev/null || pacman -Qq google-chrome &>/dev/null 2>&1 || (flatpak list --app 2>/dev/null | grep -qi "com.google.Chrome"); then
            target_browsers+=(chrome)
        fi
        if command -v microsoft-edge &>/dev/null || command -v microsoft-edge-stable &>/dev/null || pacman -Qq microsoft-edge-stable-bin &>/dev/null 2>&1; then
            target_browsers+=(edge)
        fi
    fi

    if [ ${#target_browsers[@]} -eq 0 ]; then
        print_info "No supported web browser selected or detected on the system. Skipping browser extension provisioning."
        return 0
    fi

    print_step "Provisioning Browser Extensions"
    set_gui_progress 0.45 "Configuring Browser Extensions" "Setting up enterprise extension policies..."
    print_info "Configuring extensions for target browser(s): ${target_browsers[*]}"

    local ext_json_list
    ext_json_list=$(printf '%s\n' "${browser_extensions[@]}" | "$PYTHON_BIN" -c "import sys, json; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))")

    local has_chromium_targets=0
    local has_firefox_targets=0
    local chrom_paths=()
    local ff_paths=()

    for tb in "${target_browsers[@]}"; do
        case "$tb" in
            brave)
                chrom_paths+=("/etc/brave/policies/managed/class_extensions.json")
                has_chromium_targets=1
                ;;
            chromium)
                chrom_paths+=("/etc/chromium/policies/managed/class_extensions.json")
                has_chromium_targets=1
                ;;
            chrome)
                chrom_paths+=("/etc/opt/chrome/policies/managed/class_extensions.json")
                has_chromium_targets=1
                ;;
            vivaldi)
                chrom_paths+=("/etc/vivaldi/policies/managed/class_extensions.json")
                has_chromium_targets=1
                ;;
            edge)
                chrom_paths+=("/etc/opt/edge/policies/managed/class_extensions.json")
                has_chromium_targets=1
                ;;
            firefox)
                ff_paths+=(
                    "/usr/lib/firefox/distribution/policies.json"
                    "/etc/firefox/policies/policies.json"
                )
                has_firefox_targets=1
                ;;
        esac
    done

    # Generate policy files using python in /tmp
    "$PYTHON_BIN" - <<EOF
import json
import os

selected = set(json.loads('''$ext_json_list'''))
has_chromium = bool(int('''$has_chromium_targets'''))
has_firefox = bool(int('''$has_firefox_targets'''))

EXT_DATA = {
    "return-youtube-dislike": (
        "gebbhagfogifgggkldgodflihgfeippi",
        "{762f9885-5a13-4abd-9c77-433dcd38b8fd}",
        "https://addons.mozilla.org/firefox/downloads/latest/return-youtube-dislikes/latest.xpi"
    ),
    "sponsorblock": (
        "mnjggcdmjocbbbhaepdhchncahnbgone",
        "sponsorBlocker@ajay.app",
        "https://addons.mozilla.org/firefox/downloads/latest/sponsorblock/latest.xpi"
    ),
    "adblock-for-youtube": (
        "cmedhionkhpnakcndndgjdbohmhepckk",
        "jid1-q4sG8pYhq8KGHs@jetpack",
        "https://addons.mozilla.org/firefox/downloads/latest/adblock-for-youtube/latest.xpi"
    ),
    "darkreader": (
        "eimadpbcbfnmbkopoojfekhnkhdbieeh",
        "addon@darkreader.org",
        "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi"
    ),
    "consent-o-matic": (
        "mljpablpbeekflopdjnioimmkigebmhi",
        "gdpr@cavi.au.dk",
        "https://addons.mozilla.org/firefox/downloads/latest/consent-o-matic/latest.xpi"
    ),
    "adnauseam": (
        "",
        "adnauseam@rednoise.org",
        "https://addons.mozilla.org/firefox/downloads/latest/adnauseam/latest.xpi"
    ),
    "microsoft-to-microslop": (
        "hlkljlkdinjnbfmclionhbefbnefcgll",
        "microsoft-to-microslop@example.com",
        "https://addons.mozilla.org/firefox/downloads/latest/microsoft-to-microslop/latest.xpi"
    ),
    "hola-vpn": (
        "gkojfkhlekighikafcpjkiklfbnlmeio",
        "",
        ""
    ),
}

# Chromium policies
if has_chromium:
    chromium_exts = {}
    for k in selected:
        if k in EXT_DATA:
            cid, _, _ = EXT_DATA[k]
            if cid:
                chromium_exts[cid] = {
                    "installation_mode": "normal_installed",
                    "update_url": "https://clients2.google.com/service/update2/crx"
                }

    with open("/tmp/class_chromium_policy.json", "w") as f:
        json.dump({"ExtensionSettings": chromium_exts}, f, indent=2)

# Firefox policies
if has_firefox:
    firefox_exts = {}
    for k in selected:
        if k in EXT_DATA:
            _, f_guid, f_url = EXT_DATA[k]
            if f_guid and f_url:
                firefox_exts[f_guid] = {
                    "installation_mode": "normal_installed",
                    "install_url": f_url
                }

    with open("/tmp/class_firefox_policy.json", "w") as f:
        json.dump({"policies": {"ExtensionSettings": firefox_exts}}, f, indent=2)

EOF

    # Install Chromium policies into targeted directories only
    if [ "$has_chromium_targets" -eq 1 ] && [ -f /tmp/class_chromium_policy.json ]; then
        for p in "${chrom_paths[@]}"; do
            if sudo install -D -m 644 /tmp/class_chromium_policy.json "$p" 2>/dev/null; then
                print_success "Configured Chromium extension policy in $p"
            fi
        done
    fi

    # Install Firefox policies into targeted directories only
    if [ "$has_firefox_targets" -eq 1 ] && [ -f /tmp/class_firefox_policy.json ]; then
        for p in "${ff_paths[@]}"; do
            if sudo install -D -m 644 /tmp/class_firefox_policy.json "$p" 2>/dev/null; then
                print_success "Configured Firefox extension policy in $p"
            fi
        done
    fi

    rm -f /tmp/class_chromium_policy.json /tmp/class_firefox_policy.json

    # Sideload AdNauseam for Chromium/Brave if selected and a Chromium-based browser is targeted
    if [[ " ${browser_extensions[*]} " =~ " adnauseam " ]] && [ "$has_chromium_targets" -eq 1 ]; then
        local adn_dir="$HOME/.local/share/adnauseam"
        mkdir -p "$adn_dir"
        print_info "Downloading latest AdNauseam package for Chromium/Brave..."
        if curl -sL "https://github.com/dhowe/AdNauseam/releases/latest/download/adnauseam.chromium.zip" -o /tmp/adnauseam.zip; then
            if command -v unzip &>/dev/null; then
                unzip -qo /tmp/adnauseam.zip -d "$adn_dir" 2>/dev/null || true
            else
                "$PYTHON_BIN" -c "import zipfile; zipfile.ZipFile('/tmp/adnauseam.zip').extractall('$adn_dir')" 2>/dev/null || true
            fi
            rm -f /tmp/adnauseam.zip
            cat > "$adn_dir/README.txt" << 'EOF'
AdNauseam is downloaded and unpacked in this directory.
To enable in Brave / Chromium:
1. Open brave://extensions or chrome://extensions
2. Enable "Developer mode" (toggle top right)
3. Click "Load unpacked" and select this folder (~/.local/share/adnauseam)
EOF
            print_success "AdNauseam extension unpacked in $adn_dir"
        else
            print_warning "Failed to download AdNauseam release package."
        fi
    fi

    # Clean up empty policy directories for browsers not installed or targeted
    for untargeted in brave chrome vivaldi; do
        if ! [[ " ${target_browsers[*]} " =~ " $untargeted " ]]; then
            local orphan_path=""
            case "$untargeted" in
                brave) orphan_path="/etc/brave/policies/managed/class_extensions.json" ;;
                chrome) orphan_path="/etc/opt/chrome/policies/managed/class_extensions.json" ;;
                vivaldi) orphan_path="/etc/vivaldi/policies/managed/class_extensions.json" ;;
            esac
            if [ -n "$orphan_path" ] && [ -f "$orphan_path" ]; then
                sudo rm -f "$orphan_path"
                sudo rmdir -p "$(dirname "$orphan_path")" 2>/dev/null || true
            fi
        fi
    done

    print_success "Browser extensions configured successfully."
}

# -----------------------------
# Install everything
# -----------------------------
print_step "Starting Installation"
set_gui_progress 0.05 "Preparing Installation" "Configuring package managers and driver repositories..."

if [ ${#core_pkgs[@]} -gt 0 ]; then
    print_info "Ensuring core system packages are installed (${core_pkgs[*]})..."
    set_gui_progress 0.10 "Core System" "Ensuring core system packages are installed..."
    run_install "${core_pkgs[@]}" || print_warning "Core installation had errors."
fi

if [ ${#gpu_pkgs[@]} -gt 0 ]; then
    print_info "Installing GPU drivers..."
    set_gui_progress 0.20 "Installing GPU Drivers" "Installing detected GPU drivers..."
    run_install "${gpu_pkgs[@]}" || print_warning "GPU driver installation had errors."
fi

if [ ${#browser_pkg[@]} -gt 0 ]; then
    print_info "Installing browser..."
    b_pkg="${browser_pkg[0]}"
    set_gui_progress 0.35 "Installing Web Browser" "Installing $b_pkg..."
    print_info "Attempting to install $b_pkg via pacman/yay..."
    if ! run_install "$b_pkg"; then
        print_warning "$b_pkg installation via pacman/yay failed. Falling back to Flatpak..."
        
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo || true
        
        flatpak_id=""
        case "$b_pkg" in
            brave-origin-bin|brave-bin) flatpak_id="com.brave.Browser" ;;
            firefox) flatpak_id="org.mozilla.firefox" ;;
            chromium) flatpak_id="org.chromium.Chromium" ;;
            vivaldi) flatpak_id="com.vivaldi.Vivaldi" ;;
            google-chrome) flatpak_id="com.google.Chrome" ;;
            opera-gx) flatpak_id="com.opera.GX" ;;
            microsoft-edge-stable-bin) flatpak_id="com.microsoft.Edge" ;;
        esac
        
        if [ -n "$flatpak_id" ]; then
            print_info "Installing $flatpak_id via Flathub..."
            if flatpak install -y flathub "$flatpak_id" 2>&1 | tee -a "$LOG_FILE"; then
                print_success "Installed $b_pkg successfully via Flatpak ($flatpak_id)."
            else
                print_error "Failed to install $b_pkg via both native and Flatpak channels."
            fi
        else
            print_error "No Flatpak fallback found for browser: $b_pkg"
        fi
    else
        print_success "Installed $b_pkg successfully."
    fi
fi

configure_browser_extensions

if [ ${#main_pkgs[@]} -gt 0 ]; then
    if [[ " ${main_pkgs[*]} " =~ " gamemode " ]]; then
        if [[ ! " ${main_pkgs[*]} " =~ " lib32-gamemode " ]]; then
            main_pkgs+=(lib32-gamemode)
        fi
    fi

    print_info "Installing main application packages..."
    set_gui_progress 0.55 "Installing Applications" "Installing ${#main_pkgs[@]} application package(s)..."
    run_install "${main_pkgs[@]}" || print_warning "Application installation had errors."
fi

if [ ${#emu_pkgs[@]} -gt 0 ]; then
    print_info "Installing emulators..."
    set_gui_progress 0.70 "Installing Emulators" "Installing ${#emu_pkgs[@]} emulator package(s)..."
    run_install "${emu_pkgs[@]}" || print_warning "Some emulators failed to install."
fi

if [ ${#aur_pkgs[@]} -gt 0 ]; then
    print_info "Installing custom AUR packages..."
    set_gui_progress 0.82 "Installing Custom AUR Packages" "Installing ${#aur_pkgs[@]} package(s) from AUR..."
    run_install "${aur_pkgs[@]}" || print_warning "Some custom AUR packages failed to install."
fi

# -----------------------------
# Flatpak Installation
# -----------------------------
if [ ${#flatpak_pkgs[@]} -gt 0 ]; then
    print_step "Installing Flatpak Applications"
    set_gui_progress 0.90 "Installing Flatpak Packages" "Installing Flathub packages (${flatpak_pkgs[*]})..."
    print_info "Ensuring Flathub remote is configured..."
    flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>&1 | tee -a "$LOG_FILE" || true
    for fp in "${flatpak_pkgs[@]}"; do
        print_info "Installing $fp via Flatpak..."
        flatpak install -y flathub "$fp" 2>&1 | tee -a "$LOG_FILE" || true
    done
fi

# -----------------------------
# Extras & Finalizing
# -----------------------------
print_step "Applying Extras & Finalizing"
set_gui_progress 0.96 "Finalizing System Configuration" "Enabling user services and creating helper tools..."

if [[ " ${main_pkgs[*]} " =~ " gamemode " ]]; then
    print_info "Enabling GameMode user service..."
    systemctl --user enable --now gamemoded || true
fi

SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd || true)"
fi
if [ -z "$SCRIPT_DIR" ]; then
    SCRIPT_DIR="$(pwd)"
fi

# Install Vencord script if selected
if [[ " ${script_pkgs[*]} " =~ " vencord " ]]; then
    print_info "Installing Vencord script..."
    vencord_src="$SCRIPT_DIR/vencord"
    if [ ! -f "$vencord_src" ]; then
        vencord_src="/tmp/vencord"
        curl -sL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/Cryptorial0/CLASS/master/vencord?$(date +%s)" -o "$vencord_src" 2>/dev/null || true
    fi
    if [ -f "$vencord_src" ]; then
        sudo cp "$vencord_src" /usr/local/bin/vencord
        sudo chmod +x /usr/local/bin/vencord
        mkdir -p "$HOME/.local/bin"
        cp "$vencord_src" "$HOME/.local/bin/vencord"
        chmod +x "$HOME/.local/bin/vencord"
        print_success "Installed vencord script in /usr/local/bin/vencord"
    else
        print_warning "Failed to locate or download vencord script."
    fi
fi

# Install SLSsteam script if selected
if [[ " ${script_pkgs[*]} " =~ " slssteam " ]]; then
    print_info "Installing SLSsteam script..."
    slssteam_src="$SCRIPT_DIR/slssteam"
    if [ ! -f "$slssteam_src" ]; then
        slssteam_src="/tmp/slssteam"
        curl -sL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/Cryptorial0/CLASS/master/slssteam?$(date +%s)" -o "$slssteam_src" 2>/dev/null || true
    fi
    if [ -f "$slssteam_src" ]; then
        sudo cp "$slssteam_src" /usr/local/bin/slssteam
        sudo chmod +x /usr/local/bin/slssteam
        mkdir -p "$HOME/.local/bin"
        cp "$slssteam_src" "$HOME/.local/bin/slssteam"
        chmod +x "$HOME/.local/bin/slssteam"
        print_success "Installed slssteam script in /usr/local/bin/slssteam"
    else
        print_warning "Failed to locate or download slssteam script."
    fi
fi

# Install fix-ntfs script if selected
if [[ " ${script_pkgs[*]} " =~ " fix-ntfs " ]]; then
    print_info "Installing NTFS Disk Repair tool (fix-ntfs)..."
    fixntfs_src="$SCRIPT_DIR/fix-ntfs"
    if [ ! -f "$fixntfs_src" ]; then
        fixntfs_src="/tmp/fix-ntfs"
        curl -sL -H "Cache-Control: no-cache" "https://raw.githubusercontent.com/Cryptorial0/CLASS/master/fix-ntfs?$(date +%s)" -o "$fixntfs_src" 2>/dev/null || true
    fi
    if [ -f "$fixntfs_src" ]; then
        sudo cp "$fixntfs_src" /usr/local/bin/fix-ntfs
        sudo chmod +x /usr/local/bin/fix-ntfs
        mkdir -p "$HOME/.local/bin"
        cp "$fixntfs_src" "$HOME/.local/bin/fix-ntfs"
        chmod +x "$HOME/.local/bin/fix-ntfs"

        # Also create desktop entry for application menu
        sudo bash -c 'cat > /usr/share/applications/fix-ntfs.desktop <<\EOF
[Desktop Entry]
Name=NTFS Disk Repair & Mount
Comment=Repair and auto-mount dirty or unmountable NTFS drives
Exec=fix-ntfs
Icon=drive-harddisk
Terminal=true
Type=Application
Categories=System;Utility;
Keywords=ntfs;disk;repair;mount;fix;
EOF'
        sudo chmod 644 /usr/share/applications/fix-ntfs.desktop 2>/dev/null || true
        print_success "Installed fix-ntfs in /usr/local/bin/fix-ntfs (and created desktop launcher)"
    else
        print_warning "Failed to locate or download fix-ntfs script."
    fi
fi

print_info "Creating yayf AUR search helper command..."
sudo bash -c 'cat > /usr/local/bin/yayf <<\EOF
#!/usr/bin/env bash
set -euo pipefail

if ! command -v fzf &>/dev/null; then
    echo "fzf is required for yayf. Please install it with: sudo pacman -S fzf"
    exit 1
fi

fzf_args=(
    --multi
    --prompt="AUR Search > "
    --header="[TAB]: Multi-select | [ENTER]: Install | [ESC]: Exit | [ALT-P]: Toggle Info"
    --preview="yay -Siia {1}"
    --preview-label="alt-p: toggle description, alt-b/B: toggle PKGBUILD, alt-j/k: scroll, tab: multi-select"
    --preview-label-pos="bottom"
    --preview-window="down:65%:wrap"
    --bind="alt-p:toggle-preview"
    --bind="alt-d:preview-half-page-down,alt-u:preview-half-page-up"
    --bind="alt-k:preview-up,alt-j:preview-down"
    --bind="alt-b:change-preview:yay -Gpa {1} | tail -n +5"
    --bind="alt-B:change-preview:yay -Siia {1}"
    --color="pointer:green,marker:green"
)

selected_pkgs=$(yay -Slqa | fzf "${fzf_args[@]}" || true)
if [ -n "$selected_pkgs" ]; then
    echo "$selected_pkgs" | tr "\n" " " | xargs yay -S
fi
EOF'
sudo chmod +x /usr/local/bin/yayf
print_success "Created executable yayf helper in /usr/local/bin/yayf"


# -----------------------------
# Finish
# -----------------------------
set_gui_progress 1.00 "Setup Complete!" "All packages and configurations deployed successfully. System reboot recommended." "complete"

print_step "Setup Complete!"
print_success "All requested packages and configurations have been deployed."
print_info "Log file saved to: ${BWHITE}$LOG_FILE${NC}"
print_info "A system reboot is highly recommended."
echo ""

if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    if command -v notify-send &>/dev/null; then
        notify-send "Cryptorial's Lazy Arch Setup Script" "Setup completed successfully! A system reboot is recommended." -i system-software-install || true
    fi
fi

if [ "$USE_GUI" -eq 1 ] && [ -n "${GUI_PID:-}" ] && kill -0 "$GUI_PID" 2>/dev/null; then
    wait "$GUI_PID" 2>/dev/null || true
fi
