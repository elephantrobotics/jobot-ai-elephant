import cv2
import time
import os
import threading
import sys
sys.path.append('/home/er/jobot-ai-elephant')
from spacemit_orc.ocr import OCRProcessor
from spacemit_audio import play_wav

class CameraOCR:
    def __init__(self, camera_index=22, timeout=30):
        det_model_path = 'spacemit_orc/models/ppocr3_det_fixed.onnx'
        rec_model_path = 'spacemit_orc/models/ppocr_rec.onnx'
        rec_dict_path = 'spacemit_orc/models/rec_word_dict.txt'
        self.ocr = OCRProcessor(det_model_path, rec_model_path, rec_dict_path)

        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L)
        if not self.cap.isOpened():
            raise Exception(f"无法打开摄像头（index: {camera_index}）")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.timeout = timeout
        self.start_time = time.time()
        self.recognized_texts = []
        self.status_play = {'20': False, '5': False, '2': False}

        self.frame = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    def display_loop(self):
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("无法读取摄像头帧")
                continue

            with self.lock:
                self.frame = frame.copy()

            cv2.imshow("Camera", frame)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                self.stop_event.set()
                break

    def ocr_loop(self):
        while not self.stop_event.is_set():
            time.sleep(0.2)  # Control the recognition frequency
            with self.lock:
                if self.frame is None:
                    continue
                frame_copy = self.frame.copy()
            try:
                # results = self.ocr(temp_path)
                results = self.ocr(cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB))

            except Exception as e:
                print(f"OCR 处理出错: {e}")
                results = []

            if results:
                texts = [item["content"] for item in results]
                for text in texts:
                    if text not in self.recognized_texts:
                        print(f"[识别到] {text}")
                        self.recognized_texts.append(text)
                        if '20' in text and not self.status_play['20']:
                            play_wav('/home/er/jobot-ai-elephant/feedback_wav/shoukuan20yuan.wav')
                            self.status_play['20'] = True
                        elif '5' in text and not self.status_play['5']:
                            play_wav('/home/er/jobot-ai-elephant/feedback_wav/shoukuan5yuan.wav')
                            self.status_play['5'] = True
                        elif '2' in text and not self.status_play['2']:
                            play_wav('/home/er/jobot-ai-elephant/feedback_wav/shoukuan2yuan.wav')
                            self.status_play['2'] = True

            if time.time() - self.start_time > self.timeout:
                print("识别超时")
                self.stop_event.set()
                break

    def recognize_once(self):
        t_display = threading.Thread(target=self.display_loop)
        t_ocr = threading.Thread(target=self.ocr_loop)

        t_display.start()
        t_ocr.start()

        t_display.join()
        t_ocr.join()

        return self.recognized_texts

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

def recognize_text_from_camera(camera_index=22, timeout=30):
    ocr_camera = CameraOCR(camera_index, timeout)
    result = ocr_camera.recognize_once()
    ocr_camera.release()
    return result

if __name__ == "__main__":
    result = recognize_text_from_camera(camera_index=22, timeout=30)
    if result:
        print(f"识别结果: {result}")
    else:
        print("未能在规定时间内识别文本")
