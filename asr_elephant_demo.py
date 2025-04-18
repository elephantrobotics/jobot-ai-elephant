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
            input() # enter trigger
            # Start recording user voice
            rec_audio.max_time_record = 3
            rec_audio.frame_is_append = True
            rec_audio.start_recording()
            rec_audio.thread.join() # Wait for the recording to finish

            audio_ret = rec_audio.get_audio_file() # Get the recording
            text = asr_model.generate(audio_ret)
            print('user: ', text)

    except KeyboardInterrupt:
        print("process was interrupted by user.")
