import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

# *************************************************************
# Abstract Base Class
# *************************************************************
class GameLauncher(ABC):
    """
    Base of all launchers.
    Manages common controls and the 'launch' process.
    """
    def launch(self, emulator_exe: str, game_path: str) -> bool:
        """
        Template Method.
        It performs the checks, prepares the command, and executes it.
        """
        # Common Controls
        if not self._check_paths(emulator_exe, game_path):
            return False
        
        # Prepare the command. (Sub-classes override it)
        command = self.get_launch_command(emulator_exe, game_path)
        if not command:
            print("LAUNCH ABORTED: Command generation failed.")
            return False
        
        print(f"LAUNCHING: {command}")
        
        # Run
        try:
            work_dir = os.path.dirname(emulator_exe)
            subprocess.Popen(command, cmd=work_dir, shell=False)
            return True
        
        except Exception as error:
            print(f"LAUNCH EXCEPTION: {error}")
            return False
        
    def _check_paths(self, exe: str, game: str) -> bool:
        
        if not exe or not os.path.exists(exe):
            print(f"Error: Emulator exe not found: {exe}")
            return False
        
        if not game or not os.path.exists(game):
            print(f"Error: Game file not found: {game}")
            return False
        
        return True
    
    @abstractmethod
    def get_launch_command(self, emulator_exe: str, game_path: str) -> list:
        pass
    
# *************************************************************
# Concrete Classes
# *************************************************************
class SimpleLauncher(GameLauncher):
    """
    For platforms that only work with simple arguments (C64, Atari, etc.)
    """
    def __init__(self, arg_template: list):
        
        self.arg_template = arg_template

    def get_launch_command(self, emulator_exe, game_path) -> list:
        
        cmd = [emulator_exe]
        for arg in self.arg_template:
            filled = arg.format(game_path=game_path, game_dir=os.path.dirname(game_path))
            cmd.append(filled)
        return cmd
    
class AmigaLauncher(GameLauncher):
    """
    Amiga-specific logic: Reads template, generates configuration. 
    """
    DEFAULT_ROM_NAME = "Kickstart v1.3 rev 34.5 (1987)(Commodore)(A500-A1000-A2000-CDTV).rom"
    
    def _find_vault_root(self, game_path: str) -> Path:
        """Level up in the directory from where the game is located and look for the _Skryer folder."""
        path = Path(game_path).resolve()
        for _ in range(6):
            
            if (path / "_Skryer").exists() or (path / "System").exists():
                return path
            
            if path.parent == path: break
            path = path.parent
            
        return None
        
    def _get_kickstart_path(self, vault_root: Path) -> str:
        """
        Finds the kickstart file in RetroVault/System/Commodore Amiga/ROMs and returns its path
        """
        # Dest path: RetroVault/System/Commodore Amiga/ROMs/kick13.rom
        rom_path = vault_root / "System" / "Commodore Amiga" / "ROMs" / self.DEFAULT_ROM_NAME
        
        if rom_path.exists():
            return str(rom_path.absolute())
        else:
            print(f"KICKSTART NOT FOUND: {rom_path}")
            return None
        
    def _create_config(self, game_path: str, vault_root: Path) -> str:
        
        try:
            game_file = Path(game_path)
            game_name = game_file.stem
            
            template_path = vault_root / "_Skryer" / "Commodore Amiga" / "Templates" / "Default.uae"
            configs_dir = vault_root / "_Skryer" / "Commodore Amiga" / "Configs"
            target_config_path = configs_dir / f"{game_name}.uae"

            kickstart_path = self._get_kickstart_path(vault_root)
            
            # If no ROM is found, warn you but still proceed (Perhaps the user will select it manually)
            if not kickstart_path:
                print("WARNING: Kickstart ROM not found, config will be incomplete.")
                kickstart_path = ""

            configs_dir.mkdir(parents=True, exist_ok=True)

            if not template_path.exists():
                print(f"Template not found: {template_path}")
                return None

            new_lines = []
            with open(template_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    
                    if stripped.startswith("floppy0="):
                        new_lines.append(f"floppy0={game_file.absolute()}\n")
                    elif "{kickstart_path}" in line:
                         filled_line = line.replace("{kickstart_path}", kickstart_path)
                         new_lines.append(filled_line)
                    elif stripped.startswith("kickstart_rom_file="):
                        new_lines.append(f"kickstart_rom_file={kickstart_path}\n")
                    else:
                        new_lines.append(line)

            with open(target_config_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            return str(target_config_path)

        except Exception as e:
            print(f"Config Generation Failed: {e}")
            return None

    def get_launch_command(self, emulator_exe: str, game_path: str) -> list:
        
        vault_root = self._find_vault_root(game_path)
        config_path = None
        
        if vault_root:
            config_path = self._create_config(game_path, vault_root)
        
        if config_path:
            # Run with config
            return [emulator_exe, "-f", config_path]
        else:
            print("CRITICAL: Amiga launch aborted. Template not found or Config generation failed.")
            return None

# *************************************************************
# 3. FACTORY (FABRİKA & FACADE)
# *************************************************************
class Launcher:
    """
    Dış dünyadan erişilen tek nokta.
    Hangi sistemi çalıştıracağını bilir ve doğru işçiyi (Launcher) çağırır.
    """
    
    # Basit sistemlerin argüman haritası
    SIMPLE_ARGS = {
        "Commodore 64": ["-autostart", "{game_path}"],
        "Amstrad CPC": ["{game_path}"],
        "Sinclair ZX Spectrum": ["{game_path}"],
        "DOS": ["-conf", "{game_path}"],
        "Atari ST": ["{game_path}"],
        "Atari 8bit": ["{game_path}"]
    }

    @staticmethod
    def launch(emulator_exe: str, game_path: str, platform: str) -> bool:
        
        runner = None
        
        # Which launcher class is required ?
        if platform == "Commodore Amiga":
            runner = AmigaLauncher()
            
        elif platform in Launcher.SIMPLE_ARGS:
            args = Launcher.SIMPLE_ARGS[platform]
            runner = SimpleLauncher(args)
            
        else:
            # Bilinmeyen sistem, varsayılan davranış
            print(f"Unknown platform '{platform}', trying generic launch.")
            runner = SimpleLauncher(["{game_path}"])

        # 2. İşçiye işi devret
        return runner.launch(emulator_exe, game_path)
