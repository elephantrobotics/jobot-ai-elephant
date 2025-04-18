import json
from ollama import chat

class FCModel:
    def __init__(self, fc_model_name='qwen2.5-0.5b-fc'): # You can modify fc_model_name to your own fine-tuned ollama model.
        self._model_name = fc_model_name

    def get_chat(self, text):
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个人工智能助手。根据用户的输入返回相应的function内容，如果没有相应的function call指令则返回 None 。"
                )
            },
            {
                "role": "user",
                "content": text
            }
        ] 
        response = chat(
            model=self._model_name,
            messages=messages,
        )
        return response

    def func_response(self, text, func_map):
        response = self.get_chat(text)
        print("response:", response)
        content = response['message']['content']
        print("content:", content)
    
        try:
            content = json.loads(content)
            func_name = content.get('function', '').lower()
            if not func_name:
                print("No function name")
                return False
            if func_name not in func_map:
                print(f"function name {func_name} not in function map")
                return False
            args = content.get('arguments', {})
            print("start to execute function:", func_name)
            if not args:
                func_map[func_name]()
                return True
            else:
                func_map[func_name](**args)
                return True
        except Exception as e:
            return False

    def get_function_name(self, text, func_map):
        response = self.get_chat(text)
        print("response:", response)
        content = response['message']['content']
        print("content:", content)
    
        try:
            content = json.loads(content)
            func_name = content.get('function', '').lower()
            if not func_name:
                print("No function name")
                return False, None, None
            if func_name not in func_map:
                print(f"function name {func_name} not in function map")
                return False, None, None
            args = content.get('arguments', {})
            return True, func_name, args or None
        except Exception as e:
            return False, None, None