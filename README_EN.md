# jobot-ai-elephant

myCobot280 RISCV Smart Retail Scene System

## Install the Code

- Use git
  
```bash
git clone  https://github.com/elephantrobotics/jobot-ai-elephant.git
```

- [Download version](https://github.com/elephantrobotics/jobot-ai-elephant/releases)

## Environment Setup

```bash
sudo apt install -y \
    spacemit-ollama-toolkit \
    portaudio19-dev \
    python3-dev \
    libopenblas-dev \
    ffmpeg \
    python3-venv \
    python3-spacemit-ort \
    libceres-dev \
    libopencv-dev
```

## Large Model Dependency Installation

```bash
cd ~/jobot-ai-elephant/spacemit_audio
bash ollama.sh
```

## Python Dependency Installation

```bash
cd ~/jobot-ai-elephant
python3 -m venv ~/asr_env
source ~/asr_env/bin/activate
pip install -r requirements.txt
```

## Add User to Audio Group

```bash
sudo usermod -aG audio $USER
```

## Using the Code

### Check Recording Devices

```bash
arecord -l
```

Sample output:

Devices with "camera" in the name are camera-related and should not be selected. Card 3 is usable.

```bash
**** List of CAPTURE Hardware Devices ****
card 1: Camera [USB Camera], device 0: USB Audio [USB Audio]
    Subdevices: 1/1
    Subdevice #0: subdevice #0
card 2: Camera_1 [USB 2.0 Camera], device 0: USB Audio [USB Audio]
    Subdevices: 1/1
    Subdevice #0: subdevice #0
card 3: Device [USB PnP Sound Device], device 0: USB Audio [USB Audio]
    Subdevices: 1/1
    Subdevice #0: subdevice #0
```

Modify the recording device index to `3` in the `jobot-ai-pipeline/smart_main_asr.py` file:

```python
...
record_device = 3  # Recording device index, needs to be changed
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=2, max_time=2, channels=1, rate=48000, device_index=record_device)
...
```

### Control Maximum Recording Duration

```python
rec_audio.max_time_record = 3  # Maximum recording time in seconds
```

Recording runs in non-blocking mode by default. For most applications, serial execution is more common—use `join()` to wait for recording to finish:

```python
# Start recording user audio
rec_audio.max_time_record = 3
rec_audio.frame_is_append = True
rec_audio.start_recording()
rec_audio.thread.join()  # Wait for recording to complete
```

### Check Playback Devices

```bash
aplay -l
```

Sample output:

```bash
(asr_env) jobot-ai-pipeline git:(main) aplay -l
card 0: sndes8326 [snd-es8326], device 0: i2s-dai0-ES8326 HiFi ES8326 HiFi-0 []
    Subdevices: 1/1
    Subdevice #0: subdevice #0
card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]
    Subdevices: 1/1
    Subdevice #0: subdevice #0
```

The USB speaker corresponds to `card 2`. Therefore, set:  
`play_device = 'plughw:2,0'`

Update the following files accordingly:

```python
# smart_main_asr.py
play_device='plughw:0,0'  # Playback device
```

```python
# spacemit_audio/play.py
play_device='plughw:0,0'  # Playback device
```

### Run the Code

```bash
cd ~/jobot-ai-elephant
source ~/asr_env/bin/activate  # Run within the virtual environment
python smart_main_asr.py
```

After pressing Enter with no input, it enters recording mode. Default is 3 seconds.

**Fuzzy command matching supported examples:**

"Grab the orange", "Grab the apple", "Checkout", etc.

**Commands supported by the large language model:**

1. "Give me an apple", "And an orange" ...
2. The large model can recognize object names.

### Project Directory Structure

```bash
├── spacemit_audio          # Audio module: recording, playback, ASR
├── spacemit_cv             # Computer vision module
├── spacemit_llm            # Large language model module
├── spacemit_orc            # OCR module
├── tools                   # Utilities
├── feedback_wav            # Feedback audio
├── cv_robot_arm_demo.py
├── asr_elephant_demo.py    # Audio test script
├── functions.py
├── ocr_demo.py             # Standalone OCR test
├── README_EN.md            # English Use Documentation
├── README.md               # Chinese Use Documentation
├── smart_main_asr.py       # Main retail program
├── smart_main.py
├── test_llm.py             # LLM test script
├── test_match.py           # Function match test
└── test_play.py            # Playback test script
```
