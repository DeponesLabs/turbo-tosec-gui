import os
import subprocess
import platform

class Launcher:
    """
    Responsible for launching game files with the relevant emulator.
    """
    
    # Platform-specific argument templates
    # Emulators sometimes don't just accept the file path, they require a flag.
    # Fill in {game_path} and {emulator_dir} placeholders in the code.
    LAUNCH_ARGS = {
        "Commodore 64": ["-autostart", "{game_path}"],      # VICE
        "Commodore Amiga": ["{game_path}"],                 # WinUAE / FS-UAE
        "Amstrad CPC": ["{game_path}"],                     # WinCPC
        "Sinclair ZX Spectrum": ["{game_path}"],
        "DOS": ["-conf", "{game_path}"],
        "ScummVM": ["-p", "{game_dir}", "{game_id}"],       # ScummVM (This is complex, keep it simple for now)
        "Atari ST": ["{game_path}"],                # Steem SSE
        "Atari 8bit": ["{game_path}"]               # Altirra
    }
    
    @staticmethod
    def launch(emulator_exe: str, game_path: str, system_name: str) -> bool:
        """
        Starts the emulator and the game.

        :param emulator_exe: The path to the .exe file from the settings (e.g., C:/Emu/x64sc.exe)
        :param game_path: The game file from the Vault (e.g., D:/Vault/.../game.d64)
        :param system_name: The system name from the database (e.g., Commodore 64)
        """
        if not emulator_exe or not os.path.exists(emulator_exe):
            print(f"LAUNCH ERROR: Emulator exe not found: {emulator_exe}")
            return False
        
        if not game_path or not os.path.exists(game_path):
            print(f"LAUNCH ERROR: Game file not found: {game_path}")
            return False
        
        # Set the working directory to where the emulator is located (Important! Some emulators may not be able to find their DLLs otherwise)
        work_dir = os.path.dirname(emulator_exe)

        # Prepare command list: [exe_path, arg1, arg2, ...]
        cmd = [emulator_exe]

        # Add system-specific arguments
        # Default behavior: Only append to the end of the game file
        args_template = Launcher.LAUNCH_ARGS.get(system_name, ["{game_path}"])

        for arg in args_template:
            # Fill the placeholders
            filled_args = arg.format(game_path=game_path, game_dir=os.path.dirname(game_path))
            cmd.append(filled_args)
            
        print(f"LAUNCHING: {cmd}")
        
        try:
            # Use subprocess.Popen to prevent the program from freezing (block). 
            # # The game will open, and Skryer will continue running in the background.
            subprocess.Popen(cmd, cwd=work_dir, shell=False)
            return True
        except:
            print(f"LAUNCH EXCEPTION: {e}")
            return False
