# import sounddevice as sd
import wave
import tempfile
import pyaudio
import os
import time
from tools.elephant import func_map, sys_mes


from spacemit_llm import LLMModel
llm_model = LLMModel(sys_mes=sys_mes)

# llm_model = LLMModel(llm_model_path, func_map, sys_mes)

if __name__ == '__main__':
    
    try:
        while True:
            text = input("请输入: ")
            llm_output = llm_model.generate(text)
            full_response = ''
            for output_text in llm_output:
                print(output_text, end='', flush=True)
                full_response += output_text
            if full_response is None:
                continue

            print('\n')

    except KeyboardInterrupt:
        print("process was interrupted by user.")