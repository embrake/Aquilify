import os
import platform

def get_environment_variables():
    return {
        var: os.getenv(var)
        for var in [
            'ALLUSERSPROFILE', 'APPDATA', 'CHROME_CRASHPAD_PIPE_NAME', 'COLORTERM', 'COMMONPROGRAMFILES',
            'COMMONPROGRAMFILES(X86)', 'COMMONPROGRAMW6432', 'COMPUTERNAME', 'COMSPEC', 'DRIVERDATA',
            'LOCALAPPDATA', 'LOGONSERVER', 'NUMBER_OF_PROCESSORS', 'ONEDRIVE', 'ONEDRIVECONSUMER',
            'ORIGINAL_XDG_CURRENT_DESKTOP'
        ]
    }

def get_user_info():
    try:
        username = os.getlogin()
    except OSError:
        username = "Unavailable"
    return {
        'Username': username,
        'Home Directory': os.path.expanduser('~'),
    }

def get_system_paths():
    return {
        'Root Directory': os.path.abspath('/'),
        'Temp Directory': os.getenv('TEMP'),
    }

def get_sys_info():
    sys_info = {
        'System': platform.system(),
        'Node Name': platform.node(),
        'Release': platform.release(),
        'Version': platform.version(),
        'Machine': platform.machine(),
        'Processor': platform.processor(),
        **get_environment_variables(),
        **get_user_info(),
        **get_system_paths(),
    }

    return sys_info