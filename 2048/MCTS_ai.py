from utils import *
from Greedy_ai import Greedy_AI2048
import copy
import time
import random
import numpy as np

class MCTSNode:
    def __init__(self, game, parent=None, move=None):
        self.game = game
        self.parent = parent
        self.move = move
        self.children = {}
        self.visits = 0
        self.score = 0
        self.untried_moves = self._get_untried_moves()
    
    def _get_untried_moves(self):
        valid_moves = []
        for direction in range(4):
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                valid_moves.append(direction)
        return valid_moves
    
    def add_child(self, move):
        game_copy = copy.deepcopy(self.game)
        game_copy.move(move)
        child = MCTSNode(game_copy, self, move)
        self.untried_moves.remove(move)
        self.children[move] = child
        return child
    
    def update(self, score):
        self.visits += 1
        self.score += score
    
    def fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def best_child(self, exploration_weight=1.4):
        if not self.children:
            return None
            
        best_score = float('-inf')
        best_child = None
        
        for child in self.children.values():
            if child.visits == 0:
                return child
                
            exploit = child.score / child.visits
            explore = exploration_weight * np.sqrt(2 * np.log(self.visits) / child.visits)
            ucb = exploit + explore
            
            if ucb > best_score:
                best_score = ucb
                best_child = child
                
        return best_child


