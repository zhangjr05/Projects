import os
import json
import copy
import random

# 定义游戏常量
GRID_SIZE = 4  # 游戏网格大小 4x4
CELL_SIZE = 100  # 每个格子的像素大小
PADDING = 10  # 格子间距
SCORE_AREA = 50  # 额外的50像素用于显示分数
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * PADDING
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * PADDING + SCORE_AREA # 额外的像素用于显示分数

# 游戏状态
GAME_RUNNING = 0 # 游戏会继续运行
GAME_WON = 1 # 在庆祝信息显示1s后恢复运行状态
GAME_LOST = 2 # 游戏结束运行，等待用户操作

# 随机生成2的概率
RANDOM_P_TWO = 0.9

TWO = 2
FOUR = 4

# AI移动延迟 (ms)
AI_DELAY = 80

# 主题定义
THEMES = {
    "classic": {
        "name": "经典",
        "background": (187, 173, 160),  # 浅棕灰色
        "empty_cell": (204, 192, 179),  # 浅米色
        "text_light": (119, 110, 101),  # 深灰褐色
        "text_dark": (249, 246, 242),   # 米白色
        "overlay": (255, 255, 255, 150),  # 半透明白色
        "tile_colors": {
            0: (204, 192, 179),  # 浅米色
            2: (100, 200, 230),  # 蓝色
            4: (80, 180, 250),   # 深蓝色
            8: (70, 220, 180),   # 青绿色
            16: (60, 200, 150),  # 绿色
            32: (80, 230, 120),  # 浅绿色
            64: (120, 210, 100), # 黄绿色
            128: (160, 190, 220), # 淡蓝紫色
            256: (170, 160, 240), # 浅紫色
            512: (180, 130, 220), # 中紫色
            1024: (190, 100, 200), # 深紫色
            2048: (200, 70, 180), # 紫红色
            4096: (210, 50, 160), # 深紫红色
            8192: (220, 40, 140)  # 紫粉色
        }
    },
    "dark": {
        "name": "暗黑",
        "background": (30, 32, 38),     # 深灰黑色
        "empty_cell": (50, 53, 60),     # 深灰色
        "text_light": (190, 195, 200),  # 浅灰色
        "text_dark": (255, 255, 255),   # 纯白色
        "overlay": (0, 0, 0, 150),      # 半透明黑色
        "tile_colors": {
            0: (50, 53, 60),      # 深灰色
            2: (40, 100, 150),    # 深蓝色
            4: (50, 130, 170),    # 蓝色
            8: (60, 160, 140),    # 青色
            16: (50, 150, 100),   # 绿色
            32: (70, 170, 80),    # 浅绿色
            64: (100, 170, 60),   # 黄绿色
            128: (120, 100, 170), # 浅紫色
            256: (140, 90, 190),  # 紫色
            512: (160, 80, 200),  # 深紫色
            1024: (170, 70, 180), # 紫红色
            2048: (180, 60, 160), # 深紫红色
            4096: (190, 50, 140), # 紫粉色
            8192: (190, 50, 140)  # 紫粉色
        }
    },
    "neon": {
        "name": "霓虹",
        "background": (5, 5, 5),          # 纯黑色背景
        "empty_cell": (20, 20, 30),       # 深蓝黑色
        "text_light": (230, 230, 255),    # 亮蓝白色
        "text_dark": (255, 255, 255),     # 纯白色
        "overlay": (0, 0, 100, 150),      # 半透明深蓝色
        "tile_colors": {
            0: (20, 20, 30),        # 深蓝黑色
            2: (0, 180, 255),       # 鲜亮霓虹蓝
            4: (0, 255, 220),       # 霓虹青色
            8: (0, 255, 120),       # 霓虹绿色
            16: (120, 255, 0),      # 霓虹黄绿
            32: (220, 255, 0),      # 霓虹黄色
            64: (255, 180, 0),      # 霓虹橙色
            128: (255, 80, 0),      # 霓虹红橙
            256: (255, 0, 80),      # 霓虹红色
            512: (255, 0, 200),     # 霓虹粉红
            1024: (220, 0, 255),    # 霓虹紫红
            2048: (140, 0, 255),    # 霓虹紫色
            4096: (70, 0, 255),     # 霓虹蓝紫
            8192: (0, 50, 255)      # 霓虹深蓝
        },
        "glow": True
    },
    "ocean": {
        "name": "海洋",
        "background": (10, 40, 65),      # 深海蓝
        "empty_cell": (20, 60, 85),      # 深蓝色
        "text_light": (150, 210, 230),   # 浅蓝色
        "text_dark": (230, 250, 255),    # 近白色
        "overlay": (0, 50, 80, 150),     # 半透明深蓝色
        "tile_colors": {
            0: (20, 60, 85),       # 深蓝色
            2: (30, 90, 130),      # 深蓝
            4: (40, 110, 160),     # 海蓝
            8: (50, 140, 150),     # 青蓝
            16: (40, 150, 120),    # 海绿
            32: (50, 160, 100),    # 绿色
            64: (80, 170, 90),     # 黄绿
            128: (100, 100, 160),  # 浅紫蓝
            256: (110, 80, 170),   # 浅紫色
            512: (120, 60, 180),   # 紫色
            1024: (130, 50, 190),  # 深紫色
            2048: (140, 40, 200),  # 亮紫色
            4096: (150, 30, 190),  # 暗紫红
            8192: (160, 20, 180)   # 深紫
        },
        "gradient": True
    },
    "forest": {
        "name": "森林",
        "background": (30, 60, 35),      # 森林绿
        "empty_cell": (40, 70, 45),      # 深绿色
        "text_light": (190, 220, 200),   # 浅绿灰色
        "text_dark": (235, 250, 240),    # 近白色
        "overlay": (30, 60, 35, 150),    # 半透明森林绿
        "tile_colors": {
            0: (40, 70, 45),       # 深绿色
            2: (60, 100, 65),      # 中绿色
            4: (80, 120, 75),      # 浅绿色
            8: (100, 140, 70),     # 草绿色
            16: (120, 160, 60),    # 黄绿色
            32: (140, 180, 50),    # 亮黄绿
            64: (110, 130, 50),    # 橄榄绿
            128: (90, 110, 50),    # 暗橄榄绿
            256: (70, 90, 40),     # 深橄榄绿
            512: (120, 100, 60),   # 棕绿色
            1024: (140, 110, 70),  # 浅棕色
            2048: (160, 120, 80),  # 中棕色
            4096: (90, 70, 40),    # 深棕色
            8192: (70, 50, 30)     # 暗棕色
        },
        "texture": True
    },
    "candy": {
        "name": "糖果",
        "background": (255, 240, 245),   # 浅粉色
        "empty_cell": (250, 235, 240),   # 米白粉色
        "text_light": (150, 100, 120),   # 暗粉色
        "text_dark": (90, 60, 70),       # 深粉棕色
        "overlay": (255, 220, 230, 150), # 半透明粉色
        "tile_colors": {
            0: (250, 235, 240),    # 米白粉色
            2: (255, 200, 220),    # 浅粉色
            4: (255, 180, 210),    # 中粉色
            8: (255, 230, 150),    # 浅黄色
            16: (180, 230, 255),   # 浅蓝色
            32: (200, 255, 200),   # 浅绿色
            64: (255, 190, 170),   # 浅橙色
            128: (220, 170, 255),  # 浅紫色
            256: (255, 150, 180),  # 深粉色
            512: (150, 220, 255),  # 中蓝色
            1024: (255, 220, 120), # 浅橙黄色
            2048: (200, 255, 160), # 浅黄绿色
            4096: (255, 160, 140), # 浅红色
            8192: (190, 180, 255)  # 浅蓝紫色
        },
        "animation": "bounce"
    },
}

