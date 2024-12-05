#!/usr/bin/env python3

import argparse
import subprocess
import sys
import shutil
from dataclasses import dataclass

APP_ID_MAPPING = [
    # User Define
    ["footclient", "󰽒", "Foot Terminal"],
    ["popup_term", "", "Pop-up Terminal"],
    ["zen-browser", "󰈹", "Zen Browser"],
    ["musicfox", "", "Musicfox"],
]
APP_ID_MAPPING_FALLBACK = "󰣆"
DMENU_DELIMITER = " "  # Delimiter between icon and name in dmenu

### DO NOT EDIT BELOW THIS LINE  ###

APP_ID_MAPPING += [  # Original Entries
    ["kitty", "󰄛", "Kitty Terminal"],
    ["firefox", "󰈹", "Firefox"],
    ["microsoft-edge", "󰇩", "Edge"],
    ["discord", "", "Discord"],
    ["vesktop", "", "Vesktop"],
    ["org.kde.dolphin", "", "Dolphin"],
    ["plex", "󰚺", "Plex"],
    ["steam", "", "Steam"],
    ["spotify", "󰓇", "Spotify"],
    ["ristretto", "󰋩", "Ristretto"],
    ["obsidian", "󱓧", "Obsidian"],
    # Browsers
    ["google-chrome", "", "Google Chrome"],
    ["brave-browser", "󰖟", "Brave Browser"],
    ["chromium", "", "Chromium"],
    ["opera", "", "Opera"],
    ["vivaldi", "󰖟", "Vivaldi"],
    ["waterfox", "󰖟", "Waterfox"],
    ["thorium", "󰖟", "Waterfox"],
    ["tor-browser", "", "Tor Browser"],
    ["floorp", "󰈹", "Floorp"],
    # Terminals
    ["gnome-terminal", "", "GNOME Terminal"],
    ["konsole", "", "Konsole"],
    ["alacritty", "", "Alacritty"],
    ["wezterm", "", "Wezterm"],
    ["foot", "󰽒", "Foot Terminal"],
    ["tilix", "", "Tilix"],
    ["xterm", "", "XTerm"],
    ["urxvt", "", "URxvt"],
    ["st", "", "st Terminal"],
    # Development Tools
    ["code", "󰨞", "Visual Studio Code"],
    ["vscode", "󰨞", "VS Code"],
    ["sublime-text", "", "Sublime Text"],
    ["atom", "", "Atom"],
    ["android-studio", "󰀴", "Android Studio"],
    ["intellij-idea", "", "IntelliJ IDEA"],
    ["pycharm", "󱃖", "PyCharm"],
    ["webstorm", "󱃖", "WebStorm"],
    ["phpstorm", "󱃖", "PhpStorm"],
    ["eclipse", "", "Eclipse"],
    ["netbeans", "", "NetBeans"],
    ["docker", "", "Docker"],
    ["vim", "", "Vim"],
    ["neovim", "", "Neovim"],
    ["neovide", "", "Neovide"],
    ["emacs", "", "Emacs"],
    # Communication Tools
    ["slack", "󰒱", "Slack"],
    ["telegram-desktop", "", "Telegram"],
    ["org.telegram.desktop", "", "Telegram"],
    ["whatsapp", "󰖣", "WhatsApp"],
    ["teams", "󰊻", "Microsoft Teams"],
    ["skype", "󰒯", "Skype"],
    ["thunderbird", "", "Thunderbird"],
    # File Managers
    ["nautilus", "󰝰", "Files (Nautilus)"],
    ["thunar", "󰝰", "Thunar"],
    ["pcmanfm", "󰝰", "PCManFM"],
    ["nemo", "󰝰", "Nemo"],
    ["ranger", "󰝰", "Ranger"],
    ["doublecmd", "󰝰", "Double Commander"],
    ["krusader", "󰝰", "Krusader"],
    # Media Players
    ["vlc", "󰕼", "VLC Media Player"],
    ["mpv", "", "MPV"],
    ["rhythmbox", "󰓃", "Rhythmbox"],
    # Graphics Tools
    ["gimp", "", "GIMP"],
    ["inkscape", "", "Inkscape"],
    ["krita", "", "Krita"],
    ["blender", "󰂫", "Blender"],
    # Video Editing
    ["kdenlive", "", "Kdenlive"],
    # Games and Gaming Platforms
    ["lutris", "󰺵", "Lutris"],
    ["heroic", "󰺵", "Heroic Games Launcher"],
    ["minecraft", "󰍳", "Minecraft"],
    ["csgo", "󰺵", "CS:GO"],
    ["dota2", "󰺵", "Dota 2"],
    # Office and Productivity
    ["evernote", "", "Evernote"],
    ["sioyek", "", "Sioyek"],
    # Cloud Services and Sync
    ["dropbox", "󰇣", "Dropbox"],
    # Desktop
    ["^$", "󰇄", "Desktop"],
]


