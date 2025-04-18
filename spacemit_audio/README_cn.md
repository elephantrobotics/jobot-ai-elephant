# ASR-LLM 流水线使用文档

## 安装说明

首次使用 ASR-LLM 接口时，需要先配置 Ollama 环境：

```
bash ollama.sh
```

安装 python 依赖：

```
sudo apt update
sudo apt install python3-venv
python3 -m venv ~/asr_env
source ~/asr_env/bin/activate
pip install --extra-index-url https://git.spacemit.com/api/v4/projects/33/packages/pypi/simple --extra-index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple -r requirements.txt
```

## 使用方法

### spacemit_asr 模块

在 `spacemit_asr` 模块中，提供了两个类：`ASRModel` 和 `RecAudio`。

`RecAudio` 存在 `mode` 变量用于设置对周围声音的检测灵敏度，提供三档可选：
  - 第 1 档（默认）：检测到周围有声音即可触发录音；
  - 第 2 档：灵敏度平衡；
  - 第 3 档：只有检测到明确的人声才会触发录音。

- `sld` 变量用于设置静音判断时间，即当检测到环境静音超过设定时长后，自动停止录音。默认值为 1 秒，可根据需要自定义。

使用示例如下：

```
from spacemit_asr import ASRModel, RecAudio, mode, sld
asr_model = ASRModel()
rec_audio = RecAudio(mode, sld)

audio_file = rec_audio.record_audio()
text = asr_model.generate(audio_file)
```

- `record_audio` 方法用于录制并采样音频。
- `ASRModel` 类用于语音识别，返回转写后的文本。

### spacemit_llm 模块

在 `spacemit_llm` 模块中，定义了两个类：`LLMModel` 和 `FCModel`。

项目根目录下有一个名为 `functions.py` 的文件，
该文件是函数注册中心，你可以在其中实现任何自定义的函数逻辑。

- `LLMModel` 用于普通的大语言模型流式对话。
- `FCModel` 用于函数调用（工具使用）。

使用示例如下：

```
from spacemit_llm import LLMModel, FCModel

llm_model = LLMModel()
fc_model = FCModel()

function_called = fc_model.func_response(text, func_map)
llm_output = llm_model.generate(text)
```

`FCModel` 类定义了一个方法 `func_response`，用于判断是否触发函数调用，返回布尔值。
`LLMModel` 类定义了一个方法 `generate`，用于持续生成语言模型的流式输出。