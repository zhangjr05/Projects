import copy
import time
from Greedy_ai import Greedy_AI2048
import os
import json
import gradio as gr
import re

try:
    from dashscope import Generation, save_api_key
    GLOBAL_API_KEY = 'your_api_key'
    save_api_key(GLOBAL_API_KEY)
    Generation.api_key = GLOBAL_API_KEY
    os.environ["DASHSCOPE_API_KEY"] = GLOBAL_API_KEY
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"导入DashScope失败: {e}")
    LLM_AVAILABLE = False

def ensure_api_key():
    try:
        from dashscope import Generation
        if not Generation.api_key:
            Generation.api_key = GLOBAL_API_KEY
        return True
    except:
        return False

class LLM_AI2048(Greedy_AI2048):
    def __init__(self, game=None, model="qwen-max", api_key=None):
        super().__init__(game)
        self.model = model
        self.move_history = []
        self.decision_cache = {}
        self.use_llm = LLM_AVAILABLE
        self.failed_calls = 0
        self.cache_hits = 0
        self.total_calls = 0
        
        # 简化提示模板，减少token数量
        self.prompt_template = """
你是2048游戏AI专家。分析游戏状态并给出最佳移动方向。

当前游戏状态:
{}

可行方向:
- 上(0) 
- 右(1) 
- 下(2) 
- 左(3)

请考虑:
1. 保持最大数字在角落
2. 维持递减序列
3. 保持足够空白格子
4. 优先合并大数字

简要分析各方向优缺点，最后给出最佳方向(0-3)。

最终决策(仅需数字0-3): 
"""
        # API密钥设置
        if api_key:
            self._set_api_key(api_key)

    def _set_api_key(self, api_key):
        """单独处理API密钥设置"""
        try:
            from dashscope import Generation, save_api_key
            save_api_key(api_key)
            Generation.api_key = api_key
            os.environ["DASHSCOPE_API_KEY"] = api_key
            self.use_llm = True
            return True
        except Exception:
            return False

    def get_move(self):
        """获取下一步移动方向"""
        if not self.game:
            return 0
        
        self.total_calls += 1
        
        # 检查特殊条件
        if self.failed_calls >= 3:
            self.use_llm = False
        
        # 优先检查缓存
        grid_tuple = tuple(map(tuple, self.game.get_grid()))
        if grid_tuple in self.decision_cache:
            self.cache_hits += 1
            return self.decision_cache[grid_tuple]
        
        # 紧急情况或LLM不可用时使用评估函数
        if not self.use_llm or self._is_emergency_situation():
            return self._fallback_to_greedy()
        
        # 使用LLM做决策
        return self._get_move_from_llm(grid_tuple)
    
    def _is_emergency_situation(self):
        """检查是否为紧急情况（空格很少或需要快速响应）"""
        grid = self.game.get_grid()
        empty_count = sum(cell == 0 for row in grid for cell in row)
        return empty_count <= 2  # 空格少于等于2个视为紧急
    
    def _fallback_to_greedy(self):
        """回退到贪婪算法"""
        direction = self._get_best_move_by_evaluation()
        
        self.move_history.append({
            "state": self._format_game_state_compact(),
            "response": "使用评估函数决策" + ("" if self.use_llm else "(LLM已禁用)"),
            "direction": direction,
            "time": time.time()
        })
        
        return direction
    
    def _get_move_from_llm(self, grid_tuple):
        """从LLM获取移动方向"""
        try:
            ensure_api_key()
            start_time = time.time()
            
            # 使用更紧凑的游戏状态描述减少token数量
            game_state_text = self._format_game_state_compact()
            prompt = self.prompt_template.format(game_state_text)
            
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                result_format='message',
                max_tokens=600,  # 减少token上限以加快响应
                temperature=0.2  # 降低温度提高确定性
            )
            
            content = response.output.choices[0]['message']['content']
            
            # 解析响应获取方向
            direction = self._parse_llm_response(content)
            
            # 验证方向的有效性
            if not self._is_valid_move(direction):
                # 如果LLM给出无效移动，使用贪婪算法
                direction = self._get_best_move_by_evaluation()
                content += "\n[无效移动，使用评估函数替代]"
            
            # 记录决策
            process_time = time.time() - start_time
            self.move_history.append({
                "state": game_state_text,
                "response": content,
                "direction": direction,
                "time": time.time(),
                "process_time": process_time
            })
            
            # 缓存决策
            self.decision_cache[grid_tuple] = direction
            self.failed_calls = 0
            
            return direction
            
        except Exception as e:
            self.failed_calls += 1
            if self.failed_calls == 1:
                print(f"LLM调用错误: {str(e)[:100]}...")
            
            return self._fallback_to_greedy()
    
    def _is_valid_move(self, direction):
        """检查移动是否有效"""
        game_copy = copy.deepcopy(self.game)
        return game_copy.move(direction)
    
    def _format_game_state_compact(self):
        """生成更紧凑的游戏状态描述"""
        grid = self.game.get_grid()
        score = self.game.get_score()
        
        # 简化网格显示
        grid_text = "网格:\n"
        for row in grid:
            grid_text += "|" + "|".join(f"{cell:^4}" if cell else "    " for cell in row) + "|\n"
        
        empty_count = sum(cell == 0 for row in grid for cell in row)
        max_tile = max(max(row) for row in grid)
        
        # 计算可合并的方块对
        mergeable_pairs = self._count_mergeable_pairs()
        
        # 添加有效移动方向
        valid_moves = []
        for direction in range(4):
            direction_name = ["上", "右", "下", "左"][direction]
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                valid_moves.append(f"{direction}({direction_name})")
        
        state_text = f"{grid_text}\n"
        state_text += f"分数:{score} 空格:{empty_count} 最大值:{max_tile} 可合并对:{mergeable_pairs}\n"
        state_text += f"有效移动: {', '.join(valid_moves)}\n"
        
        return state_text
    
    def _count_mergeable_pairs(self):
        """计算可合并的方块对数量"""
        grid = self.game.get_grid()
        count = 0
        
        # 水平检查
        for i in range(4):
            for j in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i][j+1]:
                    count += 1
        
        # 垂直检查
        for j in range(4):
            for i in range(3):
                if grid[i][j] != 0 and grid[i][j] == grid[i+1][j]:
                    count += 1
                    
        return count
    
    def _parse_llm_response(self, response_text):
        """从LLM响应中提取移动方向"""
        # 优先查找最后出现的单个数字
        pattern = r'(?:方向|决策|移动|选择)\D*?([0-3])[^0-9]*$'
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            return int(match.group(1))
            
        # 查找最后一行包含的数字
        lines = response_text.strip().split('\n')
        for line in reversed(lines):
            for num in ["0", "1", "2", "3"]:
                if num in line and not re.search(r'\d+\.\d+', line):  # 避免匹配小数
                    return int(num)
        
        # 通过方向名称映射
        direction_words = {
            "上": 0, "up": 0, "向上": 0, 
            "右": 1, "right": 1, "向右": 1,
            "下": 2, "down": 2, "向下": 2,
            "左": 3, "left": 3, "向左": 3
        }
        
        for word, dir_num in direction_words.items():
            if word in response_text.lower():
                return dir_num
        
        # 默认返回左移
        return 3
    
    def _get_best_move_by_evaluation(self):
        """使用评估函数选择最佳移动"""
        valid_moves = []
        scores = []
        
        for direction in range(4):
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                valid_moves.append(direction)
                scores.append(super()._evaluate(game_copy))
        
        if not valid_moves:
            return 0
        
        best_idx = scores.index(max(scores))
        return valid_moves[best_idx]
    
    def get_stats(self):
        """获取统计信息"""
        return {
            "cache_hits": self.cache_hits,
            "total_calls": self.total_calls,
            "cache_hit_ratio": self.cache_hits / max(1, self.total_calls),
            "failed_calls": self.failed_calls,
            "llm_enabled": self.use_llm,
            "decisions_count": len(self.move_history)
        }
    
    def save_history(self, filename=None):
        """保存决策历史"""
        if not self.move_history:
            return
        
        if filename is None:
            filename = f"llm_decisions_{int(time.time())}.json"
        
        try:
            # 添加统计信息
            history_with_stats = {
                "stats": self.get_stats(),
                "decisions": self.move_history
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(history_with_stats, f, ensure_ascii=False, indent=2)
            print(f"决策历史已保存到 {filename}")
            return filename
        except Exception as e:
            print(f"保存决策历史时出错: {e}")
            return None


def create_gradio_interface():
    ensure_api_key()
    
    from game import Game2048
    
    global_state = {
        "game": None,
        "ai": None,
        "game_history": [],
        "move_count": 0,
        "running": False,
        "last_update_time": 0
    }
    
    def initialize_game():
        global_state["game"] = Game2048()
        global_state["ai"] = LLM_AI2048(
            game=global_state["game"]
        )
        global_state["game_history"] = [copy.deepcopy(global_state["game"].get_grid())]
        global_state["move_count"] = 0
        global_state["running"] = False
        global_state["last_update_time"] = time.time()
        return format_grid(global_state["game"].get_grid()), "游戏已初始化，当前分数: 0", ""
    
    def format_grid(grid):
        html = """
        <style>
        .game-container {
            width: 100%;
            max-width: 450px;
            margin: 0 auto;
            padding: 15px;
            background: #bbada0;
            border-radius: 8px;
            position: relative;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-gap: 15px;
            margin-bottom: 10px;
        }
        .cell {
            aspect-ratio: 1/1;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 32px;
            font-weight: bold;
            border-radius: 5px;
            transition: all 0.1s ease;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }
        .cell-2 { background: #eee4da; color: #776e65; }
        .cell-4 { background: #ede0c8; color: #776e65; }
        .cell-8 { background: #f2b179; color: #f9f6f2; }
        .cell-16 { background: #f59563; color: #f9f6f2; }
        .cell-32 { background: #f67c5f; color: #f9f6f2; }
        .cell-64 { background: #f65e3b; color: #f9f6f2; }
        .cell-128 { background: #edcf72; color: #f9f6f2; font-size: 28px; }
        .cell-256 { background: #edcc61; color: #f9f6f2; font-size: 28px; }
        .cell-512 { background: #edc850; color: #f9f6f2; font-size: 28px; }
        .cell-1024 { background: #edc53f; color: #f9f6f2; font-size: 24px; }
        .cell-2048 { background: #edc22e; color: #f9f6f2; font-size: 24px; }
        .cell-0 { background: #cdc1b4; }
        </style>
        
        <div class="game-container">
        <div class="grid">
        """
        
        for row in grid:
            for cell in row:
                value = cell if cell > 0 else ""
                html += f'<div class="cell cell-{cell}">{value}</div>'
        
        html += """
        </div>
        </div>
        """
        return html
    
    def format_thoughts(thoughts):
        if not thoughts:
            return ""
        
        md = f"## 移动 #{global_state['move_count']}\n\n"
        
        # 添加移动方向和时间信息
        direction_names = ['上', '右', '下', '左']
        direction = thoughts.get('direction', 0)
        md += f"**方向:** {direction_names[direction]} (代码:{direction})\n\n"
        
        # 添加处理时间信息（如果有）
        if 'process_time' in thoughts:
            md += f"**处理时间:** {thoughts['process_time']:.3f}秒\n\n"
        
        # 显示LLM分析或评估函数信息
        md += "**分析:**\n\n"
        md += f"```\n{thoughts['response']}\n```"
        
        return md
    
    def make_move():
        if global_state["game"] is None:
            initialize_game()
        
        if global_state["game"].get_game_state() != 0:
            return format_grid(global_state["game"].get_grid()), f"游戏结束，最终分数: {global_state['game'].get_score()}", ""
        
        start_time = time.time()
        direction = global_state["ai"].get_move()
        decision_time = time.time() - start_time
        
        moved = global_state["game"].move(direction)
        global_state["move_count"] += 1
        global_state["game_history"].append(copy.deepcopy(global_state["game"].get_grid()))
        global_state["last_update_time"] = time.time()
        
        thoughts = None
        if global_state["ai"].move_history and len(global_state["ai"].move_history) > 0:
            thoughts = global_state["ai"].move_history[-1]
            # 添加决策时间信息
            if 'process_time' not in thoughts:
                thoughts['process_time'] = decision_time
        
        thoughts_md = format_thoughts(thoughts)
        
        status = global_state["game"].get_game_state()
        status_text = "进行中"
        if status == 1:
            status_text = "胜利！"
        elif status == 2:
            status_text = "失败"
        
        # 添加LLM/贪婪信息
        method = "LLM" if "LLM" not in (thoughts.get('response', "") if thoughts else "") else "贪婪"
        
        return format_grid(global_state["game"].get_grid()), f"移动 #{global_state['move_count']}: {'上右下左'[direction]} ({method})，分数={global_state['game'].get_score()}，状态={status_text}", thoughts_md
    
    def auto_play():
        global_state["running"] = True
        
        if global_state["game"] is None:
            initialize_game()
        
        result = format_grid(global_state["game"].get_grid()), f"自动游戏开始，分数: {global_state['game'].get_score()}", ""
        yield result
        
        # 改进刷新机制：基于时间和步数的自适应刷新
        update_frequency = 3  # 每隔多少步更新一次UI
        min_update_interval = 0.5  # 最小更新间隔(秒)
        steps_since_update = 0
        
        while global_state["running"] and global_state["game"] and global_state["game"].get_game_state() == 0:
            grid_html, status, thoughts_md = make_move()
            steps_since_update += 1
            
            current_time = time.time()
            time_since_last_update = current_time - global_state["last_update_time"]
            
            # 满足以下任一条件时更新UI：
            # 1. 已执行足够多步骤
            # 2. 距离上次更新已经过去足够长时间
            if steps_since_update >= update_frequency or time_since_last_update >= min_update_interval:
                global_state["last_update_time"] = current_time
                steps_since_update = 0
                yield grid_html, status, thoughts_md
            
            # 动态延迟：空格越少，延迟越短（更快响应紧急情况）
            grid = global_state["game"].get_grid()
            empty_count = sum(cell == 0 for row in grid for cell in row)
            delay = 0.01 if empty_count <= 3 else 0.05
            time.sleep(delay)
        
        final_score = global_state["game"].get_score() if global_state["game"] else 0
        stats = global_state["ai"].get_stats() if global_state["ai"] else {}
        llm_ratio = f"LLM使用率: {1 - stats.get('cache_hit_ratio', 0):.1%}" if stats else ""
        
        return format_grid(global_state["game"].get_grid()), f"游戏结束，最终分数: {final_score}，共{global_state['move_count']}步 {llm_ratio}", ""
    
    def stop_auto_play():
        global_state["running"] = False
        
        if global_state["game"] is None:
            return "", "游戏未初始化", ""
        
        stats = global_state["ai"].get_stats() if global_state["ai"] else {}
        cache_info = f"，缓存命中率: {stats.get('cache_hit_ratio', 0):.1%}" if stats else ""
        
        return format_grid(global_state["game"].get_grid()), f"自动游戏已停止，分数: {global_state['game'].get_score()}{cache_info}", ""
    
    def save_results():
        if global_state["game"] is None:
            return "游戏未初始化"
        
        if global_state["ai"]:
            filename = global_state["ai"].save_history()
            stats = global_state["ai"].get_stats()
            cache_hit = f"缓存命中率: {stats['cache_hit_ratio']:.1%}" if stats else ""
            return f"游戏历史已保存到 {filename}，共{global_state['move_count']}步，最终分数: {global_state['game'].get_score()}，{cache_hit}"
        return "AI未初始化，无法保存历史"
    
    def set_api_key(key):
        try:
            global GLOBAL_API_KEY
            from dashscope import Generation, save_api_key
            save_api_key(key)
            Generation.api_key = key
            os.environ["DASHSCOPE_API_KEY"] = key
            GLOBAL_API_KEY = key
            
            # 重置AI以使用新密钥
            if global_state["ai"]:
                global_state["ai"]._set_api_key(key)
                global_state["ai"].use_llm = True
                global_state["ai"].failed_calls = 0
            
            return f"API密钥已设置: {key[:5]}****"
        except Exception as e:
            return f"API密钥设置失败: {str(e)}"
    
    with gr.Blocks(title="LLM玩2048") as demo:
        gr.Markdown("# 🤖 通义千问玩2048")
        gr.Markdown("使用大语言模型来玩2048游戏")
        
        with gr.Row():
            api_input = gr.Textbox(
                label="通义千问API密钥", 
                placeholder="输入API密钥后点击设置",
                type="password"
            )
            api_button = gr.Button("设置API密钥")
            api_status = gr.Textbox(label="API状态")
        
        with gr.Row():
            with gr.Column(scale=3):
                grid_display = gr.HTML()
                status_text = gr.Textbox(label="状态")
                
                with gr.Row():
                    init_button = gr.Button("初始化游戏", variant="primary")
                    move_button = gr.Button("执行一步")
                    auto_button = gr.Button("自动运行", variant="primary")
                    stop_button = gr.Button("停止", variant="stop")
                    save_button = gr.Button("保存历史")
                
                save_status = gr.Textbox(label="保存状态")
                
            with gr.Column(scale=4):
                thoughts_display = gr.Markdown()
        
        api_button.click(set_api_key, inputs=[api_input], outputs=[api_status])
        init_button.click(initialize_game, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        move_button.click(make_move, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        auto_button.click(auto_play, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        stop_button.click(stop_auto_play, inputs=[], outputs=[grid_display, status_text, thoughts_display])
        save_button.click(save_results, inputs=[], outputs=[save_status])
        
        demo.load(lambda: gr.update(value=GLOBAL_API_KEY or ""), outputs=[api_input])
    
    return demo

def create_llm_ai(game, api_key=None):
    if api_key:
        try:
            from dashscope import save_api_key, Generation
            save_api_key(api_key)
            Generation.api_key = api_key
            os.environ["DASHSCOPE_API_KEY"] = api_key
        except ImportError:
            pass
    
    ai = LLM_AI2048(game)
    return ai

if __name__ == "__main__":
    ensure_api_key()
    demo = create_gradio_interface()
    demo.launch()