# 随机选择一个主题
CURRENT_THEME = random.choice(list(THEMES.keys()))

# 背景和空格子颜色直接使用主题中的定义
BACKGROUND_COLOR = THEMES[CURRENT_THEME]["background"]
EMPTY_CELL_COLOR = THEMES[CURRENT_THEME]["empty_cell"]

# 根据当前主题生成方块颜色映射
TILE_COLORS = THEMES[CURRENT_THEME]["tile_colors"]

# 生成文字颜色映射
TEXT_COLORS = {}
for value in TILE_COLORS.keys():
    # 对于较小的数值使用深色文字，较大数值使用浅色文字
    if value <= 4:
        TEXT_COLORS[value] = THEMES[CURRENT_THEME]["text_light"]
    else:
        TEXT_COLORS[value] = THEMES[CURRENT_THEME]["text_dark"]


# 功能函数

def get_path(file_name):
    """获取文件路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, file_name)


def load_highscores():
    """读取历史最高分"""
    try:
        records_path = get_path("records.json")
        if os.path.exists(records_path):
            with open(records_path, "r") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, dict) and "scores" in data and isinstance(data["scores"], list):
                        return sorted(data["scores"], reverse=True)
                except json.JSONDecodeError:
                    pass
        return [0]
    except Exception as e:
        print(f"读取分数记录时出错: {e}")
        return [0]
    

def save_score(score):
    """保存新的分数记录"""
    if score <= 0:
        return
        
    try:
        scores = load_highscores()
        scores.append(score)
        scores = sorted(scores, reverse=True)
        
        records_path = get_path("records.json")
        with open(records_path, "w") as f:
            json.dump({"scores": scores}, f, indent=4)

    except Exception as e:
        print(f"保存分数记录时出错: {e}")


def fast_copy_game(game):
    """轻量级游戏复制函数，避免完整深拷贝"""
    new_game = copy.copy(game)  # 浅拷贝对象
    new_game.grid = [row[:] for row in game.grid]  # 仅深拷贝网格数据
    return new_game