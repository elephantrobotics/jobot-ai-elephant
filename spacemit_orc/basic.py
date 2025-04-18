import cv2
import numpy as np
from onnxruntime import InferenceSession, SessionOptions
import spacemit_ort



class Baseinfer:
    def __init__(self, model_path, use_cpu=False):
        if use_cpu:
            providers = ['CPUExecutionProvider']
        else:
            providers=["SpaceMITExecutionProvider"]       
            

        options = SessionOptions()        
        options.intra_op_num_threads = 4

        self.model = InferenceSession(model_path, providers=providers, sess_options=options)
        self.input_name = self.model.get_inputs()[0].name

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)

    def forward(self, *args, **kwargs):
        ...
