import numpy as np
import copy
import pickle
import random
import os
from tqdm import tqdm
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from Greedy_ai import Greedy_AI2048
from utils import *

class DT_AI2048(Greedy_AI2048):
    """
    使用决策树分类预测当前状态能否达到2048的AI。
    只用决策树，不引入集成、剪枝等更高级方法。
    """

    def __init__(self, game=None, model_path=None):
        super().__init__(game)
        self.model = None  # 决策树模型
        self.scaler = None  # 特征标准化器
        self.model_path = model_path if model_path else get_path("models/dt_model.pkl")
        self._load_or_create_model()
        # 统计信息
        self.stats = {
            "predictions": 0,
            "high_prob_moves": 0,
            "low_prob_moves": 0,
            "total_moves": 0,
            "cache_hits": 0
        }
        self.pred_cache = {}  # 概率预测缓存
        self.max_cache_size = 10000

    def _load_or_create_model(self):
        """加载已有模型或新建决策树模型"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.scaler = model_data['scaler']
            print("成功加载2048决策树模型")
        except (FileNotFoundError, EOFError):
            print("未找到决策树模型文件，创建新的决策树分类器")
            self.model = DecisionTreeClassifier(
                max_depth=10,  # 适当加深树深度
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            self.scaler = StandardScaler()

    def _save_model(self):
        """保存模型"""
        model_dir = os.path.dirname(self.model_path)
        os.makedirs(model_dir, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        print(f"决策树模型已保存至 {self.model_path}")

    def _extract_features(self, game):
        """
        从游戏状态提取丰富的特征向量。
        参考greedy_ai的评估思想，加入棋盘结构、单调性、平滑度等。
        """
        grid = np.array(game.get_grid())
        flat_grid = grid.flatten()
        max_tile = np.max(flat_grid)
        empty_count = np.sum(flat_grid == 0)
        score = game.get_score()
        greedy_score = self._evaluate(game)  # 父类贪婪评估

        # 可合并的相邻块数
        merge_potential = 0
        for i in range(4):
            for j in range(3):
                if grid[i, j] != 0 and grid[i, j] == grid[i, j+1]:
                    merge_potential += 1
        for j in range(4):
            for i in range(3):
                if grid[i, j] != 0 and grid[i, j] == grid[i+1, j]:
                    merge_potential += 1

        # 最大块是否在角落
        max_in_corner = int(any(grid[i, j] == max_tile for i, j in [(0,0), (0,3), (3,0), (3,3)]))

        # 行列最大值
        row_max = np.max(grid, axis=1) / 2048.0
        col_max = np.max(grid, axis=0) / 2048.0

        # 行列单调性（递减性）
        row_mono = [int(np.all(np.diff(row) <= 0)) for row in grid]
        col_mono = [int(np.all(np.diff(col) <= 0)) for col in grid.T]

        # 平滑度（相邻格子差值和，越小越平滑）
        smoothness = 0
        for i in range(4):
            for j in range(4):
                if grid[i, j] != 0:
                    if j < 3 and grid[i, j+1] != 0:
                        smoothness -= abs(grid[i, j] - grid[i, j+1])
                    if i < 3 and grid[i+1, j] != 0:
                        smoothness -= abs(grid[i, j] - grid[i+1, j])
        smoothness = smoothness / 10000.0

        # 角落最大块的分布
        corners = [grid[0,0], grid[0,3], grid[3,0], grid[3,3]]
        corner_max = max(corners) / 2048.0

        # 各种数值块的分布
        tile_counts = [np.sum(flat_grid == v) / 16.0 for v in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]]

        # 组合所有特征
        features = [
            greedy_score / 100.0,
            max_tile / 2048.0,
            empty_count / 16.0,
            score / 20000.0,
            merge_potential / 24.0,
            max_in_corner,
            smoothness,
            corner_max
        ] + list(row_max) + list(col_max) + row_mono + col_mono + tile_counts
        return np.array(features).reshape(1, -1)

    def _heuristic_prob(self, game):
        """未训练模型时的启发式概率估计"""
        grid = game.get_grid()
        max_tile = max(max(row) for row in grid)
        empty_count = sum(row.count(0) for row in grid)
        if max_tile >= 1024:
            base_prob = 0.95
        elif max_tile >= 512:
            base_prob = 0.7
        elif max_tile >= 256:
            base_prob = 0.4
        elif max_tile >= 128:
            base_prob = 0.2
        else:
            base_prob = 0.1
        eval_score = self._evaluate(game)
        norm_eval = min(1.0, max(0.0, eval_score / 100.0))
        prob = 0.7 * base_prob + 0.3 * norm_eval
        if empty_count <= 2:
            prob *= 0.7
        return max(0.0, min(1.0, prob))

    def predict_probability(self, game):
        """预测当前状态达到2048的概率（带缓存）"""
        grid_tuple = tuple(tuple(row) for row in game.get_grid())
        if grid_tuple in self.pred_cache:
            self.stats["cache_hits"] += 1
            return self.pred_cache[grid_tuple]
        grid = game.get_grid()
        max_tile = max(max(row) for row in grid)
        if max_tile >= 1024:
            prob = 0.95
            self.pred_cache[grid_tuple] = prob
            return prob
        features = self._extract_features(game)
        if not hasattr(self.model, 'classes_'):
            prob = self._heuristic_prob(game)
            self.pred_cache[grid_tuple] = prob
            return prob
        try:
            self.stats["predictions"] += 1
            if self.scaler is not None:
                features = self.scaler.transform(features)
            prob = self.model.predict_proba(features)[0][1]
            # 控制缓存大小
            if len(self.pred_cache) >= self.max_cache_size:
                keys_to_remove = list(self.pred_cache.keys())[:int(len(self.pred_cache)*0.2)]
                for key in keys_to_remove:
                    del self.pred_cache[key]
            self.pred_cache[grid_tuple] = float(prob)
            return float(prob)
        except:
            prob = self._heuristic_prob(game)
            self.pred_cache[grid_tuple] = prob
            return prob

    def get_move(self):
        """
        一步前瞻：对每个方向模拟一步后评估概率，选最优。
        概率和贪婪分数加权，提升决策鲁棒性。
        """
        if not self.game:
            return None
        self.stats["total_moves"] += 1
        best_move = None
        best_score = -float('inf')
        for direction in range(4):
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                prob = self.predict_probability(game_copy)
                greedy_score = self._evaluate(game_copy)
                score = prob * 0.7 + (greedy_score / 100.0) * 0.3
                if score > best_score:
                    best_score = score
                    best_move = direction
        # 如果没有有效移动，随机选一个
        if best_move is None:
            valid_moves = []
            for direction in range(4):
                game_copy = copy.deepcopy(self.game)
                if game_copy.move(direction):
                    valid_moves.append(direction)
            if valid_moves:
                best_move = random.choice(valid_moves)
            else:
                best_move = random.randint(0, 3)
        # 统计高低概率移动
        if best_score > 0.7:
            self.stats["high_prob_moves"] += 1
        else:
            self.stats["low_prob_moves"] += 1
        return best_move

    def collect_training_data(self, num_games=100, max_moves=2000):
        """
        自动模拟游戏收集训练数据，增加多样性。
        前20%局用贪婪，20%-40%用半随机，40%-100%用随机。
        """
        from game import Game2048
        X = []
        y = []
        for i in tqdm(range(num_games), desc="收集决策树训练数据"):
            game = Game2048()
            game_states = []
            move_count = 0
            if i < num_games * 0.2:
                strategy = "greedy"
            elif i < num_games * 0.4:
                strategy = "semi_random"
            else:
                strategy = "random"
            with tqdm(total=max_moves, desc=f"游戏 {i+1}/{num_games}", leave=False) as pbar:
                while game.get_game_state() == 0 and move_count < max_moves:
                    game_states.append(copy.deepcopy(game))
                    if strategy == "greedy":
                        ai = Greedy_AI2048(game)
                        move = ai.get_move()
                    elif strategy == "semi_random":
                        if random.random() < 0.5:
                            ai = Greedy_AI2048(game)
                            move = ai.get_move()
                        else:
                            valid_moves = []
                            for direction in range(4):
                                game_copy = copy.deepcopy(game)
                                if game_copy.move(direction):
                                    valid_moves.append(direction)
                            move = random.choice(valid_moves) if valid_moves else random.randint(0, 3)
                    else:  # 完全随机
                        valid_moves = []
                        for direction in range(4):
                            game_copy = copy.deepcopy(game)
                            if game_copy.move(direction):
                                valid_moves.append(direction)
                        move = random.choice(valid_moves) if valid_moves else random.randint(0, 3)
                    game.move(move)
                    move_count += 1
                    pbar.update(1)
            final_max_tile = max(max(row) for row in game.get_grid())
            reached_2048 = final_max_tile >= 2048
            for state in game_states:
                features = self._extract_features(state)
                X.append(features[0])
                y.append(1 if reached_2048 else 0)
        return np.array(X), np.array(y)

    def train_model(self, X=None, y=None, num_games=100):
        """训练决策树模型，自动平衡样本"""
        if X is None or y is None:
            print("收集决策树训练数据...")
            X, y = self.collect_training_data(num_games=num_games)
        if len(X) == 0:
            print("没有收集到训练数据")
            return False
        print(f"开始训练决策树模型，使用 {len(X)} 个样本")
        self.pred_cache = {}
        # 简单的数据平衡
        success_rate = sum(y) / len(y)
        print(f"原始样本成功率: {success_rate:.2%}")
        if success_rate < 0.1 or success_rate > 0.9:
            print("数据不平衡，进行采样平衡...")
            pos_indices = np.where(y == 1)[0]
            neg_indices = np.where(y == 0)[0]
            min_samples = min(len(pos_indices), len(neg_indices))
            min_samples = max(100, min_samples)
            if len(pos_indices) > min_samples and len(neg_indices) > min_samples:
                if len(pos_indices) > len(neg_indices):
                    pos_indices = np.random.choice(pos_indices, len(neg_indices), replace=False)
                else:
                    neg_indices = np.random.choice(neg_indices, len(pos_indices), replace=False)
                balanced_indices = np.concatenate([pos_indices, neg_indices])
                X = X[balanced_indices]
                y = y[balanced_indices]
                print(f"平衡后样本数: {len(X)}, 成功率: {sum(y)/len(y):.2%}")
        print("特征标准化...")
        self.scaler = StandardScaler().fit(X)
        X_scaled = self.scaler.transform(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        print("训练决策树分类器...")
        self.model.fit(X_train, y_train)
        train_accuracy = self.model.score(X_train, y_train)
        test_accuracy = self.model.score(X_test, y_test)
        print(f"训练集准确率: {train_accuracy:.4f}")
        print(f"测试集准确率: {test_accuracy:.4f}")
        # 输出特征重要性
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            print("\n决策树特征重要性:")
            for i, imp in enumerate(importances):
                print(f"特征 {i}: {imp:.4f}")
        print("保存决策树模型...")
        self._save_model()
        return True

    def get_stats(self):
        """返回统计信息"""
        return self.stats

if __name__ == "__main__":
    from game import Game2048
    ai = DT_AI2048()
    ai.train_model(num_games=50)
    print("\n测试决策树AI在游戏中的表现...")
    game = Game2048()
    ai.game = game
    moves = 0
    while game.get_game_state() == 0 and moves < 1000:
        move = ai.get_move()
        game.move(move)
        moves += 1
        if moves % 50 == 0:
            max_tile = max(max(row) for row in game.get_grid())
            print(f"移动次数: {moves}, 最大块: {max_tile}")
    max_tile = max(max(row) for row in game.get_grid())
    print(f"\n游戏结束: 移动次数={moves}, 最大块={max_tile}")
    print(f"决策树AI统计信息: {ai.get_stats()}")