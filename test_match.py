from tools.elephant import func_map, object_name_dict_zh
import difflib

# 识别是否有函数调用
def execute_command(user_input):
    valid_commands = list(object_name_dict_zh.keys())
    
    # 使用 difflib 进行模糊匹配
    match = difflib.get_close_matches(user_input, valid_commands, n=1, cutoff=0.6)
    
    if match:
        try:
            _name = object_name_dict_zh[match[0]]
            return True, _name
        except:
            return False, None
    else:
        return False, None


if __name__ == '__main__':
    
    try:
        while True:
            text = input("请输入: ")
            ret, object_name = execute_command(text)
            if ret:
                print(f"识别到语义为: {object_name}")
                user_input = object_name 
            else:
                print("大模型开始理解")

    except KeyboardInterrupt:
        print("process was interrupted by user.")