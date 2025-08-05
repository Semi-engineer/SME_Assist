# File: app_config.py (Updated for One-File EXE)
import sys
import os

def get_base_path():
    """ 
    Get the absolute path to the application's base directory.
    Works for normal script, one-folder EXE, and one-file EXE.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (e.g., by PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            # This is the case for a one-file executable.
            # _MEIPASS is the path to the temporary directory.
            return sys._MEIPASS
        else:
            # This is the case for a one-folder executable.
            return os.path.dirname(sys.executable)
    else:
        # If run as a normal Python script
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# Define absolute paths for all data files using the correct base path
DATABASE_PATH = os.path.join(BASE_PATH, 'SME_Assist.db')
CONFIG_PATH = os.path.join(BASE_PATH, 'config.json')
LANG_DIR = os.path.join(BASE_PATH, 'lang')
TEMPLATES_DIR = os.path.join(BASE_PATH, 'templates')
ICON_PATH = os.path.join(BASE_PATH, 'assets', 'app_icon.ico')