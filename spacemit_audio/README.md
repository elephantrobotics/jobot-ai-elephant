# This is a document about how to use asr-llm pipeline

## Installation

When using the asr-llm interface for the first time, you need to set up the Ollama environment first.

```
bash ollama.sh
```

Installl python requirements:

```
sudo apt update
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### spacemit_audio

In the `spacemit_audio` module, two classes are provided: `ASRModel` and `RecAudio`, along with two configurable parameters: `mode` and `sld`.

`RecAudio` have the `mode` parameter sets the sensitivity for detecting surrounding sounds. Three levels are available:
  - Level 1 (default): Recording is triggered when any surrounding sound is detected.
  - Level 2: Balanced sensitivity.
  - Level 3: Recording is triggered only when clear human speech is detected.

- The `sld` parameter defines the duration of silence detection. If the environment remains silent longer than the specified time, recording will automatically stop. The default value is 1 second and can be customized as needed.

You can use them like this:

```
from spacemit_audio import ASRModel, RecAudio, mode, sld
asr_model = ASRModel()
rec_audio = RecAudio(mode, sld)

audio_file = rec_audio.record_audio()
text = asr_model.generate(audio_file)
```

The `record_audio` method is used to record and sample audio.
The `ASRModel` class returns the transcribed text as output.

### spacemit_llm

In the `spacemit_llm` module, two classes are defined: `LLMModel` and `FCModel`.  

A file named `functions.py` exists in the root directory.  
It serves as a function registry, where you can implement any custom functions you need.

- `LLMModel` is used for general large language model streaming conversations.
- `FCModel` is used for function calling (tool use).

You can use them like this:

```
from spacemit_llm import LLMModel, FCModel

llm_model = LLMModel()
fc_model = FCModel()

function_called = fc_model.func_response(text, func_map)
llm_output = llm_model.generate(text)
```

The `FCModel` class defines a method called `func_response`,
which returns a boolean value to determine whether to proceed with a general large language model conversation.

The `LLMModel` class defines a method called `generate`,
which continuously iterates over the streaming output returned by the language model.