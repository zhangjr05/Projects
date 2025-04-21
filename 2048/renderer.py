import pygame
from utils import * 
from game import *

class GameRenderer:
    def __init__(self):
        '''初始化游戏渲染器'''
        # Pygame初始化字体
        pygame.font.init()

        # 设置个性化主题 ~~
        self.theme = THEMES[CURRENT_THEME]

        # 创建游戏窗口
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("2048 Game")

        # 加载并缓存字体
        self._init_fonts()
        # 预渲染固定文本
        self._init_text_surfaces()

        # 破纪录通知状态
        self.record_time = 0
        self.show_record = False

    def _init_fonts(self):
        '''初始化所需字体'''
        self.fonts = {
            'normal': pygame.font.SysFont('Arial', 30, bold=True),
            'big': pygame.font.SysFont('Arial', 40, bold=True),
            'small': pygame.font.SysFont('Arial', 20),
            'tiny': pygame.font.SysFont('Arial', 18)
        }

    def _init_text_surfaces(self):
        '''预渲染固定文本'''
        self.text_surfaces = {
            'win': self.fonts['big'].render("You Win!", True, (119, 110, 101)),
            'game_over': self.fonts['big'].render("Game Over!", True, (119, 110, 101)),
            'restart': self.fonts['small'].render("Press 'R' to Restart", True, (119, 110, 101)),
            'new_record': self.fonts['big'].render("NEW RECORD!", True, (249, 246, 242))
        }
        
    def render(self, game):
        '''
        class GameRenderer 的关键函数
        用于渲染游戏画面 实现可视化
        '''
        # 清空屏幕 (把背景铺好)
        self.screen.fill(self.theme["background"])

        # 绘制网格和方块
        self._draw_grid(game.get_grid())

        # 绘制分数
        self._draw_score(game.get_score(), game.high_score)

        # 处理破纪录通知 (记录都是AI破的...)
        self._handle_record_notification(game)
        
        # 绘制游戏状态
        game_state = game.get_game_state()
        if game_state != 0:  # 游戏不在运行状态
            self._draw_game_state(game_state)
        
        # 刷新屏幕 (不刷新你看什么O.o)
        pygame.display.flip()

    def _handle_record_notification(self, game):
        '''处理破纪录通知的显示'''
        current_time = pygame.time.get_ticks()
        
        # 检查是否破纪录并显示通知 
        if game.new_record and not self.show_record:
            self.show_record = True
            self.record_time = current_time
            game.new_record = False  # 重置标志
        
        # 如果正在显示破纪录通知且未超过1秒
        if self.show_record and current_time - self.record_time < 1000:
            self._draw_new_record()
        elif self.show_record:
            self.show_record = False  # 超过1秒后停止显示 (总不能一直挡着吧)

    def _draw_grid(self, grid: list[list[int]]):
        '''绘制游戏网格和方块'''
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                # 计算格子位置
                x = j * CELL_SIZE + (j + 1) * PADDING
                y = i * CELL_SIZE + (i + 1) * PADDING + SCORE_AREA # SCORE_AREA区域用来显示分数
                value = grid[i][j]

                # 设置格子颜色
                color = self.theme["tile_colors"].get(value, (0, 0, 0))

                # 绘制格子
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE), 0, 5)

                # 如果格子有值，绘制文字
                if value != 0:
                    self._draw_tile_text(value, x, y)
    
    def _draw_tile_text(self, value, x, y):
        '''绘制方块上的数字'''
        text_color = self.theme["text_dark"] if value >= 8 else self.theme["text_light"]
        
        # 为不同大小的数字选择合适的字体
        if value < 100:
            font = self.fonts['normal']
        elif value < 1000:
            font = self.fonts['small']
        else:
            font = self.fonts['tiny']
            
        text_surface = font.render(str(value), True, text_color)
        text_rect = text_surface.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
        self.screen.blit(text_surface, text_rect)

    def _draw_score(self, score, high_score):
        """绘制分数和最高分"""
        score_text = self.fonts['normal'].render(f"Score: {score}", True, (119, 110, 101))
        self.screen.blit(score_text, (10, 10))
        
        high_score_text = self.fonts['normal'].render(f"Best: {high_score}", True, (119, 110, 101))
        self.screen.blit(high_score_text, (WINDOW_WIDTH - high_score_text.get_width() - 10, 10))

    def _draw_game_state(self, state):
        '''绘制游戏状态消息'''
        # 创建半透明覆盖层
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

        if state == GAME_WON:
            overlay.fill((255, 255, 255, 180))
        else:
            overlay.fill((255, 255, 255, 150))
            
        self.screen.blit(overlay, (0, 0))
        
        # 选择并显示游戏状态消息
        if state == GAME_WON:
            message_surface = self.fonts['big'].render("You Win!", True, (20, 20, 140))
        else:
            message_surface = self.text_surfaces['game_over']
            
        message_rect = message_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        self.screen.blit(message_surface, message_rect)

    def _draw_new_record(self):
        """显示破纪录通知"""
        overlay = pygame.Surface((WINDOW_WIDTH, 60), pygame.SRCALPHA)
        overlay.fill((220, 20, 60, 230))
        self.screen.blit(overlay, (0, WINDOW_HEIGHT // 2 - 30))
        
        record_text = self.fonts['big'].render("NEW RECORD!", True, (255, 255, 0))
        text_rect = record_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        
        glow_text = self.fonts['big'].render("NEW RECORD!", True, (255, 255, 255))
        glow_rect = glow_text.get_rect(center=(WINDOW_WIDTH // 2 + 2, WINDOW_HEIGHT // 2 + 2))
        self.screen.blit(glow_text, glow_rect)

        self.screen.blit(record_text, text_rect)