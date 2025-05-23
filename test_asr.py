import os
import time
from spacemit_audio import ASRModel, RecAudioThreadPipeLine

record_device = 2
# rec_audio = RecAudioThreadPipeLine(sld=0.5, max_time=3, channels=1, rate=48000, device_index=record_device, trig_on=0.16, trig_off=0.1)

rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=1, max_time=2, channels=1, rate=48000, device_index=record_device)



print("语音模型初始化....")
asr_model = ASRModel()
print("语音模型初始化完成 !!! ")


if __name__ == '__main__':
    try:
        while True:
            print("Press enter to start!")
            input()  # enter trigger
            # Start recording user voice
            rec_audio.frame_is_append = True
            rec_audio.start_recording()
            rec_audio.thread.join() # Wait for the recording to finish

            audio_ret = rec_audio.get_audio()  # Get the recording
            text = asr_model.generate(audio_ret)
            print('user: ', text)

    except KeyboardInterrupt:
        print("process was interrupted by user.")
