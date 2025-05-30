import cv2
from pyzbar.pyzbar import decode
import time
import threading

class QRCodeScanner:
    def __init__(self, camera_index=0, timeout=30):
        self.camera_index = camera_index
        self.timeout = timeout
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L)
        if not self.cap.isOpened():
            raise Exception("无法打开摄像头")

        self.frame = None
        self.qr_data = None
        self.lock = threading.Lock()
        self.running = True
        self.count = 0
        self.start_time = time.time()

    def scan_qrcode_from_camera(self, raw_frame):
        decoded_objects = decode(raw_frame)
        # Recognize the QR code and return text information
        for obj in decoded_objects:
            return obj.data.decode("utf-8")
        return None

    def display_loop(self):
        while self.running or self.count <= 25:
            ret, frame = self.cap.read()
            if not ret:
                print("无法读取视频流")
                self.running = False
                break

            with self.lock:
                self.frame = frame.copy()

            cv2.imshow("QR", frame)

            if cv2.waitKey(20) & 0xFF == ord('q'):
                self.running = False
                break

            self.count+=1

        cv2.destroyAllWindows()

    def recognition_loop(self):
        while self.running and (time.time() - self.start_time < self.timeout):
            if self.frame is not None:
                with self.lock:
                    frame_copy = self.frame.copy()

                start_time = time.time()
                qr_data = self.scan_qrcode_from_camera(frame_copy)
                end_time = (time.time() - start_time) * 1000
                print(f"处理时间: {end_time:.3f}ms")

                if qr_data:
                    self.qr_data = qr_data
                    print("识别成功，准备退出")
                    self.running = False
                    break

            time.sleep(0.01)

        # If the timeout is exceeded, return None
        if time.time() - self.start_time >= self.timeout:
            print("识别超时")
            self.running = False

    def capture_and_recognize(self):
        display_thread = threading.Thread(target=self.display_loop)
        recognition_thread = threading.Thread(target=self.recognition_loop)

        display_thread.start()
        recognition_thread.start()

        recognition_thread.join()
        self.running = False
        display_thread.join()

        return self.qr_data

    def release_resources(self):
        self.cap.release()
        cv2.destroyAllWindows()

# Main program calling interface
def recognize_qr_from_video(camera_index=0, timeout=15):
    scanner = QRCodeScanner(camera_index=camera_index, timeout=timeout)
    qr_data = scanner.capture_and_recognize()
    scanner.release_resources()
    return qr_data

# Usage Examples
if __name__ == "__main__":
    qr_text = recognize_qr_from_video(camera_index=22, timeout=15)
    if qr_text:
        print(f"识别到的二维码文本: {qr_text}")
    else:
        print("未能在规定时间内识别二维码")
