import cv2
import numpy as np
import onnxruntime as ort
#import spacemit_ort

class AGVDetection:
    def __init__(self, config_path="agv_config.yaml"):
        self.config = self._load_config(config_path)

    def _load_config(self, path):
        # 加载AGV检测配置的逻辑
        pass

    def detect(self, image):
        # 检测逻辑
        pass
        #return results
