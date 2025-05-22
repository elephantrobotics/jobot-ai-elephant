import time
import threading
import cv2
import os

from tools.elephant.elephant_function_motion_control import ElephantMotionControl
from tools.elephant.elephant_function_map import valid_classes, sys_mes, grab_async, execute_command, object_name_dict_zh
from spacemit_orc.OCRVideoCapture import recognize_text_from_camera
from smart_interface import ImageInfer

# init
motion_control = ElephantMotionControl()

# ASR + LLM part: speech recognition and large model related parts
from spacemit_llm import LLMModel, FCModel
llm_model = LLMModel(sys_mes=sys_mes)

# Import voice modules, including recording, playback, VAD, etc.
from spacemit_audio import ASRModel, RecAudioThreadPipeLine, play_wav_non_blocking, play_wav, find_audio_card, find_playback_card
import spacemit_audio.play

play_device = f'plughw:{find_playback_card()},0' # Playback device
spacemit_audio.play.set_play_device(play_device)

record_device = find_audio_card(target_name='[USB PnP Sound Device]') # Recording equipment needs to be changed
print(f"录音设备号：{record_device}")
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=1, max_time=2, channels=1, rate=48000, device_index=record_device)

print("语音模型初始化....")
asr_model = ASRModel()
print("语音模型初始化完成 !!! ")

# Large model initialization
print("大模型初始化....")

llm_output = llm_model.generate('拿个苹果')
full_response = ''
for output_text in llm_output:
    full_response += output_text
if full_response is None:
    pass
print("大模型初始化完成 !!! ")

def user_input_loop(image_infer : ImageInfer):
    """
    用户输入选择
    """
    play_wav('/home/er/jobot-ai-elephant/feedback_wav/huanyingshiyong.wav') ###  Welcome to the Smart Retail System
    while True:
        try:
            user_input = input("\n1. 按下回车, 然后语音输入待抓取物体类别（可选类别：jeep, apple, banana, bed, grape......）\n2. 按下回车，语音输入结账或买单开始结算，请在30秒内使用超市抵用券进行结算）\n3. 输入 q 退出：")
            print("开始录音............................")
            if user_input.lower() == 'q':
                break
            if not user_input:
                # Start recording
                rec_audio.frame_is_append = True
                rec_audio.start_recording()
                rec_audio.thread.join() # Wait for the recording to finish

                audio_ret = rec_audio.get_audio() # Get recording data

                text = asr_model.generate(audio_ret) # Speech to Text
                print('user: ', text)

                if text == '':
                    print("没听清楚，请再说一次")
                    play_wav('./feedback_wav/meitingqingchu.wav') ### Didn't hear clearly
                    continue

                ### Fuzzy matching, usually without parameters, can be used for demonstration
                ret, object_name = execute_command(text, object_name_dict_zh)
                if ret:
                    print(f"识别到语义为: {object_name}")
                    user_input = object_name
                else:
                    print("大模型开始理解")

                    llm_output = llm_model.generate(text)
                    full_response = ''
                    for output_text in llm_output:
                        print(output_text, end='', flush=True)
                        full_response += output_text
                    if full_response is None:
                        play_wav('./feedback_wav/wuxiaoneirong.wav') ### Invalid content
                        continue

                    print('\n')

                    ret, object_name = execute_command(full_response, object_name_dict_zh)
                    if ret:
                        print(f"识别到语义为: {object_name}")
                        user_input = object_name
                    else:
                        print("未匹配到对应语义")
                        play_wav('./feedback_wav/wuxiaoneirong.wav')
                        continue

            if user_input.lower() == 'intro':
                play_wav('./feedback_wav/dayuyanmoxing.wav') # Big model self introduction
                continue

            if user_input.lower() == 'start checkout':  # If you enter 'start checkout', text recognition will be performed and checkout will begin
                play_wav('./feedback_wav/qingshaohou.wav') ### Checkout in progress, please wait
                play_wav('./feedback_wav/nixuangoule.wav') ### Settlement details report

                image_infer.when_checkout = True # If camera 20 is turned on, turn it off first

                ocr_text = recognize_text_from_camera(camera_index=22, timeout=60)
                if ocr_text:
                    print('结算结果：', ocr_text)
                    play_wav('./feedback_wav/xiaciguanglin.wav') ### Payment of 27 yuan has been completed. Welcome to visit next time.
                else:
                    print("文字识别失败或超时")
                    play_wav('./feedback_wav/shibieshibai.wav') ### Text recognition failed or timed out

                image_infer.when_checkout = False # After the recognition is completed, turn on the camera again 20
                continue

            # Checks if the input category is among the valid categories
            if user_input.lower() not in valid_classes:
                print(f"无效类别：'{user_input}'，请重新输入有效的类别。")
                play_wav('./feedback_wav/wuxiaoleibei.wav')
                continue

            cls_name = user_input.strip()
            center_point = image_infer.get_target_coord(cls_name)

            if center_point:
                res = grab_async(center_point, cls_name, motion_control)
                print("&&&&", res)

                if cls_name == "apple":
                    play_wav_non_blocking('./feedback_wav/pingguo.wav')
                elif cls_name == "orange":
                    play_wav_non_blocking('./feedback_wav/chengzi.wav')
                elif cls_name == "banana":
                    play_wav_non_blocking('./feedback_wav/xiangjiao.wav')
                else:
                    play_wav_non_blocking('./feedback_wav/zhengzaizhuaqu.wav')

            else:
                play_wav('./feedback_wav/wuxiaoleibei.wav')
                print(f"❌ 未找到类别为 '{cls_name}' 的目标，请重新输入")

        except Exception as e:
            print("Error occurred:", e)


if __name__ == '__main__':
    image_infer = ImageInfer(motion_control)

    display_thread = threading.Thread(target=image_infer.camera_display_loop)
    inference_thread = threading.Thread(target=image_infer.inference_loop)

    display_thread.start()
    inference_thread.start()

    try:
        user_input_loop(image_infer)  # The main thread is waiting for user input
    except KeyboardInterrupt:
        print("用户中断，退出程序...")

    image_infer.stop()
    display_thread.join()
    inference_thread.join()
