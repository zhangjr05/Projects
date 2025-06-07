import os
import time
import json
import numpy as np
import matplotlib.pyplot as plt
from game import Game2048
from Greedy_ai import Greedy_AI2048
from MCTS_ai import MCTS_AI2048
from ML_ai import ML_Enhanced_AI2048
from utils import get_path
from tqdm import tqdm

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False


def test_ai_performance(ai_class=Greedy_AI2048, ai_name="Greedy", num_games=10, max_moves=10000, **kwargs):
    """测试AI性能并返回结果"""
    scores = []
    max_tiles = []
    moves_count = []
    game_durations = []

    # 添加进度条
    for i in tqdm(range(num_games), desc=f"测试 {ai_name} AI"):
        game = Game2048()
        ai = ai_class(game, **kwargs)
        
        move_count = 0
        start_time = time.time()

        # 内层游戏进度条
        with tqdm(total=max_moves, desc=f"游戏 {i+1}", leave=False) as pbar:
            while game.get_game_state() == 0 and move_count < max_moves:
                move = ai.get_move()
                game.move(move)
                move_count += 1
                pbar.update(1)
                
                # 每100步更新一次显示信息
                if move_count % 100 == 0:
                    max_tile = max(max(row) for row in game.get_grid())
                    pbar.set_description(f"游戏 {i+1} - 分数: {game.get_score()}, 最大值: {max_tile}")
        
        end_time = time.time()

        # 记录结果
        scores.append(game.get_score())
        max_tiles.append(max(max(row) for row in game.get_grid()))
        moves_count.append(move_count)
        game_durations.append(end_time - start_time)
        
        # 使用tqdm.write避免干扰进度条显示
        tqdm.write(f"游戏 {i+1} 完成: 分数={game.get_score()}, 最大数={max(max(row) for row in game.get_grid())}")

    stats = {
        "average_score": float(np.mean(scores)),
        "highest_score": int(np.max(scores)),
        "average_max_tile": float(np.mean(max_tiles)),
        "highest_max_tile": int(np.max(max_tiles)),
        "average_moves": float(np.mean(moves_count)),
        "success_rate_2048": float(sum(1 for max_tile in max_tiles if max_tile >= 2048) / num_games * 100),
        "average_time_to_2048": float(np.mean([game_durations[i] for i in range(num_games) if max_tiles[i] >= 2048])) if any(max_tile >= 2048 for max_tile in max_tiles) else 0,
    }

    results = {
        "ai_name": ai_name,
        "scores": scores,
        "max_tiles": max_tiles,
        "moves_count": moves_count,
        "game_durations": game_durations,
        "stats": stats,
        "test_params": {
            "num_games": num_games,
            "max_moves": max_moves,
            **kwargs
        }
    }

    # 打印统计信息
    print(f"\n===== {ai_name} AI 测试结果 =====")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return results


def test_greedy_ai(num_games=100, max_moves=2000, save_path=None):
    """测试贪婪AI并可选保存结果"""
    print("\n开始测试贪婪AI...")
    greedy_results = test_ai_performance(
        ai_class=Greedy_AI2048, 
        ai_name="Greedy",
        num_games=num_games, 
        max_moves=max_moves
    )
    
    # 如果提供保存路径，则保存结果
    if save_path:
        with open(save_path, 'w') as f:
            json.dump(greedy_results, f, indent=4)
        print(f"贪婪AI测试结果已保存到 {save_path}")
    
    return greedy_results


def test_mcts_ai(num_games=100, max_moves=2000, simulation_time=3.0, save_path=None):
    """测试MCTS AI并可选保存结果"""
    print("\n开始测试MCTS AI...")
    mcts_results = test_ai_performance(
        ai_class=MCTS_AI2048, 
        ai_name="MCTS",
        num_games=num_games,
        max_moves=max_moves,
        simulation_time=simulation_time
    )
    
    # 如果提供保存路径，则保存结果
    if save_path:
        with open(save_path, 'w') as f:
            json.dump(mcts_results, f, indent=4)
        print(f"MCTS AI测试结果已保存到 {save_path}")
    
    return mcts_results


