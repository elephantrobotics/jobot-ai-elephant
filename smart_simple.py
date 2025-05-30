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
                # play_wav('./feedback_wav/wuxiaoleibei.wav', device=play_device)
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
