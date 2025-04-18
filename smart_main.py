import time
import threading
import cv2

from spacemit_cv import ElephantDetection
from tools.elephant.elephant_function_motion_control import ElephantMotionControl
from tools.elephant.elephant_function_map import *
from spacemit_orc.OCRVideoCapture import recognize_text_from_camera

detector = ElephantDetection('spacemit_cv/best.onnx')
motion_control = ElephantMotionControl()

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
        if cv2.waitKey(1) & 0xFF == ord('q'):
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
    global cap, latest_frame, selected_class
    while True:
        try:
            user_input = input("\n1. 请输入待抓取物体类别（可选类别：jeep, apple, banana, bed, grape......）\n2. 开始结算（请输入'start checkout' 开始结算，请在30秒内使用超市抵用券进行结算）\n3. 输入 q 退出：")
            if user_input.lower() == 'q':
                break
            if not user_input:
                continue
            if user_input.lower() == 'start checkout':  # 如果输入 'start checkout' 则执行文字识别，开始结算
                if cap:  # 如果摄像头20已打开，先关闭
                    cap.release()
                    cv2.destroyAllWindows()
                ocr_text = recognize_text_from_camera(camera_index=22, timeout=30)
                if ocr_text:
                    print('结算结果：', ocr_text)
                else:
                    print("文字识别失败或超时")
                # 识别完成后，重新打开摄像头20
                cap = cv2.VideoCapture(20, cv2.CAP_V4L)
                if not cap.isOpened():
                    print("❌ 无法重新打开摄像头20")
                continue  # 继续下一次输入循环

            # 检查输入的类别是否在有效类别中
            if user_input.lower() not in valid_classes:
                print(f"无效类别：'{user_input}'，请重新输入有效的类别。")
                continue
            cls = user_input.strip()
            res = grab_an_object_and_place_it_in_a_position(cls, latest_frame, motion_control, detector)
            print(res)
        except Exception as e:
            print("发生错误：", e)


if __name__ == '__main__':
    display_thread = threading.Thread(target=camera_display_loop)
    display_thread.start()

    user_input_loop()  # 主线程等待用户输入

    display_thread.join()
