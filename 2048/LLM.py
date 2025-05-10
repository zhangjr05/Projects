import copy
import time
import os
import json
import gradio as gr
import re
from Greedy_ai import Greedy_AI2048

# 使用环境变量安全存储API密钥
GLOBAL_API_KEY = 'sk-11742ea4a8cc421e949e05c049d86e51'

try:
    from dashscope import Generation, save_api_key
    save_api_key(GLOBAL_API_KEY)
    Generation.api_key = GLOBAL_API_KEY
    os.environ["DASHSCOPE_API_KEY"] = GLOBAL_API_KEY
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"导入DashScope失败: {e}")
    LLM_AVAILABLE = False

def ensure_api_key():
    """确保API密钥已设置"""
    try:
        from dashscope import Generation
        if not Generation.api_key:
            Generation.api_key = GLOBAL_API_KEY
        return True
    except:
        return False

class LLM_AI2048(Greedy_AI2048):
    """使用LLM增强的2048 AI"""
    
    def __init__(self, game=None, model="qwen-max", api_key=None):
        super().__init__(game)
        self.model = model
        self.move_history = []
        self.decision_cache = {}
        self.use_llm = LLM_AVAILABLE
        self.failed_calls = 0
        self.cache_hits = 0
        self.total_calls = 0
        
        # 优化的LLM提示模板
        self.prompt_template = """
你是2048游戏AI专家。分析游戏状态并给出最佳移动方向。

当前游戏状态:
{}

可行方向:
- 上(0) 
- 右(1) 
- 下(2) 
- 左(3)

2048游戏最佳策略:
1. 始终保持最大数字固定在一个角落(优先左下角)
2. 沿着主对角线或边缘维持严格的降序排列
3. 保持足够空白格子以应对随机新块
4. 维持"蛇形路径"结构(例如: 从左下16-8-4-2沿Z字形排列)
5. 避免将大数字分散在棋盘上
6. 合并方向应该始终指向最大数字所在的角落

分析每个有效方向的移动结果:
1. 这个移动是否保持最大数字在角落?
2. 这个移动是否维持单调递减序列?
3. 这个移动后是否有足够的空白格子?
4. 这个移动是否创造了合并机会?

给出你的决策过程，最后用一行给出选择的方向(只需数字0-3):
"""
        # API密钥设置
        if api_key:
            self._set_api_key(api_key)

    def _set_api_key(self, api_key):
        """设置API密钥"""
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
        
        # LLM不可用时使用贪婪算法
        if self.failed_calls >= 3:
            self.use_llm = False
        
        # 优先检查缓存
        grid_tuple = tuple(map(tuple, self.game.get_grid()))
        if grid_tuple in self.decision_cache:
            self.cache_hits += 1
            return self.decision_cache[grid_tuple]
        
        # 紧急情况或LLM不可用时使用贪婪算法
        if not self.use_llm:
            return self._fallback_to_greedy()
        
        # 动态选择决策策略
        max_tile = max(max(row) for row in self.game.get_grid())
        empty_count = sum(cell == 0 for row in self.game.get_grid() for cell in row)
        
        # 早期/晚期阶段使用贪婪算法
        if max_tile < 64 or empty_count <= 3 or self.failed_calls >= 2:
            return self._fallback_to_greedy()
        
        # 中期使用LLM
        try:
            return self._get_move_from_llm(grid_tuple)
        except Exception as e:
            self.failed_calls += 1
            print(f"LLM调用错误: {str(e)[:100]}...")
            return self._fallback_to_greedy()

    def _fallback_to_greedy(self):
        """回退到贪婪算法"""
        # 直接使用父类的方法
        direction = super().get_move()
        
        # 记录决策
        self.move_history.append({
            "state": self._format_game_state(),
            "response": "使用贪婪搜索算法决策" + 
                      ("" if self.use_llm else "(LLM已禁用)"),
            "direction": direction,
            "time": time.time()
        })
        
        # 缓存决策
        grid_tuple = tuple(map(tuple, self.game.get_grid()))
        self.decision_cache[grid_tuple] = direction
        
        return direction

    def _get_move_from_llm(self, grid_tuple):
        """从LLM获取移动方向"""
        ensure_api_key()
        start_time = time.time()
        
        # 准备游戏状态描述
        game_state_text = self._format_game_state()
        prompt = self.prompt_template.format(game_state_text)
        
        # 调用LLM API
        response = Generation.call(
            model=self.model,
            prompt=prompt,
            result_format='message',
            max_tokens=300,
            temperature=0.1
        )
        
        content = response.output.choices[0]['message']['content']
        direction = self._parse_llm_response(content)
        
        # 验证方向有效性
        if direction not in [0, 1, 2, 3] or not self._is_valid_move(direction):
            old_direction = direction
            direction = super().get_move()  # 使用父类方法
            content += f"\n[无效移动 {old_direction}，已替换为有效移动 {direction}]"
        
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

    def _is_valid_move(self, direction):
        """检查移动是否有效"""
        if direction not in [0, 1, 2, 3]:
            return False
            
        game_copy = copy.deepcopy(self.game)
        return game_copy.move(direction)
    
    def _format_game_state(self):
        """格式化游戏状态"""
        grid = self.game.get_grid()
        score = self.game.get_score()
        
        # 简化网格显示
        grid_text = "网格:\n"
        for row in grid:
            grid_text += "|" + "|".join(f"{cell:^4}" if cell else "    " for cell in row) + "|\n"
        
        empty_count = sum(cell == 0 for row in grid for cell in row)
        max_tile = max(max(row) for row in grid)
        
        # 添加有效移动方向
        valid_moves = []
        for direction in range(4):
            direction_name = ["上", "右", "下", "左"][direction]
            game_copy = copy.deepcopy(self.game)
            if game_copy.move(direction):
                valid_moves.append(f"{direction}({direction_name})")
        
        state_text = f"{grid_text}\n"
        state_text += f"分数:{score} 空格:{empty_count} 最大值:{max_tile}\n"
        state_text += f"有效移动: {', '.join(valid_moves)}\n"
        
        return state_text

    def _parse_llm_response(self, response_text):
        """解析LLM响应获取方向"""
        # 查找数字方向
        patterns = [
            r'最终(?:选择|决策|方向)[^\d]*?([0-3])',
            r'(?:选择|决策|方向)[是为]?\s*?([0-3])',
            r'(?:方向|决策|移动|选择)\D*?([0-3])[^0-9]*$',
            r'([0-3])\s*$'  # 最后一行只有一个数字
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                return int(match.group(1))
            
        # 查找最后一行数字
        lines = response_text.strip().split('\n')
        for line in reversed(lines):
            for num in ["0", "1", "2", "3"]:
                if num in line and not re.search(r'\d+\.\d+', line):
                    return int(num)
        
        # 查找方向名称
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
    """创建Gradio界面"""
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
        """初始化游戏"""
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
        """格式化游戏网格为HTML"""
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
        """格式化AI思考过程"""
        if not thoughts:
            return ""
        
        move_number = global_state["move_count"]
        
        md = f"## 移动 #{move_number}\n\n"
        
        direction_names = ['上', '右', '下', '左']
        direction = thoughts.get('direction', 0)
        md += f"**方向:** {direction_names[direction]} (代码:{direction})\n\n"

        if 'process_time' in thoughts:
            md += f"**处理时间:** {thoughts['process_time']:.3f}秒\n\n"

        md += "**分析:**\n\n"
        md += f"```\n{thoughts['response']}\n```"
        
        return md
    
    def make_move():
        """执行一步移动"""
        if global_state["game"] is None:
            initialize_game()
        
        if global_state["game"].get_game_state() != 0:
            return format_grid(global_state["game"].get_grid()), f"游戏结束，最终分数: {global_state['game'].get_score()}", ""
        
        start_time = time.time()
        direction = global_state["ai"].get_move()
        decision_time = time.time() - start_time
        
        # 修复：执行实际移动
        moved = global_state["game"].move(direction)
        
        global_state["move_count"] += 1
        global_state["game_history"].append(copy.deepcopy(global_state["game"].get_grid()))
        global_state["last_update_time"] = time.time()
        
        thoughts = None
        if global_state["ai"].move_history and len(global_state["ai"].move_history) > 0:
            thoughts = global_state["ai"].move_history[-1]
            if 'process_time' not in thoughts:
                thoughts['process_time'] = decision_time
        
        thoughts_md = format_thoughts(thoughts)
        
        max_tile = max(max(row) for row in global_state["game"].get_grid())
        status = global_state["game"].get_game_state()
        status_text = "进行中"
        
        # 修复：当达到2048也算成功
        if status == 1 or max_tile >= 2048:
            status_text = "胜利！"
        elif status == 2:
            status_text = "失败"
        
        # 判断使用LLM还是贪婪算法
        method = "贪婪" if thoughts and "使用贪婪" in thoughts.get('response', "") else "LLM"
        
        return format_grid(global_state["game"].get_grid()), f"移动 #{global_state['move_count']}: {'上右下左'[direction]} ({method})，分数={global_state['game'].get_score()}，状态={status_text}", thoughts_md
    
    def auto_play():
        """自动运行游戏"""
        global_state["running"] = True
        
        if global_state["game"] is None:
            initialize_game()
        
        result = format_grid(global_state["game"].get_grid()), f"自动游戏开始，分数: {global_state['game'].get_score()}", ""
        yield result
        
        update_frequency = 3  # 每3步更新一次UI
        min_update_interval = 0.5  # 最小更新间隔(秒)
        steps_since_update = 0
        
        while global_state["running"] and global_state["game"]:
            # 检查游戏是否结束
            max_tile = max(max(row) for row in global_state["game"].get_grid())
            if global_state["game"].get_game_state() != 0 or max_tile >= 2048:
                break
                
            grid_html, status, thoughts_md = make_move()
            steps_since_update += 1
            
            current_time = time.time()
            time_since_last_update = current_time - global_state["last_update_time"]
            
            if steps_since_update >= update_frequency or time_since_last_update >= min_update_interval:
                global_state["last_update_time"] = current_time
                steps_since_update = 0
                yield grid_html, status, thoughts_md
            
            # 动态延迟
            grid = global_state["game"].get_grid()
            empty_count = sum(cell == 0 for row in grid for cell in row)
            delay = 0.01 if empty_count <= 3 else 0.05
            time.sleep(delay)
        
        final_score = global_state["game"].get_score() if global_state["game"] else 0
        stats = global_state["ai"].get_stats() if global_state["ai"] else {}
        llm_ratio = f"LLM使用率: {1 - stats.get('cache_hit_ratio', 0):.1%}" if stats else ""
        
        # 判断游戏结果
        max_tile = max(max(row) for row in global_state["game"].get_grid())
        result_text = "胜利！" if max_tile >= 2048 else "失败" if global_state["game"].get_game_state() == 2 else "游戏结束"
        
        return format_grid(global_state["game"].get_grid()), f"{result_text}，最终分数: {final_score}，共{global_state['move_count']}步 {llm_ratio}", ""
    
    def stop_auto_play():
        """停止自动运行"""
        global_state["running"] = False
        
        if global_state["game"] is None:
            return "", "游戏未初始化", ""
        
        stats = global_state["ai"].get_stats() if global_state["ai"] else {}
        cache_info = f"，缓存命中率: {stats.get('cache_hit_ratio', 0):.1%}" if stats else ""
        
        return format_grid(global_state["game"].get_grid()), f"自动游戏已停止，分数: {global_state['game'].get_score()}{cache_info}", ""
    
    def save_results():
        """保存游戏结果"""
        if global_state["game"] is None:
            return "游戏未初始化"
        
        if global_state["ai"]:
            filename = global_state["ai"].save_history()
            stats = global_state["ai"].get_stats()
            cache_hit = f"缓存命中率: {stats['cache_hit_ratio']:.1%}" if stats else ""
            return f"游戏历史已保存到 {filename}，共{global_state['move_count']}步，最终分数: {global_state['game'].get_score()}，{cache_hit}"
        return "AI未初始化，无法保存历史"
    
    def set_api_key(key):
        """设置API密钥"""
        try:
            global GLOBAL_API_KEY
            from dashscope import Generation, save_api_key
            save_api_key(key)
            Generation.api_key = key
            os.environ["DASHSCOPE_API_KEY"] = key
            GLOBAL_API_KEY = key
            
            # 重置AI
            if global_state["ai"]:
                global_state["ai"]._set_api_key(key)
                global_state["ai"].use_llm = True
                global_state["ai"].failed_calls = 0
            
            return f"API密钥已设置: {key[:5]}****"
        except Exception as e:
            return f"API密钥设置失败: {str(e)}"
    
    # 创建Gradio界面
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
    """创建LLM AI实例"""
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