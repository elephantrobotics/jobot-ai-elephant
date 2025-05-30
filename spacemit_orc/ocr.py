import cv2
import numpy as np
from pyclipper import PyclipperOffset, JT_ROUND, ET_CLOSEDPOLYGON
from math import ceil
from typing import Union, Tuple, Iterator, Optional, List
from .basic import Baseinfer

class TextDetector(Baseinfer):
    def __init__(self, model_path: str,
                 min_score: float = 0.6,
                 use_cpu: bool = False):
        """
        Text detector
        :param model_path: Path to the text detection model
        :param min_score: Minimum confidence score required for text box detection
        """
        super().__init__(model_path, use_cpu)

        self._limit_side_len = 960
        self._input_mean = np.float32([0.485, 0.456, 0.406]).reshape((1, 1, 3))
        self._input_std = np.float32([0.229, 0.224, 0.225]).reshape((1, 1, 3))
        self.min_size = 4
        self.threshold = 0.3
        self.box_threshold = min_score
        self.max_candidates = 1000
        self.expansion_ratio = 1.6

    def _preprocess(self, img_obj: Union[str, bytes, np.ndarray]) -> Tuple[np.ndarray, np.ndarray, int, int]:
        """
        Image preprocessing, limit the input image size
        :param img_obj: image object
        :return: returns four parameters, the first one is the processed image, the second one is the original image, and the third and fourth ones are the width and height of the image respectively
        """
        if isinstance(img_obj, str):
            image = cv2.imread(img_obj)
            if image is None:
                raise ValueError(f"无法读取图像路径: {img_obj}")
        elif isinstance(img_obj, bytes):
            image_np = np.frombuffer(img_obj, dtype=np.uint8)
            image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("无法解码图像字节流")
        elif isinstance(img_obj, np.ndarray):
            image = img_obj
        else:
            raise TypeError("img_obj 必须是 str, bytes 或 np.ndarray 类型")

        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        img = np.array(image)

        h, w = img.shape[:2]
        if (max_side := max(h, w)) > self._limit_side_len:
            obj_w, obj_h = (self._limit_side_len, self._limit_side_len / w * h) if w > h else (self._limit_side_len / h * w, self._limit_side_len)
        else:
            obj_w, obj_h = w, h

        obj_w = max(int(round(obj_w / 32) * 32), 32)
        obj_h = max(int(round(obj_h / 32) * 32), 32)

        img2 = cv2.resize(img, (obj_w, obj_h), interpolation=cv2.INTER_AREA if max_side > self._limit_side_len else cv2.INTER_LINEAR)
        return img2, img, w, h

    def _preprocess2(self, input_img: np.ndarray) -> np.ndarray:
        """
        Image preprocessing step 2
        :param input_img: preprocessed image
        :return: data available for model input
        """
        input_tensor = input_img.astype(np.float32)
        input_tensor /= 255
        input_tensor -= self._input_mean
        input_tensor /= self._input_std
        return input_tensor.transpose((2, 0, 1))[np.newaxis, ...]

    def _postprocess(self, confidence_mask: np.ndarray, ori_w: int, ori_h: int) -> List[dict]:
        """
        Post-processing, get text area information
        :param confidence_mask: Model inference result
        :param ori_w: original image width
        :param ori_h: original image height
        :return: Returns a list of dictionaries containing text area position, text area confidence, and text area center point
        """
        height, width = confidence_mask.shape
        mask = (confidence_mask > self.threshold).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        ocr_results = []

        for contour in contours[:self.max_candidates]:
            rect_obj = cv2.minAreaRect(contour)
            if min(rect_obj[1]) < self.min_size:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            mask2 = np.zeros((h, w), dtype=np.uint8)
            contour2 = contour.copy()
            contour2[..., 0] = contour2[..., 0] - x
            contour2[..., 1] = contour2[..., 1] - y
            cv2.fillPoly(mask2, [contour2], (1,))
            score = confidence_mask[y:y+h, x:x+w][mask2 == 1].mean()

            if score < self.box_threshold:
                continue

            points = cv2.boxPoints(rect_obj)
            distance = cv2.contourArea(points) * self.expansion_ratio / cv2.arcLength(points, True)
            offset = PyclipperOffset()
            offset.AddPath(points, JT_ROUND, ET_CLOSEDPOLYGON)
            new_contour = np.array(offset.Execute(distance)[0])
            rect_obj = cv2.minAreaRect(new_contour)
            if min(rect_obj[1]) < self.min_size + 2:
                continue

            points = cv2.boxPoints(rect_obj)
            points[:, 0] = points[:, 0] / width * ori_w
            points[:, 1] = points[:, 1] / height * ori_h
            center_point = (rect_obj[0][0] / width * ori_w, rect_obj[0][1] / height * ori_h)
            dic = {'points': points, 'score': score, 'center_point': center_point}
            ocr_results.append(dic)

        return ocr_results

    def forward(self, img_obj: Union[str, bytes, np.ndarray]) -> Tuple[list, np.ndarray]:
        """
        Input image to get text box information
        :param img_obj: image object
        :return: Returns two parameters, the first one is a list of dictionaries containing text area position, text area confidence, and text area center point, and the second parameter is the original image in BGR format ndarray
        """
        input_img, ori_img, ori_w, ori_h = self._preprocess(img_obj)
        input_tensor = self._preprocess2(input_img)
        output_tensor = self.model.run(None, {self.input_name: input_tensor})[0][0, 0]
        return self._postprocess(output_tensor, ori_w, ori_h), ori_img

    @staticmethod
    def warp_box(det_results: List[dict], ori_img: np.ndarray) -> Iterator:
        """
        Radially transform the text boxes at different angles in the original image for subsequent text direction judgment and text recognition
        :param det_results: Results returned by the text detector
        :param ori_img: Original image
        :return: Returns the generator of the text box image with angle correction
        """
        for result in det_results:
            start_idx = result['points'].sum(axis=1).argmin()
            points = np.roll(result['points'], 4 - start_idx, axis=0)
            w = int(np.linalg.norm(points[0] - points[1])) + 1
            h = int(np.linalg.norm(points[0] - points[3])) + 1
            new_points = np.float32([[0, 0], [w, 0], [w, h], [0, h]])

            m = cv2.getPerspectiveTransform(points, new_points)
            warp_img = cv2.warpPerspective(ori_img, m, (w, h))
            if h / w >= 1.5:
                warp_img = np.rot90(warp_img)
            yield warp_img


