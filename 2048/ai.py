import copy
import random
from utils import *

class AI2048:
    """
    2048游戏的AI类定义 使用贪婪搜索策略
    """
    def __init__(self, game=None):
        # 继承一下当前的game就完事了 AI是接盘侠
        self.game = game
    
    def get_move(self) -> int:
        """使用有限深度的贪婪搜索确定最佳移动"""
        if not self.game:
            return None
        
        depth = 3   # 搜索深度 可以根据性能需求调整 不宜过大
        best_move, _ = self._look_ahead(self.game, depth)   # 最佳选择

        if best_move is None:
            best_move = random.randint(0, 3)    # 没有就摆烂！
        return best_move
    
    def _look_ahead(self, game, depth):
        """dfs递归搜索未来几步的最佳移动"""
        if depth == 0:
            return None, self._evaluate(game)
        
        best_score = -float('inf')
        best_move = None

        for direction in range(4):
            game_copy = copy.deepcopy(game)
            if game_copy.move(direction):
                if depth == 1: # 第一层直接使用当前评估
                    move_score = self._evaluate(game_copy)
                else:
                    # 模拟随机添加一个新方块
                    empty_cells_count = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if game_copy.grid[i][j] == 0]
                    if empty_cells_count:
                        # 考虑2和4这两种可能的新方块
                        scores = []
                        for value in (TWO, FOUR):
                            for cell in empty_cells_count[:min(3, len(empty_cells_count))]:  # 限制随机位置样本数量提高效率
                                game_sim = copy.deepcopy(game_copy)
                                game_sim.grid[cell[0]][cell[1]] = value
                                _, score = self._look_ahead(game_sim, depth - 1)
                                scores.append(score)
                        # 取平均值作为期望分数
                        move_score = sum(scores) / len(scores) if scores else 0
                    else:
                        move_score = self._evaluate(game_copy)
                if move_score > best_score:
                    best_score = move_score
                    best_move = direction
                    
        return best_move, best_score

    def _evaluate(self, game):
        """
        贪婪策略评估函数
        综合考虑多种策略因素，动态调整权重
        """
        grid = game.get_grid()
        total_score = game.get_score()
        max_tile = max(max(row) for row in grid)
        empty_cells = [(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if grid[i][j] == 0]
        empty_cells_count = len(empty_cells)
        
        # 空格数量权重
        empty_weight = 16 if max_tile < 128 else 32 if max_tile < 256 else 64 if max_tile < 512 else 128 # 后期空格更重要
        total_score += empty_cells_count * empty_weight

        # 空白格分布评分
        # BFS识别连通区域，奖励空格集中分布
        if empty_cells_count > 0:
            max_cluster = 0
            visited = set()
            for empty_cell in empty_cells:
                if empty_cell in visited:
                    continue
                cluster_size = 1  # 集群计数
                queue = [empty_cell]
                visited.add(empty_cell)
                while queue:
                    i, j = queue.pop(0)
                    for ni, nj in ((i-1,j), (i+1,j), (i,j-1), (i,j+1)):
                        if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE and grid[ni][nj] == 0 and (ni, nj) not in visited:
                            cluster_size += 1
                            queue.append((ni, nj))
                            visited.add((ni, nj)) 
                if cluster_size > max_cluster:
                    max_cluster = cluster_size # 更新最大集群大小
            total_score += max_cluster * max_tile / 4
        
        # 合并潜力与权重
        merge_potential = 0
        merge_weight = 1 if max_tile < 256 else 1.2 if max_tile < 1024 else 1.5
        # 水平方向合并潜力
        for i in range(4):
            for j in range(3):
                if grid[i][j] != 0:
                    # 直接相邻相同
                    if grid[i][j] == grid[i][j + 1]:
                        merge_potential += grid[i][j] * 2
        # 垂直方向合并潜力
        for j in range(4):
            for i in range(3):
                if grid[i][j] != 0:
                    # 直接相邻相同
                    if grid[i][j] == grid[i + 1][j]:
                        merge_potential += grid[i][j] * 2
        total_score += merge_potential * merge_weight
        
        # 多模板蛇形布局评分 下为多种潜在的最优路径模板
        snake_paths = [
            # 经典Z字形蛇形路径
            [
                (0, 0), (0, 1), (0, 2), (0, 3),
                (1, 3), (1, 2), (1, 1), (1, 0),
                (2, 0), (2, 1), (2, 2), (2, 3),
                (3, 3), (3, 2), (3, 1), (3, 0)
            ],
            # 反向Z字形路径
            [
                (0, 3), (0, 2), (0, 1), (0, 0),
                (1, 0), (1, 1), (1, 2), (1, 3),
                (2, 3), (2, 2), (2, 1), (2, 0),
                (3, 0), (3, 1), (3, 2), (3, 3)
            ],
            # 螺旋形路径
            [
                (0, 0), (0, 1), (0, 2), (0, 3),
                (1, 3), (2, 3), (3, 3), (3, 2),
                (3, 1), (3, 0), (2, 0), (1, 0),
                (1, 1), (1, 2), (2, 2), (2, 1)
            ]
        ]
        
        # 计算每个路径的得分，选择最好的那个
        best_snake_score = 0
        for the_path in snake_paths:
            for path in (the_path, the_path[::-1]): # 反转评价单调递增
                values = [grid[r][c] for r, c in path]
                path_score = 0
                
                # 计算单调递减得分
                monotonic = True
                for i in range(len(values) - 1):
                    if values[i] != 0:
                        if values[i] > values[i + 1]:
                            if values[i + 1] != 0:
                                path_score += values[i + 1]
                            else:
                                path_score += values[i] / 4
                        elif values[i] == values[i + 1]:
                            path_score += values[i]
                        else:
                            # 不是递减，则惩罚
                            path_score -= values[i]
                            monotonic = False
                
                # 如果保持全局单调性，给予额外奖励
                if monotonic and values[0] > 0:
                    path_score *= 1.5
                
                if path_score > best_snake_score:
                    best_snake_score = path_score 
        
        # 动态调整蛇形路径权重
        snake_weight = 1.8 if max_tile >= 512 else 1.2 # 后期单调性更重要
        total_score += best_snake_score * snake_weight
        
        # 角落策略评分
        corner_score = 0
        corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
        corner_values = [grid[i][j] for i, j in corners]
        
        # 最大值在角落加分
        if max_tile in corner_values:
            corner_idx = corner_values.index(max_tile)
            corner_pos = corners[corner_idx]
            corner_score += max_tile * 2
            
            # 在最大值周围构建递减序列
            if corner_pos == (0, 0):  # 左上角
                # 检查右侧和下方的数值梯度
                if grid[0][1] != 0 and grid[0][0] >= grid[0][1]:
                    corner_score += grid[0][1] * 0.8
                if grid[1][0] != 0 and grid[0][0] >= grid[1][0]:
                    corner_score += grid[1][0] * 0.8
            elif corner_pos == (0, 3):  # 右上角
                if grid[0][2] != 0 and grid[0][3] >= grid[0][2]:
                    corner_score += grid[0][2] * 0.8
                if grid[1][3] != 0 and grid[0][3] >= grid[1][3]:
                    corner_score += grid[1][3] * 0.8
            elif corner_pos == (3, 0):  # 左下角
                if grid[2][0] != 0 and grid[3][0] >= grid[2][0]:
                    corner_score += grid[2][0] * 0.8
                if grid[3][1] != 0 and grid[3][0] >= grid[3][1]:
                    corner_score += grid[3][1] * 0.8
            elif corner_pos == (3, 3):  # 右下角
                if grid[2][3] != 0 and grid[3][3] >= grid[2][3]:
                    corner_score += grid[2][3] * 0.8
                if grid[3][2] != 0 and grid[3][3] >= grid[3][2]:
                    corner_score += grid[3][2] * 0.8
        
        # 检查次大数在边缘
        second_max = 0
        for i in range(4):
            for j in range(4):
                if grid[i][j] < max_tile and grid[i][j] > second_max:
                    second_max = grid[i][j]
        
        # 边缘大值策略
        edge_positions = [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]
        for i, j in edge_positions:
            if grid[i][j] == second_max:
                corner_score += second_max * 0.5
        
        total_score += corner_score
        
        # 平滑度评分
        smoothness = 0
        
        for i in range(4):
            for j in range(4):
                if grid[i][j] != 0:
                    # 计算平滑度 - 相邻格子差值越小越好
                    if j < 3 and grid[i][j + 1] != 0:
                        diff = abs(grid[i][j] - grid[i][j + 1])
                        smoothness -= diff
                    
                    if i < 3 and grid[i + 1][j] != 0:
                        diff = abs(grid[i][j] - grid[i + 1][j])
                        smoothness -= diff
        
        # 动态调整平滑度权重
        smoothness_weight = 1.5 if max_tile <= 256 else 3 # 后期平滑度更重要
        total_score += smoothness * smoothness_weight
        
        # 危险格局惩罚
        danger_score = 0
        
        # 惩罚大数在中央的情形
        center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for i, j in center_positions:
            if grid[i][j] == max_tile:
                danger_score -= max_tile
            elif grid[i][j] == second_max:
                danger_score -= second_max * 0.5
        
        danger_weight = 1 if max_tile < 256 else 3 if max_tile < 2048 else 5
        total_score += danger_score * danger_weight
        
        # 游戏状态加成
        game_state = game.get_game_state()
        if game_state == 1:  # 游戏胜利
            total_score = float('inf')  # 成功了疯狂奖励
        elif game_state == 2:  # 游戏失败
            total_score = -float('inf')  # 失败了疯狂惩罚
        
        return total_score