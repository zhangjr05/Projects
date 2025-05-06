import time
import json
import numpy as np
import matplotlib.pyplot as plt
from game import Game2048
from Greedy_ai import Greedy_AI2048
from MCTS_ai import MCTS_AI2048
from utils import get_path


def test_ai_performance(ai_class=Greedy_AI2048, ai_name="Greedy", num_games=10, max_moves=10000, **kwargs):
    """测试AI性能并返回结果"""
    scores = []
    max_tiles = []
    moves_count = []
    game_durations = []

    for i in range(num_games):
        print(f"Game Running: {i + 1}/{num_games} ")
        game = Game2048()
        ai = ai_class(game, **kwargs)
        
        move_count = 0
        start_time = time.time()

        while game.get_game_state() == 0 and move_count < max_moves:
            move = ai.get_move()
            game.move(move)
            move_count += 1
        
        end_time = time.time()

        # 记录结果
        scores.append(game.get_score())
        max_tiles.append(max(max(row) for row in game.get_grid()))
        moves_count.append(move_count)
        game_durations.append(end_time - start_time)
        
        # 打印当前游戏结果
        print(f"Score: {game.get_score()}, Max Tile: {max(max(row) for row in game.get_grid())}")

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
    print(f"\n===== {ai_name} AI Test Results =====")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return results


def test_greedy_ai(num_games=200, max_moves=10000, save_path=None):
    """测试贪婪AI并可选保存结果"""
    print("\nTesting Greedy AI...")
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
        print(f"Results saved to {save_path}")
    
    return greedy_results


def test_mcts_ai(num_games=200, max_moves=10000, simulation_time=0.5, save_path=None):
    """测试MCTS AI并可选保存结果"""
    print("\nTesting MCTS AI...")
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
        print(f"Results saved to {save_path}")
    
    return mcts_results


def visualize_results(results, show=True):
    """可视化单个AI的测试结果"""
    # 获取AI名称
    ai_name = results.get("ai_name", "Unknown")
    
    plt.figure(figsize=(15, 10))

    plt.subplot(2, 2, 1)
    plt.hist(results["scores"], bins=10)
    plt.title(f"{ai_name} - Score Distribution")
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    max_score = max(results["scores"]) if results["scores"] else 1000
    plt.xlim(0, max(10000, max_score * 1.2))

    plt.subplot(2, 2, 2)
    plt.hist(results["max_tiles"], bins=[2**i for i in range(1, 13)])
    plt.title(f"{ai_name} - Max Tile Distribution")
    plt.xlabel("Tile Value")
    plt.ylabel("Frequency")
    plt.xscale("log", base=2)

    plt.subplot(2, 2, 3)
    plt.hist(results["moves_count"], bins=10)
    plt.title(f"{ai_name} - Move Count Distribution")
    plt.xlabel("Number of Moves")
    plt.ylabel("Frequency")
    
    plt.subplot(2, 2, 4)
    plt.hist(results["game_durations"], bins=10)
    plt.title(f"{ai_name} - Game Duration Distribution")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Frequency")

    plt.tight_layout()
    
    if show:
        plt.show()
    
    return plt


