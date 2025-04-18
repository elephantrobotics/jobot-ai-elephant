import time
import threading
import cv2
import os
import difflib

from spacemit_cv import ElephantDetection # 导入大象识别模块
from tools.elephant.elephant_function_motion_control import ElephantMotionControl # 导入机械臂运动控制模块
from tools.elephant.elephant_function_map import *       # 导入函数调用相关内容
from tools.elephant import func_map, object_name_dict_zh # 导入函数调用相关内容
from spacemit_orc.OCRVideoCapture import recognize_text_from_camera # 导入文字识别模块（摄像头文字识别）

# 初始化目标检测器和运动控制对象
detector = ElephantDetection('spacemit_cv/best.onnx')
motion_control = ElephantMotionControl()

# ASR + LLM 部分：语音识别和大模型相关部分
from spacemit_llm import LLMModel, FCModel
llm_model = LLMModel(sys_mes=sys_mes)
fc_model = FCModel(fc_model_name = 'qwen2.5-0.5b-elephant-fc')

# 导入语音模块，包括录音、播放、VAD等
from spacemit_audio import ASRModel, RecAudio, RecAudioThreadPipeLine, play_wav_non_blocking, play_wav

play_device='plughw:0,0' # 播放设备
record_device = 3        # 录音设备,需要更改
rec_audio = RecAudioThreadPipeLine(vad_mode=1, sld=2, max_time=2, channels=1, rate=48000, device_index=record_device)

# 初始化
print("语音模型初始化....")
asr_model = ASRModel()
print("语音模型初始化完成 !!! ")

# 大模型初始化
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
selected_class = None  # 记录用户选择的物体名称
target_cls_name = None  # 初始没有目标类别
cap = None

# 定义有效的物体类别
valid_classes = [
    "jeep", "apple", "banana", "bed", "grape", "laptop", "microwave",
    "orange", "pear", "refrigerator1", "refrigerator2", "sofe", "sofe2",
    "tv", "washing machine1"
]

# 识别是否有函数调用
def execute_command(user_input):
    valid_commands = list(object_name_dict_zh.keys())

    # 使用 difflib 进行模糊匹配
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
    机械臂末端摄像头法兰视频流-线程显示
    """
    global cap, show_camera, latest_frame, selected_class

    while show_camera:
        # 如果在抓取阶段，关闭摄像头20
        if motion_control.is_busy():
            if cap:
                cap.release()
                cap = None
                cv2.destroyAllWindows()
            time.sleep(0.1)
            continue

        # 如果没有打开，就打开一次
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

        # 根据用户选择改变框颜色
        for idx, rect in enumerate(rect_list):
            label = classnames[idx]
            (x1, y1), width, height, *_ = rect

            # 如果该框属于用户选择的物体，改为红色
            if selected_class and label == selected_class:
                color = (0, 0, 255)  # 红色框

                # 绘制框
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
    用户输入选择
    """
    play_wav('/home/er/jobot-ai-elephant/feedback_wav/huanyingshiyong.wav', device=play_device) ### 欢迎使用智慧零售系统
    global cap, latest_frame, selected_class
    while True:
        try:
            user_input = input("\n1. 按下回车, 然后语音输入待抓取物体类别（可选类别：jeep, apple, banana, bed, grape......）\n2. 按下回车，语音输入结账或买单开始结算，请在30秒内使用超市抵用券进行结算）\n3. 输入 q 退出：")
            rec_audio.max_time_record = 3       # 最大录音时间
            rec_audio.frame_is_append = False   # 是否开启录音
            rec_audio.time_start = time.time()  # 获取当前时间戳
            rec_audio.start_recording() # 开启麦克风
            time.sleep(0.2)
            # play_wav_non_blocking('./feedback_wav/qingzhiding.wav', device=play_device) ### 请指定抓取物品
            # time.sleep(2)
            print("开始录音............................")
            rec_audio.frame_is_append = True    # 开启录音
            rec_audio.time_start = time.time()  # 获取当前时间戳
            if user_input.lower() == 'q':
                break
            if not user_input:
                rec_audio.max_time_record = 3   # 重新设置最大录音时间
                rec_audio.thread.join()         # 等待录音完成

                audio_ret = rec_audio.get_audio_file() # 获取录音数据
                text = asr_model.generate(audio_ret)   # 语音转文字
                print('user: ', text)

                if text == '':
                    print("没听清楚，请再说一次")
                    play_wav('./feedback_wav/meitingqingchu.wav', device=play_device) ### 没听清楚
                    continue

                ### 大模型匹配，可带参数、可定制
                # t1 = time.time()
                # function_called, func_name, args = fc_model.get_function_name(text, func_map)
                # print('used time:', time.time() - t1)
                # if function_called:
                #     print(f"调用的函数名: {func_name}, 函数参数：{args}")
                #     user_input = args['object_name']
                # else:
                #     print("未匹配到函数")

                ### 模糊匹配，一般不带参数，可以用于演示
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
                        play_wav('./feedback_wav/wuxiaoneirong.wav', device=play_device) ### 无效内容
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
                play_wav('./feedback_wav/dayuyanmoxing.wav', device=play_device) # 大模型自我介绍
                continue

            if user_input.lower() == 'start checkout':  # 如果输入 'start checkout' 则执行文字识别，开始结算
                play_wav('./feedback_wav/qingshaohou.wav', device=play_device) ### 正在结算，请稍后
                play_wav('./feedback_wav/nixuangoule.wav', device=play_device) ### 结算明细播报
                if cap:  # 如果摄像头20已打开，先关闭
                    cap.release()
                    cv2.destroyAllWindows()
                ocr_text = recognize_text_from_camera(camera_index=22, timeout=60)
                if ocr_text:
                    print('结算结果：', ocr_text)
                    play_wav('./feedback_wav/xiaciguanglin.wav', device=play_device) ### 已完成收款27元，欢迎下次光临
                else:
                    print("文字识别失败或超时")
                    play_wav('./feedback_wav/shibieshibai.wav', device=play_device) ### 文字识别失败或超时
                # 识别完成后，重新打开摄像头20
                cap = cv2.VideoCapture(20, cv2.CAP_V4L)
                if not cap.isOpened():
                    print("❌ 无法重新打开摄像头20")
                continue

            # 检查输入的类别是否在有效类别中
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

    user_input_loop()  # 主线程等待用户输入

    display_thread.join()
