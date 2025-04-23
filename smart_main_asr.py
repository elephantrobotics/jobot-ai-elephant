import time
import threading
import cv2
import os
import difflib

from spacemit_cv import ElephantDetection # Import the elephant recognition module
from tools.elephant.elephant_function_motion_control import ElephantMotionControl # Import the robot arm motion control module
from tools.elephant.elephant_function_map import *       # Import function call related content
from tools.elephant import func_map, object_name_dict_zh # Import function call related content
from spacemit_orc.OCRVideoCapture import recognize_text_from_camera # Import text recognition module (camera text recognition)

# Initialize the object detector and motion control objects
detector = ElephantDetection('spacemit_cv/best.onnx')
motion_control = ElephantMotionControl()

# ASR + LLM part: speech recognition and large model related parts
from spacemit_llm import LLMModel, FCModel
llm_model = LLMModel(sys_mes=sys_mes)
fc_model = FCModel(fc_model_name = 'qwen2.5-0.5b-elephant-fc')

# Import voice modules, including recording, playback, VAD, etc.
from spacemit_audio import ASRModel, RecAudio, RecAudioThreadPipeLine, play_wav_non_blocking, play_wav

play_device='plughw:0,0' # Playback device
record_device = 3        # Recording equipment needs to be changed
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=2, max_time=2, channels=1, rate=48000, device_index=record_device)

# initialization
print("语音模型初始化....")
asr_model = ASRModel()
print("语音模型初始化完成 !!! ")

# Large model initialization
print("大模型初始化....")
# function_called, func_name, args = fc_model.get_function_name('', func_map)

llm_output = llm_model.generate('拿个苹果')
full_response = ''
for output_text in llm_output:
    full_response += output_text
if full_response is None:
    pass
print("大模型初始化完成 !!! ")

classnames = None
show_camera = True
latest_frame = None
lock = threading.Lock()
selected_class = None  # Record the name of the object selected by the user
target_cls_name = None  # Initially there is no target category
cap = None

# Defining valid object classes
valid_classes = [
    "jeep", "apple", "banana", "bed", "grape", "laptop", "microwave",
    "orange", "pear", "refrigerator1", "refrigerator2", "sofe", "sofe2",
    "tv", "washing machine1"
]

# Identify if there is a function call
def execute_command(user_input):
    valid_commands = list(object_name_dict_zh.keys())

    # Fuzzy matching with difflib
    match = difflib.get_close_matches(user_input, valid_commands, n=1, cutoff=0.6)

    if match:
        try:
            _name = object_name_dict_zh[match[0]]
            return True, _name
        except:
            return False, None
    else:
        return False, None

