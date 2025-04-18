import cv2
import time
import argparse
from spacemit_orc.ocr import OCRProcessor


def ocr_image(ocr, image_path):
    start_time = time.time()
    results = ocr(image_path)
    end_time = (time.time() - start_time) * 1000
    print(results)
    print(f"Time taken: {end_time:.3f}ms")


class CameraOCR:
    def __init__(self, det_model_path, rec_model_path, rec_dict_path):
        self.ocr = OCRProcessor(det_model_path, rec_model_path, rec_dict_path)
        self.cap = cv2.VideoCapture(22, cv2.CAP_V4L)  # 根据

    def process_frame(self, frame):
        temp_path = "temp_frame.jpg"
        cv2.imwrite(temp_path, frame)
        return self.ocr(temp_path)

    def start_camera(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("无法获取摄像头画面")
                break

            start_time = time.time()
            results = self.process_frame(frame)
            end_time = (time.time() - start_time) * 1000

            print(f"识别结果: {results}")
            print(f"处理时间: {end_time:.3f}ms")

            cv2.imshow("Camera OCR", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(description='OCR 识别工具，支持图片和摄像头识别')
    # parser.add_argument('--mode', type=str, choices=['image', 'camera'], required=True,
    #                     help='选择识别模式,image 为图片识别,camera 为摄像头实时识别')
    # parser.add_argument('--image_path', type=str, default="./temp_frame.jpg",
    #                     help='当 mode 为 image 时，需要提供的图片路径')
    #
    det_model_path = 'spacemit_orc/models/ppocr3_det_fixed.onnx'
    rec_model_path = 'spacemit_orc/models/ppocr_rec.onnx'
    rec_dict_path = 'spacemit_orc/models/rec_word_dict.txt'
    #
    # args = parser.parse_args()
    #
    # if args.mode == 'image':
    #     if args.image_path is None:
    #         print("使用图片识别模式时，需要提供 --image_path 参数。")
    #     else:
    #         ocr = OCRProcessor(det_model_path, rec_model_path, rec_dict_path)
    #         ocr_image(ocr, args.image_path)
    # elif args.mode == 'camera':
    #     camera_ocr = CameraOCR(det_model_path, rec_model_path, rec_dict_path)
    #     camera_ocr.start_camera()
    camera_ocr = CameraOCR(det_model_path, rec_model_path, rec_dict_path)
    camera_ocr.start_camera()