import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

class VaultManager:
    """
    RetroVault Directory Structure Manager. 
    Its mission: To find game folders, parse assets and complete missing structures.
    """
    
    # Standard Subfolders
    SUBFOLDERS = {
        "covers": ["Covers", "Cover", "BoxArt"],
        "shots": ["Shots", "Screenshots", "Screen"],
        "captures": ["Captures", "RawCaptures", "EditedVideos"],
        "manuals": ["Manuals", "Manual", "Docs"],
        "media": ["MEDIA", "Gamefiles"]
    }
    
    # Translate the "Platform" column from the TOSEC DAT files into folder structure.
    PLATFORM_MAPPING = {
        "Commodore 64": "C64",
        "Commodore Amiga": "Amiga",
        "Amstrad CPC": "Amstrad CPC",
        "Sinclair ZX Spectrum": "Spectrum ZX",
        "IBM PC Compatibles": "PC",
        "DOS": "DOS", 
        "ScummVM": "ScummVM",
        "Atari ST": "Atari ST",
        "Atari 8bit": "Atari 8bit"
    }

    def __init__(self, root_path: str):
        
        self.root = Path(root_path) if root_path else None
        self.games_root = self.root / "Games" if self.root else None

    def is_valid(self) -> bool:
        
        """Is the Vault root directory valid?"""
        return self.root and self.root.exists() and self.games_root.exists()

    def ensure_structure(self) -> List[str]:
        """
        It completes the missing A-Z folders. 
        Return: List of created folders.
        """
        if not self.root:
            raise ValueError("Vault path not set")

        created = []
        
        # Main Games folder
        if not self.games_root.exists():
            self.games_root.mkdir(parents=True)
            created.append(str(self.games_root))

        # 0-9 vand A-Z folders
        prefixes = ["0-9"] + [chr(i) for i in range(ord('A'), ord('Z') + 1)]
        
        for prefix in prefixes:
            p_path = self.games_root / prefix
            if not p_path.exists():
                p_path.mkdir()
                created.append(str(p_path))
                
        return created

    def find_game_assets(self, game_title: str) -> Dict[str, List[str]]:
        """
        Based on the given game name (ex: "Boulder Dash") 
        Searches in Vault and returns Asset paths.
        """
        if not self.is_valid():
            return {}

        # Find Game Folder (like Games/B/Boulder Dash...) 
        # For now, doing a simple search. Fuzzy Search may be added in the future.
        target_folder = self._locate_game_folder(game_title)
        
        if not target_folder:
            return {}

        # 2. Scan assets
        assets = {
            "root": str(target_folder),
            "covers": [],
            "shots": [],
            "manuals": [],
            "media_path": ""
        }

        # Look at everything in the folder
        for item in target_folder.iterdir():
            if not item.is_dir():
                continue
            
            name = item.name
            
            # Covers
            if any(name.startswith(x) for x in self.SUBFOLDERS["covers"]):
                assets["covers"].extend(self._scan_images(item))
            
            # Shots (Shots, Shots (C64) vb. hepsini yakalar)
            elif any(name.startswith(x) for x in self.SUBFOLDERS["shots"]):
                assets["shots"].extend(self._scan_images(item))
                
            # Manuals
            elif any(name.startswith(x) for x in self.SUBFOLDERS["manuals"]):
                assets["manuals"].append(str(item)) # Klasör yolunu dönüyoruz
            
            # MEDIA
            elif name in self.SUBFOLDERS["media"]:
                assets["media_path"] = str(item)

        return assets

    def find_playable_media(self, title: str, system: str) -> Optional[str]:
        """
        Find the game's executable file according to the specified rules.

        Rule 1: Look under MEDIA/Gamefiles/<platform>.
        Rule 2: Ignore the TOSEC folder (do not perform a recursive search).
        """
        if not self.is_valid():
            return None

        # Find the game's main folder.
        game_folder = self._locate_game_folder(title)
        if not game_folder:
            return None

        target_platform_dir = self.PLATFORM_MAPPING.get(system)
        # If we couldn't find it in the mapping, maybe it's listed as "C64" in the database.
        if not target_platform_dir:
            target_platform_dir = system

        media_path = game_folder / "MEDIA" / "Gamefiles" / target_platform_dir
        
        if not media_path.exists():
            return None

        playable_extensions = {'.adf', '.d64', '.t64', '.tap', '.ipf', '.zip', '.7z', '.exe', '.com', '.bat', '.iso', '.cue'}
        
        candidates = []
        
        for item in media_path.iterdir():
            if item.is_file():
                if item.suffix.lower() in playable_extensions:
                    candidates.append(item)
        
        if not candidates:
            return None

        candidates.sort(key=lambda f: f.name.lower())
        
        for cand in candidates:
            if cand.suffix.lower() == '.m3u':
                return str(cand)
        
        return str(candidates[0])

    def _locate_game_folder(self, title: str) -> Optional[Path]:
        """
        Searches for the game under Games/A...Z. 
        First it looks for the initial (for speed), if it can't find it, it scans everywhere? 
        For now, let's just look at the initial letter.
        """
        if not title: 
            return None
        
        # Temiz baş harf (The Boulder Dash -> B)
        clean_title = title
        if title.lower().startswith("the "):
            clean_title = title[4:]
            
        first_char = clean_title[0].upper()
        
        # Letter or number ?
        if first_char.isdigit():
            bucket = "0-9"
        elif first_char.isalpha():
            bucket = first_char
        else:
            bucket = "0-9" # Let the symbols go to 0-9 for now

        bucket_path = self.games_root / bucket
        
        if not bucket_path.exists():
            return None

        # Fuzzy Match
        for folder in bucket_path.iterdir():
            if folder.is_dir() and title.lower() in folder.name.lower():
                return folder
        for folder in bucket_path.iterdir():
            if folder.is_dir() and title.lower() in folder.name.lower():
                return folder
                
        return None

    def _scan_images(self, folder: Path) -> List[str]:
        """Finds image files under the folder."""
        images = []
        valid_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Only that folder (not recursive, if there is a subfolder in shots, it should be checked separately) 
        # In this build, there is no need for recursive since "Shots (C64)" is a separate folder
        try:
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in valid_exts:
                    images.append(str(f))
        except Exception:
            pass
            
        return sorted(images)
