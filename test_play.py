# import subprocess

# subprocess.run(["espeak-ng", "-a", "300",  "-v", "zh", "正在抓取苹果"])


from spacemit_audio import play_wav_non_blocking, play_wav
import time
device='plughw:0,0'
# device='plughw:0,0'

play_wav('/home/er/jobot-ai-elephant/feedback_wav/huanyingshiyong.wav', device=device)

# play_wav('./feedback_wav/zhengzaizhuaqu.wav', device='plughw:4,0')


time.sleep(5)


# play_wav_non_blocking('./feedback_wav/zhengzaijiesuan.wav', device='plughw:4,0')


