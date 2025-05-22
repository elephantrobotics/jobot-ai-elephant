from pymycobot import *
import time
# 默认使用9000端口
mc = MyCobot280('/dev/ttyAMA0', 1000000)

mc.send_angles([5.88, -11.33, -60.11, -16.69, 4.3, -121.55],20)

ccc = mc.get_coords()
# mc.send_angles([0,0,0,0,0,0],20)

print(ccc)
time.sleep(2)