class MCTS_AI2048(Greedy_AI2048):
    def __init__(self, game=None, simulation_time=1.0):
        super().__init__(game)
        self.simulation_time = simulation_time
        self.stats = {"simulations": 0, "greedy_used": 0, "mcts_used": 0}
        self.node_cache = {}
    
    def get_move(self):
        if not self.game:
            return random.randint(0, 3)
        
        # 贪婪搜索基准
        depth = 3
        greedy_move, _ = self._look_ahead(self.game, depth)
        
        if greedy_move is None:
            for direction in range(4):
                game_copy = copy.deepcopy(self.game)
                if game_copy.move(direction):
                    greedy_move = direction
                    break
            
            if greedy_move is None:
                greedy_move = random.randint(0, 3)
        
        # MCTS搜索
        root = MCTSNode(self.game)
        
        if len(root.untried_moves) <= 1:
            self.stats["greedy_used"] += 1
            return greedy_move
        
        mcts_move = self._mcts_search(root)
        
        # 比较两种移动
        greedy_game = copy.deepcopy(self.game)
        greedy_game.move(greedy_move)
        greedy_score = self._enhanced_evaluate(greedy_game)
        
        mcts_game = copy.deepcopy(self.game)
        mcts_game.move(mcts_move)
        mcts_score = self._enhanced_evaluate(mcts_game)
        
        # 动态阈值：基于最大方块和空格数
        max_tile = max(max(row) for row in self.game.get_grid())
        empty_count = sum(row.count(0) for row in self.game.get_grid())
        
        if max_tile >= 512 and empty_count <= 5:
            threshold = 0.88  # 高分值紧张局面更信任MCTS
        elif max_tile >= 256:
            threshold = 0.93
        else:
            threshold = 0.97  # 早期更信任贪婪

        # 决策逻辑
        if mcts_score >= greedy_score * threshold:
            self.stats["mcts_used"] += 1
            return mcts_move
        else:
            self.stats["greedy_used"] += 1
            return greedy_move
    
    def _mcts_search(self, root):
        start_time = time.time()
        iteration = 0
        max_iterations = 1000
        
        while time.time() - start_time < self.simulation_time and iteration < max_iterations:
            node = self._select(root)
            
            if node.untried_moves and not self._is_terminal(node.game):
                node = self._expand(node)
            
            reward = self._simulate(node)
            
            self._backpropagate(node, reward)
            
            iteration += 1
        
        self.stats["simulations"] += iteration
        
        if not root.children:
            return random.choice(root.untried_moves) if root.untried_moves else 0
        
        best_move = None
        max_visits = -1
        
        # 使用访问次数而非UCB值来决定根节点的最佳移动
        for move, child in root.children.items():
            if child.visits > max_visits:
                max_visits = child.visits
                best_move = move
        
        return best_move
    
    def _select(self, node):
        current = node
        
        # 动态调整UCB探索权重
        max_tile = max(max(row) for row in current.game.get_grid())
        if max_tile >= 512:
            exploration_weight = 1.1  # 高分局面更注重利用
        elif max_tile >= 256:
            exploration_weight = 1.3
        else:
            exploration_weight = 1.5  # 早期更多探索
            
        while not self._is_terminal(current.game) and current.fully_expanded():
            child = current.best_child(exploration_weight=exploration_weight)
            if not child:
                break
            current = child
        
        return current
    
    def _expand(self, node):
        if not node.untried_moves:
            return node
        
        best_score = float('-inf')
        best_moves = []
        
        for move in node.untried_moves:
            game_copy = copy.deepcopy(node.game)
            if game_copy.move(move):
                score = self._enhanced_evaluate(game_copy)
                
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
        
        expand_move = random.choice(best_moves) if best_moves else random.choice(node.untried_moves)
        return node.add_child(expand_move)
    
    def _simulate(self, node):
        game = copy.deepcopy(node.game)
        
        # 保存初始状态
        initial_state = {
            'score': game.get_score(),
            'max_tile': max(max(row) for row in game.get_grid()),
            'empty_count': sum(row.count(0) for row in game.get_grid()),
            'eval': self._enhanced_evaluate(game)
        }
        
        # 动态调整模拟深度
        max_tile = initial_state['max_tile']
        if max_tile >= 512:
            depth = 12  # 高分状态增加深度
        elif max_tile >= 128:
            depth = 10  # 中等状态
        else:
            depth = 8   # 早期状态增加深度
        
        steps = 0
        
        while game.get_game_state() == 0 and steps < depth:
            valid_moves = []
            for direction in range(4):
                # 高效检测可移动性
                can_move = False
                grid = game.grid
                
                if direction == 0:  # 上
                    for j in range(4):
                        for i in range(1, 4):
                            if grid[i][j] != 0 and (grid[i-1][j] == 0 or grid[i-1][j] == grid[i][j]):
                                can_move = True
                                break
                        if can_move: break
                elif direction == 1:  # 右
                    for i in range(4):
                        for j in range(3):
                            if grid[i][j] != 0 and (grid[i][j+1] == 0 or grid[i][j+1] == grid[i][j]):
                                can_move = True
                                break
                        if can_move: break
                elif direction == 2:  # 下
                    for j in range(4):
                        for i in range(3):
                            if grid[i][j] != 0 and (grid[i+1][j] == 0 or grid[i+1][j] == grid[i][j]):
                                can_move = True
                                break
                        if can_move: break
                elif direction == 3:  # 左
                    for i in range(4):
                        for j in range(1, 4):
                            if grid[i][j] != 0 and (grid[i][j-1] == 0 or grid[i][j-1] == grid[i][j]):
                                can_move = True
                                break
                        if can_move: break
                
                # 只有确认可移动时才创建深拷贝
                if can_move:
                    game_copy = copy.deepcopy(game)
                    if game_copy.move(direction):
                        valid_moves.append(direction)
            
            if not valid_moves:
                break
            
            # 降低随机性，增加策略性
            if random.random() < 0.15:  # 从0.3降低到0.15
                best_move = random.choice(valid_moves)
            else:
                best_move = self._enhanced_evaluate_moves(game, valid_moves)
            
            game.move(best_move)
            
            # 添加随机方块
            empty_cells = [(i, j) for i in range(4) for j in range(4) if game.grid[i][j] == 0]
            if empty_cells:
                i, j = random.choice(empty_cells)
                game.grid[i][j] = 2 if random.random() < 0.9 else 4
            
            steps += 1
            
            # 提前终止检查 - 如果评估严重下降，提前结束模拟
            if steps >= 4 and self._enhanced_evaluate(game) < initial_state['eval'] * 0.75:
                break
        
        final_state = {
            'score': game.get_score(),
            'max_tile': max(max(row) for row in game.get_grid()),
            'empty_count': sum(row.count(0) for row in game.get_grid()),
            'eval': self._enhanced_evaluate(game)
        }
        
        # 计算复合奖励
        score_gain = (final_state['score'] - initial_state['score']) / 1000
        tile_gain = np.log2(final_state['max_tile'] / max(1, initial_state['max_tile']))
        empty_diff = final_state['empty_count'] - initial_state['empty_count']
        eval_diff = final_state['eval'] - initial_state['eval']
        
        reward = (
            0.5 * eval_diff +  # 提高评估函数权重
            0.25 * score_gain + 
            0.15 * tile_gain + 
            0.1 * empty_diff
        )
        
        # 游戏状态奖励
        if game.get_game_state() == 1:  # 胜利
            reward += 100
        elif game.get_game_state() == 2:  # 失败
            reward -= 30
        
        return reward
    
    def _enhanced_evaluate(self, game):
        """
        增强版评估函数，从贪婪AI中借鉴高效评估方法
        """
        grid = game.get_grid()
        score = 0
        
        # 空格评估
        empty_count = sum(row.count(0) for row in grid)
        score += empty_count * 10
        
        # 最大方块评估
        max_tile = max(max(row) for row in grid)
        
        # 最大方块位置评估
        corners = [(0,0), (0,3), (3,0), (3,3)]
        max_in_corner = False
        for i, j in corners:
            if grid[i][j] == max_tile:
                max_in_corner = True
                score += max_tile * 0.5  # 奖励最大方块在角落
                break
        
        # 单调性评估（保持方块沿一个方向递减）
        monotonicity = 0
        
        # 检查水平单调性
        for i in range(4):
            current_row = grid[i]
            if current_row[0] >= current_row[1] >= current_row[2] >= current_row[3]:
                monotonicity += 1
            if current_row[3] >= current_row[2] >= current_row[1] >= current_row[0]:
                monotonicity += 1
        
        # 检查垂直单调性
        for j in range(4):
            current_col = [grid[i][j] for i in range(4)]
            if current_col[0] >= current_col[1] >= current_col[2] >= current_col[3]:
                monotonicity += 1
            if current_col[3] >= current_col[2] >= current_col[1] >= current_col[0]:
                monotonicity += 1
        
        score += monotonicity * 20
        
        # 平滑度评估（相邻方块数值接近）
        smoothness = 0
        for i in range(4):
            for j in range(4):
                if grid[i][j] == 0:
                    continue
                
                val = np.log2(grid[i][j])
                for ni, nj in [(i+1, j), (i, j+1)]:
                    if 0 <= ni < 4 and 0 <= nj < 4 and grid[ni][nj] != 0:
                        n_val = np.log2(grid[ni][nj])
                        smoothness -= abs(val - n_val)
        
        score += smoothness * 5
        
        # 合并潜力评估
        merge_potential = 0
        for i in range(4):
            for j in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i][j+1]:
                    merge_potential += grid[i][j]
        for j in range(4):
            for i in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i+1][j]:
                    merge_potential += grid[i][j]
        
        score += merge_potential
        
        # 蛇形路径检查（理想的方块排列结构）
        snake_path = [
            (0,0), (0,1), (0,2), (0,3),
            (1,3), (1,2), (1,1), (1,0),
            (2,0), (2,1), (2,2), (2,3),
            (3,3), (3,2), (3,1), (3,0)
        ]
        
        values = []
        for i, j in snake_path:
            values.append(grid[i][j])
        
        is_snake = True
        for i in range(len(values) - 1):
            if values[i] < values[i+1] and values[i] != 0:
                is_snake = False
                break
        
        if is_snake:
            score += 50
        
        return score
    
    def _enhanced_evaluate_moves(self, game, valid_moves):
        """评估多个移动并选择最佳的"""
        best_score = float('-inf')
        best_move = random.choice(valid_moves)  # 默认值
        
        for move in valid_moves:
            game_copy = copy.deepcopy(game)
            game_copy.move(move)
            score = self._enhanced_evaluate(game_copy)
            
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def _backpropagate(self, node, reward):
        current = node
        
        while current:
            current.update(reward)
            current = current.parent
    
    def _is_terminal(self, game):
        return game.get_game_state() != 0
    
    def get_stats(self):
        return self.stats