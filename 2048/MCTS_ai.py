import copy
import time
import random
import numpy as np
from utils import *
from Greedy_ai import Greedy_AI2048

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
        """快速获取有效移动 - 减少深拷贝"""
        valid_moves = []
        for direction in range(4):
            # 使用浅拷贝替代深拷贝
            game_copy = self._fast_copy_game(self.game)
            if game_copy.move(direction):
                valid_moves.append(direction)
        return valid_moves
    
    def _fast_copy_game(self, game):
        """创建游戏的快速浅拷贝，仅用于检查移动有效性"""
        game_copy = copy.copy(game)  # 浅拷贝
        game_copy.grid = [row[:] for row in game.grid]  # 只深拷贝网格
        return game_copy

    def add_child(self, move):
        """添加子节点 - 优化拷贝"""
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

    def best_child(self, exploration_weight=1.0):
        """极简版UCB选择 - 避免不必要的NumPy转换"""
        if not self.children:
            return None
            
        # 手动计算UCB，避免小数据集上的NumPy开销
        best_score = float('-inf')
        best_child = None
        
        for child in self.children.values():
            # 标准UCB公式
            exploit = child.score / max(child.visits, 1)
            explore = exploration_weight * (2 * np.log(max(1, self.visits)) / max(1, child.visits))**0.5
            ucb = exploit + explore
            
            if ucb > best_score:
                best_score = ucb
                best_child = child
                
        return best_child


class MCTS_AI2048(Greedy_AI2048):
    """使用蒙特卡洛树搜索的2048AI (高性能版)"""
    def __init__(self, game=None, simulation_time=0.3):  # 默认搜索时间减少
        super().__init__(game)
        self.simulation_time = simulation_time
        # 使用字典而不是set作为缓存，更快的查找
        self.evaluation_cache = {}
        
    def get_move(self):
        if not self.game:
            return random.randint(0, 3)
        
        root = MCTSNode(self.game)
        
        # 快速路径
        if len(root.untried_moves) == 1:
            return root.untried_moves[0]
            
        # 急速评估，优先选择明显较好的移动
        if len(root.untried_moves) > 1:
            scores = []
            for move in root.untried_moves:
                game_copy = self._fast_copy_game(self.game)
                game_copy.move(move)
                scores.append(self._evaluate_cached(game_copy))
            
            best_idx = scores.index(max(scores))
            if scores[best_idx] > sum(scores)/len(scores) * 1.3:
                return root.untried_moves[best_idx]
        
        # 动态搜索时间
        adjusted_time = min(self.simulation_time, 0.1 + len(root.untried_moves)*0.05)
        
        # MCTS主循环
        start_time = time.time()
        while time.time() - start_time < adjusted_time:
            node = self._select(root)
            if node.untried_moves and not self._is_terminal(node.game):
                node = self._expand(node)
            reward = self._simulate_fast(node)  # 使用快速模拟
            self._backpropagate(node, reward)
        
        # 选择最佳移动 - 简化计算
        if not root.children:
            return random.choice(root.untried_moves) if root.untried_moves else random.randint(0, 3)
        
        best_move = None
        best_value = float('-inf')
        
        for move, child in root.children.items():
            # 更快的评分计算
            value = child.score / max(1, child.visits)
            if value > best_value:
                best_value = value
                best_move = move
        
        return best_move
    
    def _fast_copy_game(self, game):
        """创建游戏的快速浅拷贝，仅用于检查移动有效性"""
        game_copy = copy.copy(game)  # 浅拷贝
        game_copy.grid = [row[:] for row in game.grid]  # 只深拷贝网格
        return game_copy

    def _select(self, node):
        current_node = node
        while not self._is_terminal(current_node.game) and current_node.fully_expanded():
            child = current_node.best_child()
            if not child:
                return current_node
            current_node = child
        return current_node

    def _expand(self, node):
        if not node.untried_moves:
            return node
            
        # 快速扩展 - 减少评估次数
        if random.random() < 0.3 or len(node.untried_moves) <= 1:
            # 70%随机选择，提高速度
            best_move = random.choice(node.untried_moves)
        else:
            # 仅在30%情况下评估
            moves = node.untried_moves
            best_move = None
            best_score = float('-inf')
            
            for move in moves:
                game_copy = self._fast_copy_game(self.game)
                game_copy.move(move)
                score = self._evaluate_cached(game_copy)
                if score > best_score:
                    best_score = score
                    best_move = move
            
        return node.add_child(best_move)

    def _simulate_fast(self, node):
        """优化的快速模拟 - 减少模拟步数和评估次数"""
        game = self._fast_copy_game(node.game)
        initial_value = self._evaluate_cached(game)
        
        # 减少模拟步数
        max_steps = 12  # 从20减少到12
        steps = 0
        
        while game.get_game_state() == 0 and steps < max_steps:
            # 快速获取有效移动
            valid_moves = []
            
            for direction in range(4):
                temp_game = self._fast_copy_game(game)
                if temp_game.move(direction):
                    valid_moves.append(direction)
            
            if not valid_moves:
                break
                
            # 简化移动选择 - 90%随机移动
            if steps > 3 or random.random() < 0.9:
                move = random.choice(valid_moves)
            else:
                # 仅在前几步或10%情况下评估
                best_score = float('-inf')
                best_move = valid_moves[0]
                
                for move in valid_moves:
                    temp_game = self._fast_copy_game(game)
                    temp_game.move(move)
                    score = self._evaluate_cached(temp_game)
                    if score > best_score:
                        best_score = score
                        best_move = move
                        
                move = best_move
                
            game.move(move)
            steps += 1
        
        # 快速计算奖励
        final_value = self._evaluate_cached(game)
        reward = final_value - initial_value
        
        # 简化终局处理
        if game.get_game_state() == 2:
            reward *= 0.5
            
        return reward

    def _evaluate_cached(self, game):
        """优化的缓存评估"""
        # 简化缓存键 - 使用字符串而不是元组
        grid_str = str(game.get_grid())
        key = (grid_str, game.get_score())
        
        if key in self.evaluation_cache:
            return self.evaluation_cache[key]
        
        # 调用父类的评估函数
        result = super()._evaluate(game)
        
        # 只缓存近期结果
        if len(self.evaluation_cache) < 1000:  # 减小缓存大小
            self.evaluation_cache[key] = result
        
        return result

    def _backpropagate(self, node, reward):
        current = node
        while current:
            current.update(reward)
            current = current.parent

    def _is_terminal(self, game):
        return game.get_game_state() != 0