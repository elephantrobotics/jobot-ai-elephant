"""
OCRVideoCapture.py
This module uses a USB camera to recognize text information and return

Author: Wang Weijian
Date: 2025-04-18
"""

import cv2
import time
import os
from spacemit_orc.ocr import OCRProcessor
import sys
sys.path.append('/home/er/jobot-ai-elephant')
from spacemit_audio import play_wav_non_blocking, play_wav

class CameraOCR:
    def __init__(self, camera_index=22, timeout=30):

        det_model_path = 'spacemit_orc/models/ppocr3_det_fixed.onnx'
        rec_model_path = 'spacemit_orc/models/ppocr_rec.onnx'
        rec_dict_path = 'spacemit_orc/models/rec_word_dict.txt'
        self.ocr = OCRProcessor(det_model_path, rec_model_path, rec_dict_path)
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L)
        self.timeout = timeout
        self.start_time = time.time()
        self.recognized_texts = []  # Used to save the recognized text
        self.printed_texts = set()

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            raise Exception(f"无法打开摄像头（索引: {camera_index}）")

        self.status_play = {'20':False, '5':False, '2':False}

    def recognize_once(self):
        while 1:
            ret, frame = self.cap.read()

            if not ret:
                print("无法获取摄像头画面")
                break

            # Save temporary frames and identify them
            temp_path = "temp_frame.jpg"
            cv2.imwrite(temp_path, frame)
            try:
                start_time = time.time()
                results = self.ocr(temp_path)
                end_time = (time.time() - start_time) * 1000
                # print(f"处理时间: {end_time:.3f}ms")
            except Exception as e:
                print(f"OCR processing error: {e}")
                results = []
            valid_texts = ["超市抵用券1元", "超市抵用券2元", "超市抵用券5元", "超市抵用券10元", "超市抵用券20元"]
            # 如果识别结果存在，提取并保存
            if results:
                texts = [item["content"] for item in results]
                for text in texts:
                    if text not in self.recognized_texts:  # 避免重复添加
                        if text in valid_texts and text not in self.recognized_texts:  # 只保存符合格式的 # 避免重复添加
                            self.recognized_texts.append(text)

                        if '20' in text and self.status_play['20'] == False:
                            # play_wav_non_blocking('../feedback_wav/shoukuan20yuan.wav') ### 20元
                            play_wav('/home/er/jobot-ai-elephant/feedback_wav/shoukuan20yuan.wav') ### 20元
                            self.status_play['20'] = True
                        elif '5' in text and self.status_play['5'] == False:
                            play_wav('/home/er/jobot-ai-elephant/feedback_wav/shoukuan5yuan.wav') ### 5
                            # play_wav_non_blocking('../feedback_wav/shoukuan5yuan.wav') ### 5
                            self.status_play['5'] = True
                        elif '2' in text and self.status_play['2'] == False:
                            # play_wav_non_blocking('../feedback_wav/shoukuan2yuan.wav') ### 2
                            play_wav('/home/er/jobot-ai-elephant/feedback_wav/shoukuan2yuan.wav') ### 2
                            self.status_play['2'] = True

            # Display the real-time camera image in the window
            cv2.imshow("Camera", frame)

            cv2.waitKey(30)

            for text in self.recognized_texts:
                if text not in self.printed_texts:
                    print(text)
                    self.printed_texts.add(text)

            if time.time() - self.start_time > self.timeout:
                print("识别完成!!!")
                return self.recognized_texts

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()

def recognize_text_from_camera(camera_index=22, timeout=30):
    ocr_camera = CameraOCR(camera_index, timeout)
    result = ocr_camera.recognize_once()
    ocr_camera.release()
    return result


# 使用示例
if __name__ == "__main__":
    result = recognize_text_from_camera(camera_index=22, timeout=30)

    if result:
        print(f"Recognition results: {result}")
    else:
        print("Failed to recognize text within the allotted time")