class TextClassifier(Baseinfer):
    def __init__(self, model_path: str,
                 cls_threshold: float = 0.9,
                 use_cpu: bool = False):
        """
        Text direction classifier
        :param model_path: Path to the text direction classifier model
        :param cls_threshold: Minimum confidence level for direction classification
        :param use_cpu: Whether to use only CPU
        """
        super().__init__(model_path, use_cpu)

        self.cls_threshold = cls_threshold
        self._input_size = (3, 48, 192)
        self._labels = (0, 180)
        self._input_mean = 127.5
        self._input_std = 127.5

    def _preprocess(self, img_obj: Union[str, bytes, np.ndarray]) -> np.ndarray:
        """
        Image preprocessing, fix the height ratio of the text box image to a fixed size
        :param img_obj: image object
        :return: returns the processed image
        """
        img = img_obj.copy()
        h, w = img.shape[:2]
        scale = self._input_size[1] / h
        obj_w = ceil(w * scale)
        # if obj_w > self._input_size[2]:
        #     obj_w = self._input_size[2]

        img2 = cv2.resize(img, (obj_w, self._input_size[1]), interpolation=cv2.INTER_AREA if scale <= 1 else cv2.INTER_CUBIC)
        return img2

    def _preprocess2(self, input_img: np.ndarray) -> np.ndarray:
        """
        Image preprocessing step 2
        :param input_img: preprocessed image
        :return: data available for model input
        """
        input_tensor = input_img.transpose((2, 0, 1)).astype(np.float32)
        input_tensor -= self._input_mean
        input_tensor /= self._input_std
        return input_tensor[np.newaxis, ...]

    def _postprocess(self, each_output: np.ndarray) -> int:
        """
        Post-processing, determine the image angle
        :param each_output: model inference result
        :return: return image angle, 0 or 180
        """
        idx = each_output.argmax()
        score = np.max(each_output)
        return self._labels[1] if idx == 1 and score >= self.cls_threshold else self._labels[0]

    def forward(self, img_obj: Union[str, bytes, np.ndarray]) -> int:
        """
        Input image to get angle
        :param img_obj: image object
        :return: return image angle, 0 or 180
        """
        input_img = self._preprocess(img_obj)
        input_tensor = self._preprocess2(input_img)
        outputs = self.model.run(None, {self.input_name: input_tensor})[0][0]
        return self._postprocess(outputs)