def test_ml_ai(num_games=100, max_moves=2000, save_path=None):
    """测试ML增强AI并可选保存结果"""
    print("\n开始测试ML增强AI...")
    
    # 实例化ML增强AI并训练模型
    dummy_game = Game2048()
    ml_ai = ML_Enhanced_AI2048(dummy_game)
    
    # 如果模型未训练，先训练模型
    if not hasattr(ml_ai.model, 'classes_'):
        print("训练ML模型中...")
        # 使用较小的参数进行快速训练
        ml_ai.train_model(num_games=10, max_moves=500)
    
    ml_results = test_ai_performance(
        ai_class=ML_Enhanced_AI2048,
        ai_name="ML-Enhanced",
        num_games=num_games,
        max_moves=max_moves
    )
    
    # 如果提供保存路径，则保存结果
    if save_path:
        with open(save_path, 'w') as f:
            json.dump(ml_results, f, indent=4)
        print(f"ML增强AI测试结果已保存到 {save_path}")
    
    return ml_results


def visualize_results(results, show=True):
    """可视化单个AI的测试结果"""
    ai_name = results.get("ai_name", "Unknown")
    
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 2, 1)
    plt.hist(results["scores"], bins=10)
    plt.title(f"{ai_name} - 分数分布")
    plt.xlabel("分数")
    plt.ylabel("频率")
    max_score = max(results["scores"]) if results["scores"] else 1000
    plt.xlim(0, max(10000, max_score * 1.2))

    plt.subplot(2, 2, 2)
    plt.hist(results["max_tiles"], bins=[2**i for i in range(1, 13)])
    plt.title(f"{ai_name} - 最大方块分布")
    plt.xlabel("方块值")
    plt.ylabel("频率")
    plt.xscale("log", base=2)

    plt.subplot(2, 2, 3)
    plt.hist(results["moves_count"], bins=10)
    plt.title(f"{ai_name} - 移动次数分布")
    plt.xlabel("移动次数")
    plt.ylabel("频率")
    
    plt.subplot(2, 2, 4)
    plt.hist(results["game_durations"], bins=10)
    plt.title(f"{ai_name} - 游戏时长分布")
    plt.xlabel("时长 (秒)")
    plt.ylabel("频率")

    plt.tight_layout()
    
    # 保存图表
    results_dir = os.path.join(os.path.dirname(get_path()), "results")
    os.makedirs(results_dir, exist_ok=True)
    plt.savefig(os.path.join(results_dir, f"{ai_name}_results.png"))
    
    if show:
        plt.show()
    
    return plt


