# jobot-ai-elephant

myCobot280 RISCV 智慧零售场景系统

## 安装代码

- use git
  
```bash
git clone  https://github.com/elephantrobotics/jobot-ai-elephant.git
```

- [Download version](https://github.com/elephantrobotics/jobot-ai-elephant/releases)

## 环境安装

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

## ⼤模型依赖安装

```bash
cd ~/jobot-ai-elephant/spacemit_audio
bash ollama.sh
```

## python 依赖安装

```bash
cd ~/jobot-ai-elephant
python3 -m venv ~/asr_env
source ~/asr_env/bin/activate
pip install -r requirements.txt
```

## 设置音频组

```bash
sudo usermod -aG audio $USER
```

## 代码使用

### 确认录音设备

```bash
arecord -l
```

输出如下：

带camera的是相机设备不能选，card 3 可以

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

修改 jobot-ai-pipeline/smart_main_asr.py ⽂件⾥⾯录⾳设备为 3 即可.

```bash
...
record_device = 3  # 录音设备,需要更改
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=2, max_time=2, channels=1, rate=48000, device_index=record_device)
...
```

### 控制最大录音时间

```bash
rec_audio.max_time_record = 3 控制最⻓录⾳时间，单位 s
```

录⾳默认以⾮阻塞⽅式运⾏，但对于⼀般应⽤，串⾏执⾏⽐较常⻅，使⽤ join 等待录⾳完成。

```bash
...
# 开始录制用户声音
rec_audio.max_time_record = 3
rec_audio.frame_is_append = True
rec_audio.start_recording()
rec_audio.thread.join() # 等待录音完成
```

### 确认播放设备

```bash
aplay -l
```

输出：

```bash
(asr_env) jobot-ai-pipeline git:(main) aplay -l
card 0: sndes8326 [snd-es8326], device 0: i2s-dai0-ES8326 HiFi ES8326 HiFi-0 []
    ⼦设备: 1/1
    ⼦设备 #0: subdevice #0
card 2: Device [USB Audio Device], device 0: USB Audio [USB Audio]
    ⼦设备: 1/1
    ⼦设备 #0: subdevice #0
```

Device [USB Audio Device], device 0: USB Audio [USB Audio] 为USB扬声器，对应 card2 ，因此设
置：play_device = 'plughw:2,0'

下⾯代码的相关内容需要更改:

```bash
...
# smart_main_asr.py
play_device='plughw:0,0' # 播放设备
...
```

```bash
...
# spacemit_audio/play.py
play_device='plughw:0,0' # 播放设备
...
```

### 启动代码

```bash
cd ~/jobot-ai-elephant
source ~/asr_env/bin/activate # 使用虚拟环境运行
python smart_main_asr.py
```

不输⼊内容按下回⻋进⼊录⾳模式，默认3S

**模糊匹配⽀持的指令：**

抓橘⼦、苹果、买单等

**⼤模型⽀持指令：**

1. 给我⼀个苹果、还要⼀个橘⼦ ....
2. ⼤模型会识别物体名称

### 代码目录说明

```bash
├── spacemit_audio # 语⾳模块，包含录⾳、播放、ASR
├── spacemit_cv # 视觉模块
├── spacemit_llm # ⼤语⾳模型模块
├── spacemit_orc # OCR 模块
├── tools # 常⽤
├── feedback_wav # 反馈语⾳
├── cv_robot_arm_demo.py
├── asr_elephant_demo.py # 可以测试录⾳
├── functions.py
├── ocr_demo.py  # 单独测试OCR
├── README_EN.md  # 英文使用文档
├── README.md  # 中文使用文档
├── smart_main_asr.py # 智慧零售主程序
├── smart_main.py
├── test_llm.py # 单独测试⼤模型
├── test_match.py # 单独测试函数匹配
└── test_play.py # 单独测试播放
```