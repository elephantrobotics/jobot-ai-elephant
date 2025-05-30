import subprocess
import re

def find_audio_card(target_name="XFMDPV0018"):
    try:
        # Execute the command "arecord -l"
        result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()

        for line in lines:
            line = line.strip()
            if target_name in line:
                return int(line[5])
    except subprocess.CalledProcessError as e:
        print(f"Failed to run arecord: {e}")

    return 3

def find_playback_card(target_name="[USB Audio Device]"):
    try:
        # Execute the command "aplay -l"
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()

        for line in lines:
            line = line.strip()
            if target_name in line:
                return int(line[5])
    except subprocess.CalledProcessError as e:
        print(f"Failed to run aplay: {e}")

    return 2