def compare_ai_results(greedy_results=None, mcts_results=None, ml_results=None, 
                      greedy_path=None, mcts_path=None, ml_path=None, 
                      save_path=None, show=True):
    """比较不同AI的结果"""
    # 如果提供了文件路径，从文件加载结果
    if greedy_path and not greedy_results:
        try:
            with open(greedy_path, 'r') as f:
                greedy_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"无法加载贪婪AI结果: {greedy_path}")
    
    if mcts_path and not mcts_results:
        try:
            with open(mcts_path, 'r') as f:
                mcts_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"无法加载MCTS AI结果: {mcts_path}")
            
    if ml_path and not ml_results:
        try:
            with open(ml_path, 'r') as f:
                ml_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"无法加载ML AI结果: {ml_path}")
    
    # 确定要比较的AI类型
    ai_names = []
    avg_scores = []
    avg_max_tiles = []
    avg_moves = []
    success_rates = []
    
    if greedy_results:
        ai_names.append("贪婪")
        avg_scores.append(greedy_results["stats"]["average_score"])
        avg_max_tiles.append(greedy_results["stats"]["average_max_tile"])
        avg_moves.append(greedy_results["stats"]["average_moves"])
        success_rates.append(greedy_results["stats"]["success_rate_2048"])
    
    if mcts_results:
        ai_names.append("MCTS")
        avg_scores.append(mcts_results["stats"]["average_score"])
        avg_max_tiles.append(mcts_results["stats"]["average_max_tile"])
        avg_moves.append(mcts_results["stats"]["average_moves"])
        success_rates.append(mcts_results["stats"]["success_rate_2048"])
        
    if ml_results:
        ai_names.append("ML增强")
        avg_scores.append(ml_results["stats"]["average_score"])
        avg_max_tiles.append(ml_results["stats"]["average_max_tile"])
        avg_moves.append(ml_results["stats"]["average_moves"])
        success_rates.append(ml_results["stats"]["success_rate_2048"])
    
    # 创建比较图表
    plt.figure(figsize=(15, 10))
    
    # 比较平均分数
    plt.subplot(2, 2, 1)
    bars = plt.bar(ai_names, avg_scores, color=['skyblue', 'lightgreen', 'coral'][:len(ai_names)])
    plt.title("平均分数对比")
    plt.ylabel("分数")
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    # 比较平均最大方块
    plt.subplot(2, 2, 2)
    bars = plt.bar(ai_names, avg_max_tiles, color=['skyblue', 'lightgreen', 'coral'][:len(ai_names)])
    plt.title("平均最大方块对比")
    plt.ylabel("方块值")
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    # 比较平均移动次数
    plt.subplot(2, 2, 3)
    bars = plt.bar(ai_names, avg_moves, color=['skyblue', 'lightgreen', 'coral'][:len(ai_names)])
    plt.title("平均移动次数对比")
    plt.ylabel("移动次数")
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', va='bottom')
    
    # 比较2048成功率
    plt.subplot(2, 2, 4)
    bars = plt.bar(ai_names, success_rates, color=['skyblue', 'lightgreen', 'coral'][:len(ai_names)])
    plt.title("2048达成率对比 (%)")
    plt.ylabel("达成率 (%)")
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # 打印比较表格
    print("\n===== AI性能对比 =====")
    print(f"{'AI类型':<10} {'平均分数':<12} {'达成率 (%)':<12} {'平均最大方块':<12}")
    print("-" * 60)
    
    for i, name in enumerate(ai_names):
        print(f"{name:<10} {avg_scores[i]:<12.1f} {success_rates[i]:<12.1f} {avg_max_tiles[i]:<12.1f}")
    
    # 如果提供保存路径，保存比较数据
    if save_path:
        comparison_data = {
            "ai_types": ai_names,
            "comparison": {}
        }
        
        if greedy_results:
            comparison_data["comparison"]["greedy"] = {
                "average_score": greedy_results["stats"]["average_score"],
                "highest_score": greedy_results["stats"]["highest_score"],
                "average_max_tile": greedy_results["stats"]["average_max_tile"],
                "highest_max_tile": greedy_results["stats"]["highest_max_tile"],
                "success_rate_2048": greedy_results["stats"]["success_rate_2048"]
            }
        
        if mcts_results:
            comparison_data["comparison"]["mcts"] = {
                "average_score": mcts_results["stats"]["average_score"],
                "highest_score": mcts_results["stats"]["highest_score"],
                "average_max_tile": mcts_results["stats"]["average_max_tile"],
                "highest_max_tile": mcts_results["stats"]["highest_max_tile"],
                "success_rate_2048": mcts_results["stats"]["success_rate_2048"]
            }
            
        if ml_results:
            comparison_data["comparison"]["ml_enhanced"] = {
                "average_score": ml_results["stats"]["average_score"],
                "highest_score": ml_results["stats"]["highest_score"],
                "average_max_tile": ml_results["stats"]["average_max_tile"],
                "highest_max_tile": ml_results["stats"]["highest_max_tile"],
                "success_rate_2048": ml_results["stats"]["success_rate_2048"]
            }
        
        with open(save_path, 'w') as f:
            json.dump(comparison_data, f, indent=4)
        print(f"比较数据已保存到 {save_path}")
    
    # 保存图表
    plt.savefig(get_path(r"results\ai_comparison.png"))
    
    if show:
        plt.show()
    
    return plt


if __name__ == "__main__":
    num_games = 10
    max_moves = 2000
    
    
    # 测试所有AI类型

    # greedy_results = test_greedy_ai(
    #     num_games=num_games, 
    #     max_moves=max_moves, 
    #     save_path=get_path("results/greedy_results.json")
    # )
    
    # mcts_results = test_mcts_ai(
    #     num_games=num_games, 
    #     max_moves=max_moves, 
    #     save_path=get_path("results/mcts_results.json")
    # )

    # ml_results = test_ml_ai(
    #     num_games=num_games,
    #     max_moves=max_moves,
    #     save_path=get_path("results/ml_results.json")
    # )
    

    # 比较所有AI类型的结果

    compare_ai_results(
        greedy_path=get_path("results/greedy_results.json"),
        mcts_path=get_path("results/mcts_results.json"),
        ml_path=get_path("results/ml_results.json"),
        save_path=get_path("results/ai_comparison.json")
    )
