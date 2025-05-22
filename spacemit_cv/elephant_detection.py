import cv2
import numpy as np
import onnxruntime as ort
import spacemit_ort
class ElephantDetection:
    def __init__(self, model_path="best.onnx"):
        self.model_path = model_path
        self.class_conf = 0.3
        self.nms_thresh = 0.45
        self.labels = [line.strip() for line in open("spacemit_cv/label.txt", 'r').readlines()]
        self.infer_session= self.init_infer_session()
        self.warm_up_times = 1
        self.input_name = self.infer_session.get_inputs()[0].name
        self.output_name = self.infer_session.get_outputs()[0].name
        self.input_size = self.infer_session.get_inputs()[0].shape[2:4]


    def init_infer_session(self):
        session_options = ort.SessionOptions()
        session_options.intra_op_num_threads = 4

        # Loading ONNX Model
        session = ort.InferenceSession(self.model_path,sess_options=session_options, providers=["SpaceMITExecutionProvider"])

        return session

    def warm_up(self):
        warm_up_img = np.random.rand(1,3, self.input_size[0], self.input_size[1]).astype(np.float32)

        for i in range(self.warm_up_times):
            self.infer_session.run([self.output_name], {self.input_name: warm_up_img})

    def infer(self, image, with_draw=True):
        img = image.copy()

        # Image preprocessing
        input_tensor = self.preprocess(img,self.input_size)
        # Making inferences
        outputs = self.infer_session.run([self.output_name], {self.input_name: input_tensor})
        output = outputs[0]
        offset = output.shape[1]
        anchors = output.shape[2]

        # Post-processing
        dets = self.postprocess(image, output, anchors, offset, self.class_conf,self.input_size)
        dets = self.nms(dets)

        rect_list = self.convert_rect_list(dets)
        class_ids = [int(det[4]) for det in dets]  # Get the category index of all detected objects
        class_names = [self.labels[int(id)] for id in class_ids]  # Get Category Name
        #  Plotting Results
        if with_draw:
            result_img = self.draw_result(img, dets, self.labels)
        else:
            result_img = None

        return result_img, rect_list, class_names

    def preprocess(self, image, input_size=(320, 320)):
        shape = image.shape[:2]
        pad_color=(0,0,0)
        # Resize an image
        # Scale ratio
        r = min(input_size[0] / shape[0], input_size[1] / shape[1])
        # Compute padding
        ratio = r  # width, height ratios
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = input_size[1] - new_unpad[0], input_size[0] - new_unpad[1]  # wh padding
        dw /= 2  # divide padding into 2 sides
        dh /= 2
        if shape[::-1] != new_unpad:  # resize
            image = cv2.resize(image, new_unpad, interpolation=cv2.INTER_LINEAR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=pad_color)  # add border

        # Normalization
        image = image.astype(np.float32) / 255.0
        # Adjust dimensions to match model input [batch, channel, height, width]
        image = np.transpose(image, (2, 0, 1))
        image = np.expand_dims(image, axis=0)

        return image

    def postprocess(self,image,output, anchors, offset, conf_threshold,input_size=(320,320)):
        # Get the height and width of the image
        shape = image.shape[:2]
        # Calculate the scaling factor
        r = min(input_size[0] / shape[0], input_size[1] / shape[1])
        # Calculate the new unfilled size
        new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
        # Calculate fill volume
        dw, dh = input_size[1] - new_unpad[0], input_size[0] - new_unpad[1]
        # Divide the filling equally between the two sides
        dw /= 2
        dh /= 2

        # Remove redundant dimensions of output
        output = output.squeeze()

        # Extract bounding box information (center coordinates, width and height) corresponding to each anchor point
        center_x = output[0, :anchors]
        center_y = output[1, :anchors]
        box_width = output[2, :anchors]
        box_height = output[3, :anchors]

        # Extract all class probabilities corresponding to each anchor point
        class_probs = output[4:offset, :anchors]

        # Find the class index with the highest probability and its probability value under each anchor point
        max_prob_indices = np.argmax(class_probs, axis=0)
        max_probs = class_probs[max_prob_indices, np.arange(anchors)]

        # Filter out anchor points with confidence below the threshold
        valid_mask = max_probs > conf_threshold
        valid_center_x = center_x[valid_mask]
        valid_center_y = center_y[valid_mask]
        valid_box_width = box_width[valid_mask]
        valid_box_height = box_height[valid_mask]
        valid_max_prob_indices = max_prob_indices[valid_mask]
        valid_max_probs = max_probs[valid_mask]

        # Calculate bounding box coordinates
        half_width = valid_box_width / 2
        half_height = valid_box_height / 2
        x1 = np.maximum(0, ((valid_center_x - half_width) - dw) / r).astype(int)
        x2 = np.maximum(0, ((valid_center_x + half_width) - dw) / r).astype(int)
        y1 = np.maximum(0, ((valid_center_y - half_height) - dh) / r).astype(int)
        y2 = np.maximum(0, ((valid_center_y + half_height) - dh) / r).astype(int)

        # Combine results
        objects = np.column_stack((x1, y1, x2, y2, valid_max_prob_indices, valid_max_probs)).tolist()

        return objects

    def nms(self,dets):
        if len(dets) == 0:
            return np.empty((0, 6))

        dets_array = np.array(dets)
        # Group by category
        unique_labels = np.unique(dets_array[:, 4])
        final_dets = []

        for label in unique_labels:
            # Get the detection result of the current category
            mask = dets_array[:, 4] == label
            dets_class = dets_array[mask]

            # Sort by confidence from high to low
            order = np.argsort(-dets_class[:, 5])
            dets_class = dets_class[order]

            # Perform NMS one by one
            keep = []
            while dets_class.shape[0] > 0:
                # Keep the detection result with the highest current confidence
                keep.append(dets_class[0])
                if dets_class.shape[0] == 1:
                    break

                # Calculate the current box and other boxes IoU
                ious = self.calculate_iou(keep[-1], dets_class[1:])
                # Remove boxes whose IoU is greater than the threshold
                dets_class = dets_class[1:][ious < self.nms_thresh]

            # Add the results of the current category to the final results
            final_dets.extend(keep)

        return final_dets


    def calculate_iou(self,box, boxes):
        """
        Calculate the IoU between a box and a group of boxes
        :param box: a single box [x1, y1, x2, y2]
        :param boxes: a group of boxes [N, 4]
        :return: IoU value [N]
        """
        # Calculate the intersection area
        x1 = np.maximum(box[0], boxes[:, 0])
        y1 = np.maximum(box[1], boxes[:, 1])
        x2 = np.minimum(box[2], boxes[:, 2])
        y2 = np.minimum(box[3], boxes[:, 3])
        inter_area = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)

        # Calculate the union area
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        union_area = box_area + boxes_area - inter_area

        # Calculate IoU
        return inter_area / union_area



    # Visualize the results
    def draw_result(self,image, dets, class_names, color=(0, 255, 0), thickness=2):
        image = image.copy()
        image_h, image_w = image.shape[:2]

        for det in dets:
            x1, y1, x2, y2, label, score = det
            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)
            # Draw the bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # print('label:', label)
            cv2.putText(image, f'{class_names[int(label)]}: {score:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        return image


    def convert_rect_list(self,original_list):
        converted_list = []
        for x1, y1, x2, y2, label, prob in original_list:
            width = x2 - x1
            height = y2 - y1
            new_rect = ((x1, y1), width, height, label, prob)
            converted_list.append(new_rect)
        return converted_list