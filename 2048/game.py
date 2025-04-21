import sys
import random
import pygame
from utils import *
from renderer import GameRenderer
from ai import AI2048


class Game2048:
    def __init__(self):
        '''初始化游戏'''
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_state = GAME_RUNNING
        self.high_score = max(load_highscores())
        self.new_record = False
        self.record_already_shown = False

        # 游戏胜利!!!
        self.win_time = 0      # 胜利时的时间戳
        self.win_shown = False  # 是否已经显示过胜利信息

        # 添加两个初始方块
        # 开局两个块，装备全靠抢
        self.add_new_tile()
        self.add_new_tile()
    
    
    def add_new_tile(self) -> bool:
        '''在随机空白位置添加一个新的方块(2或4)'''
        # 找出所有空白格子
        empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if self.grid[i][j] == 0]

        if empty_cells: # 如果有空白格子
            # 随机选择一个空白格子
            i, j = random.choice(empty_cells)
            # 生成2或4
            self.grid[i][j] = TWO if random.random() < RANDOM_P_TWO else FOUR
            return True
        return False
    
    # 一些工具方法
    def get_grid(self):
        '''返回当前网格'''
        return self.grid
    
    def get_score(self):
        '''返回当前分数'''
        return self.score
    
    def get_game_state(self):
        '''返回当前游戏状态'''
        return self.game_state
    
    def move(self, direction: int) -> bool:
        """
        关键函数，根据方向移动方块
        Args:
            direction (int): 方向: 0 = 上, 1 = 右, 2 = 下, 3 = 左
        Returns:
            bool: 网格是否有变化的bool值
        """
        # 备份当前网格
        memo_grid = [row[:] for row in self.grid]

        # 根据方向执行对应移动
        if direction == 0:
            self._move_up()
        elif direction == 1:
            self._move_right()
        elif direction == 2:
            self._move_down()
        elif direction == 3:
            self._move_left()
        
        # 检查网格是否发生变化
        changed = self.grid != memo_grid

        # 如果有变化，添加新方块并检查游戏状态
        if changed:
            self.add_new_tile()
            self._check_game_state()
        
        return changed
    
    def _move_left(self):
        '''向左移动方块'''
        for i in range(GRID_SIZE):
            # 移动并合并一行
            self._move_row_left(i)

    def _move_right(self):
        '''向右移动方块'''
        for i in range(GRID_SIZE):
            # 反转行，向左移动，再反转回来
            self.grid[i].reverse()
            self._move_row_left(i)
            self.grid[i].reverse()

    def _move_up(self):
        '''向上移动方块'''
        # 转置网格
        self.grid = [list(row) for row in zip(*self.grid)]
        # 向左移动每一行
        for i in range(GRID_SIZE):
            self._move_row_left(i)
        # 再次转置回原始方向
        self.grid = [list(row) for row in zip(*self.grid)]

    def _move_down(self):
        '''向下移动方块'''
        # 转置网格
        self.grid = [list(row) for row in zip(*self.grid)]
        # 向右移动每一行
        for i in range(GRID_SIZE):
            self.grid[i].reverse()
            self._move_row_left(i)
            self.grid[i].reverse()
        # 再次转置回原始方向
        self.grid = [list(row) for row in zip(*self.grid)]
    
    def _move_row_left(self, row_index: int):
        """
        将指定行向左移动并合并
        关键函数，所有移动的基础操作
        Args:
            row_index (int): 移动行的下标
        """
        # 获取当前行并过滤掉0
        row = [tile for tile in self.grid[row_index] if tile != 0]

        # 合并相同的相邻方块
        i = 0
        while i < len(row) - 1:
            if row[i] == row[i + 1]:
                row[i] *= 2
                self.score += row[i]  # 增加分数
                row.pop(i + 1)  # 移除被合并的方块
            i += 1
        
        # 恢复长度
        while len(row) < GRID_SIZE:
            row.append(0)
        
        # 更新网格的行
        self.grid[row_index] = row
    
    def _check_game_state(self):
        '''检查'''

        # 检查是否破纪录
        if self.score > self.high_score and not self.record_already_shown:
            self.high_score = self.score
            self.new_record = True
            self.record_already_shown = True
        elif self.score > self.high_score:
            self.high_score = self.score

        # 检查是否有2048方块
        for row in self.grid:
            if 2048 in row and not self.win_shown:
                self.game_state = GAME_WON
                self.win_time = pygame.time.get_ticks()
                self.win_shown = True
                return
        
        # 检查是否还有空格
        for row in self.grid:
            if 0 in row:
                return  # 还有空格，游戏继续
            
        # 没有空格了，检查是否有可合并的方块
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE - 1):
                if self.grid[i][j] == self.grid[i][j + 1]:
                    return  # 游戏继续
                
        for i in range(GRID_SIZE - 1):
            for j in range(GRID_SIZE):
                if self.grid[i][j] == self.grid[i + 1][j]:
                    return  # 游戏继续
        
        # 既没有空格也没有可合并的方块，凉了
        self.game_state = GAME_LOST

def run():
    """梦开始的地方"""

    # 初始化pygame
    pygame.init()

    # 创建游戏和渲染器实例
    game = Game2048()
    renderer = GameRenderer()

    # 设置游戏时钟
    clock = pygame.time.Clock()

    # AI移动延迟 (ms)
    ai_mode = False
    ai_delay = AI_DELAY
    last_ai_move_time = 0
    ai = None  # 初始化AI对象为None

    # 游戏主循环
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                # 只有在非AI模式下才响应方向键(玩家不能干扰AI决策)
                if not ai_mode and game.get_game_state() == GAME_RUNNING:
                    if event.key == pygame.K_UP:
                        game.move(0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1)
                    elif event.key == pygame.K_DOWN:
                        game.move(2)
                    elif event.key == pygame.K_LEFT:
                        game.move(3)

                if event.key == pygame.K_r:  # 按R重开
                    # 保存当前分数
                    save_score(game.get_score())
                    game = Game2048()
                    if ai_mode:
                        ai = AI2048(game)  # 重新初始化AI对象

                # A键切换AI/人类模式
                if event.key == pygame.K_a:
                    ai_mode = not ai_mode
                    if ai_mode:
                        ai = AI2048(game)  # 初始化AI对象
                    print(f"{'AI' if ai_mode else '人类'} 模式")

        # AI模式下的移动
        if ai_mode and game.get_game_state() == GAME_RUNNING and ai:
            # 限制AI移动频率
            if current_time - last_ai_move_time > ai_delay:
                try:
                    direction = ai.get_move()
                    game.move(direction)
                    last_ai_move_time = current_time
                except Exception as e:
                    print(f"服务器繁忙 请稍后再试 {e}")
                    # 如果AI崩溃，重置AI
                    ai = AI2048(game)

        if game.get_game_state() == GAME_WON and (current_time - game.win_time >= 2000):
            game.game_state = GAME_RUNNING  # 恢复运行，赢了继续玩

        # 渲染
        renderer.render(game)

        # 控制帧率
        clock.tick(60)
    
    # 保存记录并退出游戏
    save_score(game.get_score())
    pygame.quit()
    sys.exit()