def camera_display_loop():
    """
    Video stream of camera flange at the end of the robotic arm - thread display
    """
    global cap, show_camera, latest_frame, selected_class

    while show_camera:
        # If in the capture phase, close the camera 20
        if motion_control.is_busy():
            if cap:
                cap.release()
                cap = None
                cv2.destroyAllWindows()
            time.sleep(0.1)
            continue

        # If it is not open, open it once
        if cap is None:
            cap = cv2.VideoCapture(20, cv2.CAP_V4L)
            if not cap.isOpened():
                print("❌ 无法打开摄像头20")
                time.sleep(1)
                continue

        ret, frame = cap.read()
        if not ret:
            continue

        result_image, rect_list, classnames = detector.infer(frame)
        # print(classnames)

        # Change box color based on user selection
        for idx, rect in enumerate(rect_list):
            label = classnames[idx]
            (x1, y1), width, height, *_ = rect

            # If the box belongs to the object selected by the user, it turns red
            if selected_class and label == selected_class:
                color = (0, 0, 255) 

                # Draw the box
                pt1 = (int(x1), int(y1))
                pt2 = (int(x1 + width), int(y1 + height))
                cv2.rectangle(result_image, pt1, pt2, color, 2)
                cv2.putText(result_image, label, (int(x1), int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        with lock:
            latest_frame = frame.copy()

        cv2.imshow("result", result_image)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            show_camera = False
            break

        time.sleep(0.01)

    if cap:
        cap.release()
    cv2.destroyAllWindows()

def user_input_loop():
    """
    User input selection
    """
    play_wav('/home/er/jobot-ai-elephant/feedback_wav/huanyingshiyong.wav', device=play_device) ### Welcome to the Smart Retail System
    global cap, latest_frame, selected_class
    while True:
        try:
            user_input = input("\n1. 按下回车, 然后语音输入待抓取物体类别（可选类别：jeep, apple, banana, bed, grape......）\n2. 按下回车，语音输入结账或买单开始结算，请在30秒内使用超市抵用券进行结算）\n3. 输入 q 退出：")
            rec_audio.max_time_record = 3 # Maximum recording time
            rec_audio.frame_is_append = False # Whether to start recording
            rec_audio.time_start = time.time() # Get the current timestamp
            rec_audio.start_recording() # Turn on the microphone
            time.sleep(0.2)
            # play_wav_non_blocking('./feedback_wav/qingzhiding.wav', device=play_device) ### Please specify the item to grab
            # time.sleep(2)
            print("开始录音............................")
            rec_audio.frame_is_append = True    # Start recording
            rec_audio.time_start = time.time()  # Get the current timestamp
            if user_input.lower() == 'q':
                break
            if not user_input:
                rec_audio.max_time_record = 3   # Reset the maximum recording time
                rec_audio.thread.join()         # Wait for the recording to finish

                audio_ret = rec_audio.get_audio_file() # Get recording data
                text = asr_model.generate(audio_ret)   # Speech to Text
                print('user: ', text)

                if text == '':
                    print("没听清楚，请再说一次")
                    play_wav('./feedback_wav/meitingqingchu.wav', device=play_device) ### Didn't hear clearly
                    continue

                ### Large model matching, with parameters and customizable
                # t1 = time.time()
                # function_called, func_name, args = fc_model.get_function_name(text, func_map)
                # print('used time:', time.time() - t1)
                # if function_called:
                #     print(f"调用的函数名: {func_name}, 函数参数：{args}")
                #     user_input = args['object_name']
                # else:
                #     print("未匹配到函数")

                ### Fuzzy matching, usually without parameters, can be used for demonstration
                ret, object_name = execute_command(text)
                if ret:
                    print(f"识别到语义为: {object_name}")
                    user_input = object_name
                else:
                    print("大模型开始理解")

                    # 使用大模型进一步解析复杂文本
                    llm_output = llm_model.generate(text)
                    full_response = ''
                    for output_text in llm_output:
                        print(output_text, end='', flush=True)
                        full_response += output_text
                    if full_response is None:
                        play_wav('./feedback_wav/wuxiaoneirong.wav', device=play_device) ### Invalid content
                        continue

                    print('\n')

                    ret, object_name = execute_command(full_response)
                    if ret:
                        print(f"识别到语义为: {object_name}")
                        user_input = object_name
                    else:
                        print("未匹配到对应语义")
                        play_wav('./feedback_wav/wuxiaoneirong.wav', device=play_device)
                        continue

            if user_input.lower() == 'intro':
                play_wav('./feedback_wav/dayuyanmoxing.wav', device=play_device) # Big model self introduction
                continue

            if user_input.lower() == 'start checkout':  # If you enter 'start checkout', text recognition will be performed and checkout will begin
                play_wav('./feedback_wav/qingshaohou.wav', device=play_device) # Checkout in progress, please wait
                play_wav('./feedback_wav/nixuangoule.wav', device=play_device) # Settlement details report
                if cap:  # If camera 20 is already on, close it first
                    cap.release()
                    cv2.destroyAllWindows()
                ocr_text = recognize_text_from_camera(camera_index=22, timeout=60)
                if ocr_text:
                    print('结算结果：', ocr_text)
                    play_wav('./feedback_wav/xiaciguanglin.wav', device=play_device) # Payment of 27 yuan has been completed. Welcome to visit next time.
                else:
                    # print("文字识别失败或超时")
                    play_wav('./feedback_wav/shibieshibai.wav', device=play_device) # Text recognition failed or timed out
                # After the recognition is completed, reopen the camera 20
                cap = cv2.VideoCapture(20, cv2.CAP_V4L)
                if not cap.isOpened():
                    print("❌ 无法重新打开摄像头20")
                continue

            # Checks if the input category is among the valid categories
            if user_input.lower() not in valid_classes:
                print(f"无效类别：'{user_input}'，请重新输入有效的类别。")
                play_wav('./feedback_wav/wuxiaoleibei.wav', device=play_device)
                continue

            cls = user_input.strip()
            res = grab_an_object_and_place_it_in_a_position(cls, latest_frame, motion_control, detector)
            print("results:", res)
            if '未找到类别' in res:
                play_wav('./feedback_wav/wuxiaoleibei.wav', device=play_device)
            else:
                if cls == "apple":
                    play_wav_non_blocking('./feedback_wav/pingguo.wav', device=play_device)
                elif cls == "orange":
                    play_wav_non_blocking('./feedback_wav/chengzi.wav', device=play_device)
                elif cls == "banana":
                    play_wav_non_blocking('./feedback_wav/xiangjiao.wav', device=play_device)
                else:
                    play_wav_non_blocking('./feedback_wav/zhengzaizhuaqu.wav', device=play_device)
        except Exception as e:
            print("发生错误：", e)


if __name__ == '__main__':
    display_thread = threading.Thread(target=camera_display_loop)
    display_thread.start()

    user_input_loop()  # The main thread waits for user input

    display_thread.join()
