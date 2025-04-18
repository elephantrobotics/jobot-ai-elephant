from spacemit_cv import ElephantDetection
import cv2
import numpy as np
import argparse

def main(args):
    # 初始化检测器
    detector = ElephantDetection(args.model)    
    detector.warm_up()
    # 读取图像
    if args.use_camera:
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # 进行检测
            result_image, rect_list = detector.infer(frame)
            # 显示结果
            cv2.imshow('frame', result_image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
    else:
        # 读取图像
        image = cv2.imread(args.image)
        # 进行检测
        result_image, rect_list = detector.infer(image)
        # 显示结果
        cv2.imwrite('result.jpg', result_image)
        # cv2.imshow('frame', result_image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
    


if __name__ == '__main__':

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='YOLOv8 ONNX Inference')
    parser.add_argument('--model', type=str, default='spacemit_cv/yolov8n.q.onnx', help='Path to the YOLOv8 ONNX model')
    parser.add_argument('--image', type=str, default='spacemit_cv/test.jpg', help='Path to the input image')
    parser.add_argument('--use-camera', action='store_true', help='Use camera as input')
    args = parser.parse_args()
    
    main(args)