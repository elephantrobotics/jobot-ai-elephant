
def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper

@singleton
class Pixel2World:
    def __init__(self):

        # 末端抓取的坐标偏移量,单位mm
        # self.x_offset = 83
        # self.y_offset = -60
        self.x_offset = -83
        self.y_offset = -80
        self.world_ratio = 204 / 480 

    def simple_convert(self, x_pixel, y_pixel):

        world_ratio = self.world_ratio
        x = round(y_pixel * world_ratio, 2)
        y = round(x_pixel * world_ratio, 2)

        x_world = x + self.x_offset
        y_world = y + self.y_offset

        return x_world, y_world


