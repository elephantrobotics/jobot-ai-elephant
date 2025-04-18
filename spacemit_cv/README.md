## 依赖安装

```shell
sudo apt update
sudo apt upgrade
sudo apt install python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install --index-url https://git.spacemit.com/api/v4/projects/33/packages/pypi/simple opencv-python==4.6.8.1

```

## 执行方法

```shell
python cv_robot_arm_demo.py #默认是加载spacemit_cv/yolov8n.q.onnx模型，推理spacemit_cv/test.jpg,可使用--model 和--image 指定模型和图片路径，还有--use-camera来使用摄像头进行推理
```



## 接口说明

```python
# 创建基础类
detector = ElephantDetection(模型路径)
# 执行推理
result_image, rect_list = detector.infer() #result_image为画好框的图像，rect_list为[x,y,w,h,class,prob]的列表
```