class TextRecognizer(Baseinfer):
    def __init__(self, model_path: str,
                 text_path: str,
                 rec_threshold: float = 0.5,
                 use_cpu: bool = False):
        """
        Text recognizer
        :param model_path: Path to the text recognition model
        :param text_path: Path to the text library
        :param rec_threshold: Confidence of text recognition, meaningless
        :param use_cpu: Whether to use only CPU
        """
        super().__init__(model_path, use_cpu)

        self.rec_threshold = rec_threshold
        self._input_size = (3, 48, 320)
        self._input_mean = 127.5
        self._input_std = 127.5
        with open(text_path, 'r', encoding='utf8') as f:
            self._texts = f.read().replace('\n', '') + ' '

    def _preprocess(self, img_obj: Union[str, bytes, np.ndarray]) -> np.ndarray:
        """
        Image preprocessing, fix the height ratio of the text box image to a fixed size
        :param img_obj: image object
        :return: returns the processed image
        """
        #img = read_image(img_obj)
        img = img_obj.copy()
        h, w = img.shape[:2]
        scale = self._input_size[1] / h
        obj_w = ceil(w * scale)

        img2 = cv2.resize(img, (obj_w, self._input_size[1]), interpolation=cv2.INTER_AREA if scale <= 1 else cv2.INTER_CUBIC)
        return img2

    def _preprocess2(self, input_img: np.ndarray) -> np.ndarray:
        """
        Image preprocessing step 2
        :param input_img: preprocessed image
        :return: data available for model input
        """
        input_tensor = input_img.transpose((2, 0, 1)).astype(np.float32)
        input_tensor -= self._input_mean
        input_tensor /= self._input_std
        return input_tensor[np.newaxis, ...]

    def _postprocess(self, each_output: np.ndarray) -> str:
        """
        Post-processing, judging the text recognition results
        :param each_output: model inference results
        :return: text recognition results
        """
        text_idx_li = each_output.argmax(axis=1)
        content = ''.join([self._texts[i - 1] for idx, i in enumerate(text_idx_li) if i != 0 and not (idx > 0 and text_idx_li[idx - 1] == text_idx_li[idx])])
        return content

    def forward(self, img_obj: Union[str, bytes, np.ndarray]) -> str:
        """
        Input image to get text recognition result
        :param img_obj: image object
        :return: text recognition result
        """
        input_img = self._preprocess(img_obj)
        input_tensor = self._preprocess2(input_img)
        outputs = self.model.run(None, {self.input_name: input_tensor})[0][0]
        return self._postprocess(outputs)


class OCRProcessor:
    def __init__(self, det_model_path: str,
                 rec_model_path: str,
                 text_path: str,
                 cls_model_path: Optional[str] = None,
                 use_cpu: bool = False,
                 save_warp_img: bool = False):
        """
        Text recognition
        :param det_model_path: Path to the text detection model
        :param rec_model_path: Path to the text recognition model
        :param text_path: Path to the text library
        :param cls_model_path: Path to the text direction classifier model. If direction detection is not required, this item can be cancelled to increase the speed
        :param use_cpu: Whether to use only CPU
        :param save_warp_img: Save each text area image, not saved by default
        """
        self.text_detector = TextDetector(det_model_path,use_cpu=use_cpu)
        self.text_recognizer = TextRecognizer(rec_model_path, text_path, use_cpu=use_cpu)
        self.text_classifier = TextClassifier(cls_model_path, use_cpu=use_cpu) if cls_model_path else None
        self.save_warp_img = save_warp_img


    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, img_obj: Union[str, bytes, np.ndarray]) -> List[dict]:
        """
        Input image to get the result after text recognition
        :param img_obj: image path, image byte data or ndarray array in BGR format
        :return: Returns a list of dictionaries containing recognition results, text area location, text area confidence, and text area center point
        """
        results, ori_img = self.text_detector.forward(img_obj)
        ocr_results = []

        for idx, i in enumerate(self.text_detector.warp_box(results, ori_img)):
            if self.text_classifier is not None:
                angle = self.text_classifier.forward(i)
                if angle == 180:
                    i = cv2.rotate(i, cv2.ROTATE_180)
            content = self.text_recognizer.forward(i)
            if not content:
                continue

            results[idx]['content'] = content
            ocr_results.append(results[idx])
            if self.save_warp_img:
                cv2.imwrite(f'{idx}.jpg', i)

        return ocr_results[::-1]


def main():
    from argparse import ArgumentParser
    import time

    parse = ArgumentParser(description='文字识别')
    parse.add_argument('-i', '--input_image', required=True, metavar='', help='需要检测的图像')
    parse.add_argument('-m1', '--det_model_path', required=True, metavar='', help='文字检测模型的路径')
    parse.add_argument('-m2', '--rec_model_path', required=True, metavar='', help='文字识别模型的路径')
    parse.add_argument('-t', '--text_path', required=True, metavar='', help='文本库的路径')
    parse.add_argument('-m3', '--cls_model_path', default='', metavar='', help='文字方向分类器模型的路径，如不需要方向检测可取消此项以提升速度')
    parse.add_argument('--use_cpu', action='store_true', default=False, help='仅使用cpu')
    parse.add_argument('--save_warp_img', action='store_true', default=False, help='保存每个文本区域图片，默认不保存')
    args = parse.parse_args()

    ocr = OCRProcessor(args.det_model_path, args.rec_model_path, args.text_path, args.cls_model_path,
                       args.use_cpu, args.save_warp_img)
    start = time.time()
    results = ocr(args.input_image)
    print(f'文字识别总用时：{time.time()-start} s')
    print(results)


if __name__ == '__main__':
    main()