def compare_ai_results(greedy_results=None, mcts_results=None, greedy_path=None, mcts_path=None, save_path=None, show=True):
    """比较两种AI的结果并创建对比图表"""
    # 如果提供了文件路径，从文件加载结果
    if greedy_path and not greedy_results:
        with open(greedy_path, 'r') as f:
            greedy_results = json.load(f)
    
    if mcts_path and not mcts_results:
        with open(mcts_path, 'r') as f:
            mcts_results = json.load(f)
    
    # 确保我们有两种AI的结果
    if not greedy_results or not mcts_results:
        print("Error: Need results for both Greedy and MCTS AI to compare")
        return None
    
    plt.figure(figsize=(15, 10))
    
    # 比较平均分数
    plt.subplot(2, 2, 1)
    ai_names = ["Greedy", "MCTS"]
    avg_scores = [
        greedy_results["stats"]["average_score"],
        mcts_results["stats"]["average_score"]
    ]
    plt.bar(ai_names, avg_scores)
    plt.title("Average Score Comparison")
    plt.ylabel("Score")
    
    # 比较平均最大方块
    plt.subplot(2, 2, 2)
    avg_max_tiles = [
        greedy_results["stats"]["average_max_tile"],
        mcts_results["stats"]["average_max_tile"]
    ]
    plt.bar(ai_names, avg_max_tiles)
    plt.title("Average Max Tile Comparison")
    plt.ylabel("Tile Value")
    
    # 比较平均移动次数
    plt.subplot(2, 2, 3)
    avg_moves = [
        greedy_results["stats"]["average_moves"],
        mcts_results["stats"]["average_moves"]
    ]
    plt.bar(ai_names, avg_moves)
    plt.title("Average Moves Comparison")
    plt.ylabel("Number of Moves")
    
    # 比较2048成功率
    plt.subplot(2, 2, 4)
    success_rates = [
        greedy_results["stats"]["success_rate_2048"],
        mcts_results["stats"]["success_rate_2048"]
    ]
    plt.bar(ai_names, success_rates)
    plt.title("2048 Success Rate Comparison (%)")
    plt.ylabel("Success Rate")
    
    plt.tight_layout()
    
    # 打印简单比较
    print("\n===== AI Performance Comparison =====")
    print(f"Greedy average score: {greedy_results['stats']['average_score']}")
    print(f"MCTS average score: {mcts_results['stats']['average_score']}")
    print(f"Greedy average max tile: {greedy_results['stats']['average_max_tile']}")
    print(f"MCTS average max tile: {mcts_results['stats']['average_max_tile']}")
    print(f"Greedy success rate (2048): {greedy_results['stats']['success_rate_2048']}%")
    print(f"MCTS success rate (2048): {mcts_results['stats']['success_rate_2048']}%")
    
    # 如果提供保存路径，保存比较数据
    if save_path:
        comparison_data = {
            "greedy": {
                "average_score": greedy_results["stats"]["average_score"],
                "highest_score": greedy_results["stats"]["highest_score"],
                "average_max_tile": greedy_results["stats"]["average_max_tile"],
                "highest_max_tile": greedy_results["stats"]["highest_max_tile"],
                "success_rate_2048": greedy_results["stats"]["success_rate_2048"]
            },
            "mcts": {
                "average_score": mcts_results["stats"]["average_score"],
                "highest_score": mcts_results["stats"]["highest_score"],
                "average_max_tile": mcts_results["stats"]["average_max_tile"],
                "highest_max_tile": mcts_results["stats"]["highest_max_tile"],
                "success_rate_2048": mcts_results["stats"]["success_rate_2048"]
            },
            "test_params": {
                "greedy": greedy_results.get("test_params", {}),
                "mcts": mcts_results.get("test_params", {})
            }
        }
        
        with open(save_path, 'w') as f:
            json.dump(comparison_data, f, indent=4)
        print(f"Comparison data saved to {save_path}")
    
    if show:
        plt.show()
    
    return plt


if __name__ == "__main__":
    # 设置测试参数
    num_games = 100
    max_moves = 10000
    simulation_time = 0.5
    
    # # 测试贪婪AI
    # greedy_results = test_greedy_ai(
    #     num_games=num_games, 
    #     max_moves=max_moves, 
    #     save_path=get_path("greedy_results.json")
    # )
    
    # # 测试MCTS AI
    # mcts_results = test_mcts_ai(
    #     num_games=num_games, 
    #     max_moves=max_moves, 
    #     simulation_time=simulation_time, 
    #     save_path=get_path("mcts_results.json")
    # )
    
    # 比较结果
    compare_ai_results(
        greedy_path=get_path("greedy_results.json"), 
        mcts_path=get_path("mcts_results.json"), 
        save_path=get_path("comparison_results.json")
    )