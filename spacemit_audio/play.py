import os
import threading
import subprocess
from playsound import playsound

# Private Module Variables
_play_device = 'plughw:0,0'


# ===== Global device control =====
def set_play_device(dev):
    global _play_device
    _play_device = dev
    print(f"[INFO] Playback device set to: {_play_device}")

def get_play_device():
    return _play_device


# ===== Basic playback function (Blocking) =====
def play_audio(wav_file_path):
    try:
        if os.path.exists(wav_file_path):
            playsound(wav_file_path)
        else:
            print(f"{wav_file_path} does not exist")
    except Exception as e:
        print(f"An error occurred while trying to play the audio file: {e}")


# ===== Aplay playback (blocked) =====
def play_wav(path, device=None, volume='80%'):
    device = device or get_play_device()
    number = device.split(":")[1].split(",")[0]

    cmd = f'amixer -c {number} set PCM {volume}'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f'Set playback volume to {volume}, return code = {proc.returncode}')

    cmd = f'aplay -D {device} {path}'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f'Play {path} on {device}, return code = {proc.returncode}')


# ===== Aplay playback (Non-blocking) =====
def play_wav_non_blocking(path, device=None, volume='80%'):
    device = device or get_play_device()
    number = device.split(":")[1].split(",")[0]

    cmd = f'amixer -c {number} set PCM {volume}'
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f'Set playback volume to {volume}, return code = {proc.returncode}')

    cmd = f'aplay -D {device} {path}'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f'Playing {path} on {device} (PID={proc.pid})')

    return proc


# ===== Thread playback (blocking playback encapsulation) =====
def play_audio_in_thread(wav_file_path, device=None, volume='100%'):
    thread = threading.Thread(target=play_wav, args=(wav_file_path, device, volume))
    thread.start()
    return thread
