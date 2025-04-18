"""
elephant_function_map.py
This module controls the grabbing of the object category name entered by the user, thereby calling the grabbing program of the robot arm

Author: Wang Weijian
Date: 2025-04-18
"""

import time
import cv2
import threading
lock = threading.Lock()


def grab_an_object_and_place_it_in_a_position(object_name, latest_frame, motion_control, detector):
    """Grab an object
    Args:
        object_name: The category of the object selected by the user
        latest_frame: The latest video frame
        motion_control: Robotic arm control class
        detector: Object recognition detector

    """
    print("ok")
    # Get the latest frame
    with lock:
        if latest_frame is None:
            print("No screen information")
            return
        frame_copy = latest_frame.copy()

    # Re-recognize a frame (you can also choose to use result_image directly)
    result_image, rect_list, classnames = detector.infer(frame_copy)
    print(f"{len(rect_list)} targets detected, category:{classnames}")

    # Traverse to find matching categories
    for idx, rect in enumerate(rect_list):
        label = classnames[idx]
        if label == object_name:
            (x1, y1), width, height, *_ = rect
            center_x = x1 + width // 2
            center_y = y1 + height // 2
            print(f"Found the target {object_name}, center point: ({center_x}, {center_y})")

            # Execute the crawl
            motion_control.convert_to_real_coordinates(center_x, center_y)
            return f"✅ Crawled {object_name} "

    return f"❌ No target of category '{object_name}' found, please try again"


# Function name mapping table
func_map = {
    "grab_an_object_and_place_it_in_a_position": grab_an_object_and_place_it_in_a_position
}


## Fuzzy matching, quick demo available
object_name_dict_zh = {
    "吉普车": "jeep", "吉普": "jeep", "抓吉普": "jeep", "拿吉普": "jeep",
    "苹果": "apple", "抓苹果": "apple", "拿苹果": "apple",
    "香蕉": "banana", "抓香蕉": "banana", "拿香蕉": "banana",
    "床": "bed", "拿床": "bed",
    "葡萄": "grape", "抓葡萄": "grape", "拿葡萄": "grape",
    "笔记本电脑": "laptop", "拿笔记本电脑": "laptop",
    "微波炉": "microwave", "拿微波炉": "microwave", "抓微波炉": "microwave",
    "橙子": "orange", "桔子": "orange" ,"橘子": "orange", "拿橘子": "orange", "抓取橘子": "orange",
    "梨": "pear", "梨子": "pear", "抓例子": "pear", "拿栗子": "pear",
    "冰箱1": "refrigerator1", "拿冰箱1": "refrigerator1",
    "冰箱2": "refrigerator2", "拿冰箱2": "refrigerator2",
    "沙发": "sofe", "拿沙发": "sofe",
    "沙发2": "sofe2", "拿沙发2": "sofe2",
    "电视": "tv", "拿电视": "tv",
    "洗衣机1": "washing machine1", "拿洗衣机1": "washing machine1",

    "请简单用一段话介绍一下你自己":'intro', "介绍一下你自己":'intro', "自我介绍一下":'intro', 
    "开始结算":'start checkout', "结算":'start checkout', "算账":'start checkout', "算钱":'start checkout', "结账":'start checkout', "买单":'start checkout', "帮我结算吧":'start checkout'
}


sys_mes = (
    "你是一个用于识别用户想要的物体名称的助手。请从下面的句子中提取用户提到的目标物体，只返回物体的名称，不要添加任何其他内容，也不要重复：\n"
    "输入：我要一个香蕉, 输出：香蕉\n"
    "输入：买一个橘子, 输出：橘子\n"
    "输入：请抓一下那个橘子，输出：橘子\n"  
)