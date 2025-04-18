import os
import time

from spacemit_audio import ASRModel, RecAudio,RecAudioThreadPipeLine

record_device = 3
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=2, max_time=2, channels=1, rate=48000, device_index=record_device)

from tools.elephant import func_map

print("语音模型初始化....")
asr_model = ASRModel()
print("语音模型初始化完成 !!! ")


if __name__ == '__main__':
    try:
        while True:
            print("Press enter to start!")
            input() # enter 触发
            # 开始录制用户声音
            rec_audio.max_time_record = 3
            rec_audio.frame_is_append = True
            rec_audio.start_recording()
            rec_audio.thread.join() # 等待录音完成

            audio_ret = rec_audio.get_audio_file() # 获取录音
            text = asr_model.generate(audio_ret)
            print('user: ', text)

    except KeyboardInterrupt:
        print("process was interrupted by user.")
