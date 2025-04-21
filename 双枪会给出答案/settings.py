import time
import random
import pygame
import os

# 颜色参数
blue = (35, 45, 75)
yellow = (255, 255, 0)
red = (255, 0, 0)
white = (255, 255, 255)


# 大小参数
screen_size = (1200, 800)   # 屏幕大小
figure_size = (50, 50)  # 人物大小
bullet_size = (0, 0, 15, 15) # 子弹大小
speed = 1   # 移速
bullet_speed = 2    # 射速
get_health = 10  # 回血量
AL = 3  # 携弹量
cd = 10 # 血包刷新冷却时间


# 图片路径

# 获取当前脚本的目录
base_dir = os.path.dirname(os.path.abspath(__file__))

mkbl_path = os.path.join(base_dir, 'images', '马可波罗.jpg')
lbqh_path = os.path.join(base_dir, 'images', '鲁班七号.jpg')
Boom_path = os.path.join(base_dir, 'images', 'Boom.jpg')
health_pack_path = os.path.join(base_dir, 'images', '血包.jpg')

# 玩家设置
class Player(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.face = [0, 1]
        self.front = [0, 1]
        self.HP = 100
        self.AP = 20
        img = pygame.image.load(image_path)
        self.image = pygame.transform.scale(img, figure_size)
        self.rect = self.image.get_rect()
    
    def update(self):
        pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, a, b):
        super().__init__()
        self.face = [a, b]


def play_explosion(screen, position):
    image = pygame.image.load(Boom_path)
    image = pygame.transform.scale(image, figure_size)
    screen.blit(image, position)
    pygame.display.flip()
    time.sleep(0.1)


health_packs = pygame.sprite.Group()

class HealthPack(pygame.sprite.Sprite):
    def __init__(self, position):
        super().__init__()
        img = pygame.image.load(health_pack_path)
        self.image = pygame.transform.scale(img, figure_size)
        self.rect = self.image.get_rect()
        self.rect.topleft = position

def spawn_health_pack():
    x = random.randint(0, screen_size[0] - figure_size[0])
    y = random.randint(0, screen_size[1] - figure_size[1])
    health_pack = HealthPack((x, y))
    health_packs.add(health_pack)