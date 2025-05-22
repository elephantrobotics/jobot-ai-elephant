import time
import threading
import cv2
import os

from tools.elephant.elephant_function_motion_control import ElephantMotionControl
from tools.elephant.elephant_function_map import valid_classes, sys_mes, grab_simple_async, execute_command, object_name_dict_zh
from spacemit_orc.OCRVideoCapture import recognize_text_from_camera
from smart_interface import ImageInfer

# init
motion_control = ElephantMotionControl()

# The ASR + LLM section
from spacemit_llm import LLMModel, FCModel
llm_model = LLMModel(sys_mes=sys_mes)

# Audio recording and playback
from spacemit_audio import ASRModel, RecAudioThreadPipeLine, play_wav_non_blocking, play_wav, find_audio_card, find_playback_card

play_device = f'plughw:{find_playback_card()},0'
record_device = find_audio_card(target_name='Device [USB PnP Sound Device]')
print(f"录音设备号：{record_device}")
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=1, max_time=2, channels=1, rate=48000, device_index=record_device)

print("语音模型初始化....")
asr_model = ASRModel()
print("语音模型初始化完成 !!! ")

# Initialization of LLM
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
                        print("没听清楚，请再说一次")
                        continue

                    print('\n')

                    ret, object_name = execute_command(full_response, object_name_dict_zh)
                    if ret:
                        print(f"识别到语义为: {object_name}")
                        user_input = object_name
                    else:
                        print("未匹配到对应语义")
                        continue

            if user_input.lower() == 'intro':
                print("自我介绍完毕！！！")
                continue

            # Checks if the input category is among the valid categories
            if user_input.lower() not in valid_classes:
                print(f"无效类别：'{user_input}'，请重新输入有效的类别。")
                continue

            cls_name = user_input.strip()
            center_point = image_infer.get_target_coord(cls_name)
            if center_point:
                res = grab_simple_async(center_point, cls_name, motion_control)
                print("&&&&", res)

            else:
                print(f"❌ 未找到类别为 '{cls_name}' 的目标，请重新输入")
        except Exception as e:
            print("发生错误：", e)


if __name__ == '__main__':
    image_infer = ImageInfer(motion_control)

    display_thread = threading.Thread(target=image_infer.camera_display_loop)
    inference_thread = threading.Thread(target=image_infer.inference_loop)

    display_thread.start()
    inference_thread.start()

    try:
        user_input_loop(image_infer)  # 主线程等待用户输入
    except KeyboardInterrupt:
        print("用户中断，退出程序...")

    image_infer.stop()
    display_thread.join()
    inference_thread.join()
