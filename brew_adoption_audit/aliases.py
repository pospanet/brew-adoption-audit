from __future__ import annotations

BUNDLE_ID_TO_CASK: dict[str, str] = {
    "com.microsoft.VSCode": "visual-studio-code",
    "com.docker.docker": "docker-desktop",
    "com.googlecode.iterm2": "iterm2",
    "com.raycast.macos": "raycast",
    "com.mikrotik.winbox": "winbox",
    "com.figma.Desktop": "figma",
    "com.obsproject.obs-studio": "obs",
    "com.raspberrypi.rpi-imager": "raspberry-pi-imager",
    "com.raspberrypi.imagingutility": "raspberry-pi-imager",
    "com.microsoft.edgemac": "microsoft-edge",
    "com.microsoft.OneDrive": "onedrive",
    "com.microsoft.teams2": "microsoft-teams",
    "com.parallels.desktop.console": "parallels",
    "com.parallels.toolbox": "parallels-toolbox",
    "com.spotify.client": "spotify",
    "com.openai.chat": "chatgpt",
    "com.openai.atlas": "chatgpt-atlas",
    "com.exafunction.windsurf": "devin-desktop",
    "ai.devin.desktop": "devin-desktop",
    "com.devin.desktop": "devin-desktop",
    "com.windsurf.editor": "windsurf",
    "com.electron.realtimeboard": "miro",
    "com.techsmith.camtasia2024": "camtasia",
}

VENDOR_MANAGED_BUNDLE_PREFIXES: tuple[str, ...] = (
    "com.microsoft.Word",
    "com.microsoft.Excel",
    "com.microsoft.Powerpoint",
    "com.microsoft.PowerPoint",
    "com.microsoft.Outlook",
    "com.microsoft.onenote.mac",
    "com.microsoft.wdav",
)


def is_vendor_managed(bundle_id: str) -> bool:
    return any(bundle_id.startswith(prefix) for prefix in VENDOR_MANAGED_BUNDLE_PREFIXES)