@dataclass
class WindowData:
    id: str
    app_id: str
    name: str


@dataclass
class Windows:
    windows: list[WindowData]

    def append(self, window: WindowData):
        self.windows.append(window)

    def map_app_id(self):
        """Map app_id to a human-readable name based on the given mapping."""

        # Convert to dict for fast lookup
        mapping_dict = {
            item[0]: f"{item[1]}{DMENU_DELIMITER}{item[2]}" for item in APP_ID_MAPPING
        }

        for window in self.windows:
            if window.app_id in mapping_dict:
                # Replace app_id with human-readable name
                window.app_id = mapping_dict[window.app_id]
            else:
                # Use fallback icon
                window.app_id = (
                    f"{APP_ID_MAPPING_FALLBACK}{DMENU_DELIMITER}{window.app_id}"
                )

    def construct_dmenu_list(self, is_map=True) -> str:
        """Construct a string from windows list for dmenu."""
        if is_map:
            self.map_app_id()
            return "\n".join(f"{win.app_id}: {win.name}" for win in self.windows)
        else:
            return "\n".join(
                f"{win.id} {win.app_id}: {win.name}" for win in self.windows
            )

    def get_id_by_index(self, index):
        return self.windows[int(index)].id


def get_windows(LAUNCHER, window_type):
    """Get the list of windows based on the specified type."""
    swaymsg_command = "swaymsg -t get_tree"
    if window_type == "all":
        jq_filter = (
            "recurse(.nodes[]?) | recurse(.floating_nodes[]?) | "
            'select(.type == "con"), select(.type == "floating_con") | '
            '(.id | tostring) + "|||" + .app_id + "|||" + .name'
        )
    elif window_type == "regular":
        jq_filter = (
            'recurse(.nodes[]?) | select(.type == "con") | '
            '(.id | tostring) + "|||" + .app_id + "|||" + .name'
        )
    elif window_type == "floating":
        jq_filter = (
            ".nodes[].nodes[].floating_nodes[] | "
            '(.id | tostring) + "|||" + .app_id + "|||" + .name'
        )
    elif window_type == "scratch":
        jq_filter = (
            'recurse(.nodes[]?) | select(.name == "__i3_scratch") | '
            'recurse(.floating_nodes[]?) | select(.type == "floating_con") | '
            '(.id | tostring) + "|||" + .app_id + "|||" + .name'
        )
    else:
        raise_error_dmenu(LAUNCHER, f'Invalid type "{window_type}"')
        sys.exit(1)

    command = (
        f"{swaymsg_command} | jq -r '{jq_filter}' | grep -v '^[0-9]\\+|\\{{6\\}}$'"
    )
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        if result.stderr == "":
            raise_error_dmenu(LAUNCHER, "Warning: No Results")
        else:
            raise_error_dmenu(
                LAUNCHER, f"Error: executing command failed: {result.stderr}"
            )
        sys.exit(1)

    return parse_window_output(result.stdout)


