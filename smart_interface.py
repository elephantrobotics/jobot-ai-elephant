from spacemit_cv import ElephantDetection
import time
import threading
import cv2
import os

class ImageInfer:
    def __init__(self, motion_control):
        self.show_camera = True
        self.cap = None
        self.latest_frame = None
        self.infer_result = None
        self.lock = threading.Lock()
        self.detector = ElephantDetection('spacemit_cv/best.onnx')
        # self.detector = ElephantDetection('spacemit_cv/yolov8n.q.onnx')
        self.motion_control = motion_control
        self.when_checkout = False
        self.selected_class = TimedStr()
        self.stop_event = threading.Event()

    def camera_display_loop(self):
        while self.show_camera and not self.stop_event.is_set():
            if self.motion_control.is_busy() or self.when_checkout:
                if self.cap:
                    self.cap.release()
                    self.cap = None
                    cv2.destroyAllWindows()
                time.sleep(0.1)
                continue

            if self.cap is None:
                self.cap = cv2.VideoCapture(20, cv2.CAP_V4L)
                if not self.cap.isOpened():
                    print("❌ 无法打开摄像头")
                    time.sleep(1)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            with self.lock:
                self.latest_frame = frame.copy()

            display_image = frame.copy()
            with self.lock:
                result = self.infer_result

            if result:
                _, rect_list, classnames = result
                # Change the box color according to the user's selection
                for rect, label_name in zip(rect_list, classnames):
                    (x1, y1), width, height, label_index, score = rect

                    if self.selected_class.get() and label_name == self.selected_class.get():
                        color = (0, 0, 255)  # If the box belongs to the object selected by the user, change it to red
                    else:
                        color = (0, 255, 0)

                    # draw box
                    pt1 = (int(x1), int(y1))
                    pt2 = (int(x1 + width), int(y1 + height))
                    cv2.rectangle(display_image, pt1, pt2, color, 2)
                    orig = (int(x1), int(y1 - 10))
                    cv2.putText(display_image, f'{label_name}: {score:.2f}', orig, cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            cv2.imshow("result", display_image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                self.show_camera = False
                break

        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

    def inference_loop(self):
        while self.show_camera and not self.stop_event.is_set():
            with self.lock:
                if self.latest_frame is None or (self.motion_control.is_busy()):
                    time.sleep(0.1)
                    continue
                frame = self.latest_frame.copy()

            try:
                result_image, rect_list, classnames = self.detector.infer(frame, with_draw=False)
                with self.lock:
                    self.infer_result = (result_image, rect_list, classnames)

            except Exception as e:
                print("There is a mistake in infer loop:", e)
                time.sleep(0.01)


    def get_target_coord(self, object_name):
        if not self.infer_result:
            return None

        result_image, rect_list, classnames = self.infer_result
        print(f"检测到 {len(rect_list)} 个目标，类别为：{classnames}")

        # Traverse to find the matching categories
        for idx, rect in enumerate(rect_list):
            label = classnames[idx]
            if label == object_name:
                (x1, y1), width, height, *_ = rect
                center_x = x1 + width // 2
                center_y = y1 + height // 2
                print(f"找到目标 {object_name}，中心点: ({center_x}, {center_y})")

                # self.selected_class = object_name
                self.selected_class.set_value(object_name)
                return [center_x, center_y]

        return None

    def stop(self):
        self.stop_event.set()



class TimedStr:
    def __init__(self, timeout=4):
        self._value = None
        self._timeout = timeout
        self._timer = None

    def _reset_to_none(self):
        self._value = None
        self._timer = None

    def set_value(self, value):
        self._value = value
        # If there is already a timer, cancel it first
        if self._timer:
            self._timer.cancel()
        # Set a new timer
        self._timer = threading.Timer(self._timeout, self._reset_to_none)
        self._timer.start()

    def get(self):
        return self._value