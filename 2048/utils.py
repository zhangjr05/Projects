import os
import json
import copy
import random
import gradio as gr

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
AI_DELAY = 0

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
        "background": (10, 25, 47),
        "empty_cell": (17, 34, 64),
        "text_light": (224, 234, 252),
        "text_dark": (224, 234, 252),
        "overlay": (35, 53, 84, 150),
        "tile_colors": {
            0: (17, 34, 64),
            2: (39, 70, 144),
            4: (87, 108, 188),
            8: (33, 230, 193),
            16: (39, 142, 165),
            32: (31, 66, 135),
            64: (7, 30, 61),
            128: (246, 201, 14),
            256: (255, 180, 0),
            512: (255, 99, 99),
            1024: (255, 24, 24),
            2048: (33, 230, 193),
            4096: (35, 53, 84),
            8192: (17, 34, 64)
        },
        "gradient": True
    },
    "forest": {
        "name": "森林",
        "background": (34, 49, 34),
        "empty_cell": (44, 62, 44),
        "text_light": (200, 230, 180),
        "text_dark": (245, 255, 235),
        "overlay": (44, 62, 44, 150),
        "tile_colors": {
            0: (44, 62, 44),
            2: (76, 110, 60),
            4: (96, 140, 80),
            8: (116, 170, 100),
            16: (136, 200, 120),
            32: (156, 220, 140),
            64: (176, 240, 160),
            128: (196, 220, 120),
            256: (176, 200, 80),
            512: (156, 170, 60),
            1024: (136, 140, 50),
            2048: (116, 110, 40),
            4096: (96, 80, 30),
            8192: (76, 60, 20)
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
    "coolrainbow": {
        "name": "炫彩",
        "background": (245, 245, 255),      # 亮色背景
        "empty_cell": (230, 230, 250),      # 亮淡紫
        "text_light": (60, 60, 60),
        "text_dark": (255, 255, 255),
        "overlay": (200, 200, 255, 120),
        "tile_colors": {
            0: (230, 230, 250),
            2: (255, 99, 132),
            4: (54, 162, 235),
            8: (255, 206, 86),
            16: (75, 192, 192),
            32: (153, 102, 255),
            64: (255, 159, 64),
            128: (255, 0, 255),
            256: (0, 255, 255),
            512: (0, 255, 127),
            1024: (255, 215, 0),
            2048: (0, 191, 255),
            4096: (255, 20, 147),
            8192: (0, 255, 0)
        },
        "glow": True
    },
}

deep_sea_theme = gr.themes.Base(
    primary_hue="blue",
    secondary_hue="blue",
    neutral_hue="slate",
    font=["Microsoft YaHei", "sans-serif"],
).set(
    body_background_fill="#0a192f",
    body_text_color="#e0eafc",
    block_background_fill="#112240",
    block_border_color="#233554",
    input_background_fill="#233554",
    input_border_color="#233554",
    button_primary_background_fill="#2563eb",
    button_primary_text_color="#e0eafc",
    button_secondary_background_fill="#233554",
    button_secondary_text_color="#e0eafc"
)

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