def parse_window_output(output):
    """Parse the output of the swaymsg command into a structured list of dictionaries."""
    windows = Windows(windows=[])
    for line in output.splitlines():
        parts = line.split("|||")
        if len(parts) >= 3:
            windows.append(WindowData(id=parts[0], app_id=parts[1], name=parts[2]))
    return windows


def dmenu_fuzzel(dmenu_str, promot):
    try:
        selected = subprocess.run(
            [
                "fuzzel",
                "--dmenu",
                "--index",
                "--log-level=none",
                "--placeholder",
                f"{promot}",
            ],
            input=dmenu_str,
            text=True,
            capture_output=True,
        ).stdout.strip()

    except FileNotFoundError:
        print("Error: fuzzel is not installed.", file=sys.stderr)
        sys.exit(1)
    return selected


def dmenu_rofi(dmenu_str, promot):
    try:
        selected = subprocess.run(
            [
                "rofi",
                "-dmenu",
                "-format",
                "i",
                "-p",
                f"{promot}",
            ],
            input=dmenu_str,
            text=True,
            capture_output=True,
        ).stdout.strip()

    except FileNotFoundError:
        print("Error: rofi is not installed.", file=sys.stderr)
        sys.exit(1)
    return selected


def dmenu_run(launcher, dmenu_str, promot):
    selected_index = None
    match launcher:
        case "fuzzel":
            selected_index = dmenu_fuzzel(dmenu_str, promot)
        case "rofi":
            selected_index = dmenu_rofi(dmenu_str, promot)
    return selected_index


def raise_error_dmenu(launcher, err):
    dmenu_run(launcher, err, "")
    print(err, file=sys.stderr)


WINDOW_TPYES = ["all", "floating", "scratch", "regular"]
SUPPORTED_LAUNCHERS = ["fuzzel", "rofi"]


def main():
    parser = argparse.ArgumentParser(
        description="List and select windows using swaymsg and dmenu launchers like fuzzel and rofi."
    )
    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="all",
        choices=WINDOW_TPYES,
        help='Type of window to list. Defaults to "all".',
    )
    parser.add_argument(
        "--plain-output",
        action="store_true",
        help="Print a plain, unbeautified list to dmenu.",
    )
    parser.add_argument(
        "-l",
        "--launcher",
        type=str,
        choices=SUPPORTED_LAUNCHERS,
        help="Specific a dmenu launcher to use. Will use first exist launcher if not define.",
    )
    args = parser.parse_args()

    WINDOW_TYPE = args.type
    PLAIN_OUTPUT = args.plain_output
    LAUNCHER = args.launcher

    # If launcher not defined in cli, use first found launcher in SUPPORTED_LAUNCHERS
    if not LAUNCHER:
        for launcher in SUPPORTED_LAUNCHERS:
            if shutil.which(launcher):
                LAUNCHER = launcher
                break
    if not LAUNCHER:
        print("Error: No supported launcher is installed.", file=sys.stderr)
        sys.exit(1)

    windows = get_windows(LAUNCHER, WINDOW_TYPE)

    if not windows:
        raise_error_dmenu(LAUNCHER, "Error: No windows found")
        sys.exit(1)

    # Build dmenu list
    windows_dmenu_str = windows.construct_dmenu_list(is_map=not PLAIN_OUTPUT)
    dmenu_promot = f"{str.capitalize(WINDOW_TYPE)} Windows"

    # Run dmenu
    selected_index = dmenu_run(LAUNCHER, windows_dmenu_str, dmenu_promot)

    # Tell sway to focus said window
    if selected_index:
        window_id = windows.get_id_by_index(selected_index)
        subprocess.run(["swaymsg", f"[con_id={window_id}] focus"])


if __name__ == "__main__":
    main()
