import time
import threading
import traceback
import numpy as np
import math
from pymycobot import *
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
from gpiozero import LED

from spacemit_cv.QRCodeScanner import recognize_qr_from_video
from .coordinate_transformation import Pixel2World


class ElephantMotionControl(object):
    def __init__(self):
        self._is_busy = False
        # 初始化机械臂对象
        self.mc = MyCobot280('/dev/ttyAMA0', 1000000)
        Device.pin_factory = LGPIOFactory(chip=0)  # Explicitly specify /dev/gpiochip0
        # Initialize GPIO controlled devices
        self.valve = LED(72)
        self.gpio_status(False)

        self.pixel2world_calc = Pixel2World()

        # Initial coordinates
        self.cam_coords = [194.3, -40.2, 235.1, -177.29, -3.82, 37.42]
        # Identify the area angle position
        self.detect_area_angle_position = [5.88, -11.33, -60.11, -16.69, 4.3, -121.55]
        # Angle position of product storage area
        self.storage_area_angle_position = [-58.88, -3.95, -53.7, -31.11, 1.23, -26.36]
        # Scan code to settle the transaction area location angle
        self.payment_transaction_area_angle_position = [99.93, -3.42, -84.46, -4.57, 1.66, -2.28]

        # Coordinate motion velocity
        self.coords_speed = 100
        # Angular motion velocity
        self.angles_speed = 50

        # Used to determine whether the current task is completed, the default is True
        self.task_completed = True

        # Determine exercise mode
        self.is_interpolation_mode()

        # By default, the robot arm returns to the recognition area.
        self.return_to_initial_point()

    def is_busy(self):
        return self._is_busy

    def is_interpolation_mode(self):
        """
        Determine whether the robot is in interpolation mode. If not, you need to set the interpolation mode.
        """
        if self.mc.get_fresh_mode() == 1:
            # Set the interpolation mode
            self.mc.set_fresh_mode(0)

    def gpio_status(self, flag):
        if flag:
            self.valve.off()
            time.sleep(0.05)
        else:
            self.valve.on()
            time.sleep(0.05)

    def check_position(self, data, ids, max_same_data_count=50):
        """
        Loop to check if a certain position is reached
        :param data: Angle or coordinate
        :param ids: Angle - 0, coordinate - 1
        :return:
        """
        try:
            same_data_count = 0
            while True:
                if ids == 1:
                    xyz_tolerance = 4.0
                    angle_tolerance = 3.0

                    # ball
                    xyz_tolerance = math.sqrt(3 * xyz_tolerance**2)
                    angle_tolerance = math.sqrt(3 * angle_tolerance**2)

                    for i in range(4):
                        current_coords = self.mc.get_coords()
                        if type(current_coords) == list:
                            break
                    distance_xyz = np.linalg.norm(np.array(current_coords[:3]) - np.array(data[:3]))
                    distance_angle = np.linalg.norm(np.array(current_coords[3:]) - np.array(data[3:]))

                    # print(f"a = {distance_xyz:.2f}, b = {distance_angle:.2f}")

                    if distance_xyz <= xyz_tolerance and distance_angle <= angle_tolerance:
                        break
                else:
                    angle_tolerance = 3.0
                    angle_tolerance = math.sqrt(3 * angle_tolerance**2)

                    for i in range(4):
                        current_angles = self.mc.get_angles()
                        if type(current_angles) == list:
                            break
                    distance_angle = np.linalg.norm(np.array(current_angles) - np.array(data))

                    # print(f"b = {distance_angle:.2f}")
                    if distance_angle <= angle_tolerance:
                        break

                same_data_count += 1
                if same_data_count >= max_same_data_count:
                    break
                time.sleep(0.1)
        except Exception as e:
            e = traceback.format_exc()
            print(e)

    def purchased_goods_storage_area(self):
        """
        Angle position of the purchased goods storage area
        """
        self.mc.send_angles(self.storage_area_angle_position, self.angles_speed)
        self.check_position(self.storage_area_angle_position, 0)

    def return_payment_transaction_area(self):
        """
        Scan code to settle the transaction area angle position
        """
        self.mc.send_angles(self.payment_transaction_area_angle_position, self.angles_speed)
        self.check_position(self.payment_transaction_area_angle_position, 0)

    def return_to_initial_point(self):
        """
        The robot arm returns to the initial point, that is, the angle position of the recognition area
        """
        self.mc.send_angles(self.detect_area_angle_position, self.angles_speed)
        self.check_position(self.detect_area_angle_position, 0)

    def return_get_init_point_coords(self):
        """
        Re-obtain the coordinates of the recognition area location points
        """
        self.cam_coords = None
        while self.cam_coords is None:
            self.cam_coords = self.mc.get_coords()
            # print('new-----new----cam_coords', self.cam_coords)

    def convert_to_real_coordinates(self, x_pixel, y_pixel):
        """
        Convert pixel coordinates to real coordinates and move the robot
        :param x_pixel: X coordinate of the pixel center of the object
        :param y_pixel: Y coordinate of the pixel center of the object
        """
        if not self.task_completed:
            return
        self.task_completed = False  # Mark a task as in progress

        # Calculate new coordinates
        x_world, y_world = self.pixel2world_calc.simple_convert(x_pixel, y_pixel)
        self.cam_coords[0] = self.cam_coords[0] + x_world
        self.cam_coords[1] = self.cam_coords[1] + y_world
        self.cam_coords[2] = 170

        print(f"Move to new coordinates: {self.cam_coords}")

        def move_robot():
            """
            Control the robot arm to move and grab, and start it using a child thread
            """
            self._is_busy = True
            # Move over the object
            # self.mc.send_coords(self.cam_coords, self.coords_speed, 1)
            # self.check_position(self.cam_coords, 1, max_same_data_count=20)
            self.cam_coords[2] = 97
            # Move to the surface of the object and prepare to grab it
            self.mc.send_coords(self.cam_coords, self.coords_speed, 1)
            self.check_position(self.cam_coords, 1, max_same_data_count=12)
            # Start the suction pump
            self.gpio_status(True)
            # Move to the top of the object and prepare to place it
            self.cam_coords[2] = 230
            self.mc.send_coords(self.cam_coords, self.coords_speed, 1)
            self.check_position(self.cam_coords, 1, max_same_data_count=12)
            # Place the object in the merchandise storage area
            self.purchased_goods_storage_area()
            print('开始二维码文字识别----')
            qr_text = recognize_qr_from_video(camera_index=22, timeout=15)

            if qr_text:
                print(f"识别到的二维码文本: {qr_text}")

            else:
                print("二维码识别失败或超时，任务未能继续")
            # Place the object in the scan code settlement transaction area
            self.return_payment_transaction_area()
            self.gpio_status(False)
            # The robot arm returns to its initial position
            self.return_to_initial_point()
            self._is_busy = False
            # Complete the task and start the next recognition
            self.task_completed = True
            # Re-obtain the coordinates of the initial point of the recognition position
            self.return_get_init_point_coords()

        # Use threads to execute robot actions to avoid lag
        threading.Thread(target=move_robot).start()


    def convert_to_real_coordinates_simple(self, x_pixel, y_pixel):
        """
        转换像素坐标为实际坐标并移动机械臂
        :param x_pixel: 物体的像素中心点X坐标
        :param y_pixel: 物体的像素中心点Y坐标
        """
        if not self.task_completed:
            return  # 如果任务还没有完成，直接跳过
        self.task_completed = False  # 标记任务为进行中

        # 计算新的坐标
        x_world, y_world = self.pixel2world_calc.simple_convert(x_pixel, y_pixel)
        self.cam_coords[0] = self.cam_coords[0] + x_world
        self.cam_coords[1] = self.cam_coords[1] + y_world
        self.cam_coords[2] = 170

        def move_robot():
            """
            控制机械臂移动抓取，使用子线程启动
            """
            self._is_busy = True
            # 移动到物体上方
            # self.mc.send_coords(self.cam_coords, self.coords_speed, 1)
            # self.check_position(self.cam_coords, 1, max_same_data_count=12)
            self.cam_coords[2] = 97
            # 移动到物体表面，准备抓取
            self.mc.send_coords(self.cam_coords, self.coords_speed, 1)
            self.check_position(self.cam_coords, 1, max_same_data_count=12)
            # 开启吸泵
            self.gpio_status(True)
            # 移动到物体上方，准备放置
            self.cam_coords[2] = 230
            self.mc.send_coords(self.cam_coords, self.coords_speed, 1)
            self.check_position(self.cam_coords, 1, max_same_data_count=12)

            # 将物体放置到商品存放区
            self.purchased_goods_storage_area()

            self.gpio_status(False)
            # 机械臂回到初始位置
            self.return_to_initial_point()
            self._is_busy = False
            # 完成任务,开启下一次识别
            self.task_completed = True
            # 重新获取识别位置初始点坐标
            self.return_get_init_point_coords()

        # 使用线程执行机器人动作，避免卡顿
        # threading.Thread(target=move_robot).start()
        move_robot()
