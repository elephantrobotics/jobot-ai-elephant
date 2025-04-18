"""
QRCodeScanner.py
This module uses a USB camera to recognize the text information in the QR code and returns

Author: Wang Weijian
Date: 2025-04-18
"""

import cv2
from pyzbar.pyzbar import decode
import time

class QRCodeScanner:
    def __init__(self, camera_index=0, timeout=30):
        self.camera_index = camera_index
        self.time_out = timeout
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L)
        self.start_time = time.time()

        if not self.cap.isOpened():
            raise Exception("无法打开摄像头")

    def scan_qrcode_from_camera(self, raw_frame):
        """Scan the QR code in the camera frame and return the recognition result"""
        decoded_objects = decode(raw_frame)
        if decoded_objects:
            # Recognize the QR code and return text information
            for obj in decoded_objects:
                qr_data = obj.data.decode("utf-8")
                return qr_data
        return None

    def capture_and_recognize(self):
        """Capture camera images and perform QR code recognition, returning the recognized text"""
        while True:
            ret, frame = self.cap.read()
            cv2.imshow("QR", frame)
            cv2.waitKey(30)
            if not ret:
                print("无法读取视频流")
                break
            # Perform QR code recognition
            start_time = time.time()
            qr_data = self.scan_qrcode_from_camera(frame)
            end_time = (time.time() - start_time) * 1000

            print(f"处理时间: {end_time:.3f}ms")

            if qr_data:
                time.sleep(3)
                cv2.destroyAllWindows()
                return qr_data  # Recognize the QR code and return data

            # If the timeout is exceeded, return None
            if time.time() - self.start_time > self.time_out:
                print("识别超时!!!")
                cv2.destroyAllWindows()
                return None

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def release_resources(self):
        """Release camera resources"""
        self.cap.release()
        cv2.destroyAllWindows()

# Main program calling interface
def recognize_qr_from_video(camera_index=22, timeout=15):
    scanner = QRCodeScanner(camera_index=camera_index, timeout=timeout)
    qr_data = scanner.capture_and_recognize()
    scanner.release_resources()
    return qr_data

# Usage Examples
if __name__ == "__main__":
    qr_text = recognize_qr_from_video(camera_index=23, timeout=15)
    if qr_text:
        print(f"识别结果: {qr_text}")
    else:
        print("未能在规定时间内识别二维码")
