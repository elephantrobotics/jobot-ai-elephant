import time
import cv2
import threading
import difflib

lock = threading.Lock()

def grab_simple_async(center_point, object_name, motion_control):
    """抓取某物体放置到某位置
    Args:
        object_name: 用户选择抓取的物体类别
        motion_control: 机械臂控制类
    """
    # 执行抓取
    center_x, center_y = center_point
    motion_control.convert_to_real_coordinates_simple(center_x, center_y)
    return f"✅ 已抓取 {object_name} "

def grab_async(center_point, object_name, motion_control):
    """抓取某物体放置到某位置
    Args:
        object_name: 用户选择抓取的物体类别
        motion_control: 机械臂控制类
    """
    # Execute the crawl
    center_x, center_y = center_point
    motion_control.convert_to_real_coordinates(center_x, center_y)
    return f"✅ 已抓取 {object_name} "

# Function name mapping table
func_map = {
    "grab_an_object_and_place_it_in_a_position": grab_simple_async
}

# Define valid object categories
valid_classes = [
    "jeep", "grape", "pear", "refrigerator1", "refrigerator2", "sofe", "sofe2", "washing machine1",
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]


# Identify whether there is a function call
def execute_command(user_input, object_name_dict):
    valid_commands = list(object_name_dict.keys())
    match = difflib.get_close_matches(user_input, valid_commands, n=1, cutoff=0.6)
    if match:
        try:
            _name = object_name_dict[match[0]]
            return True, _name
        except:
            return False, None
    else:
        return False, None

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