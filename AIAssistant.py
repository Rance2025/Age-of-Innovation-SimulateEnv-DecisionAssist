import os
import dashscope
import json
from typing import Dict, List, Optional, Any
from http import HTTPStatus


class AIAssistant:
    """
    Age of Innovation 策略顾问类
    
    特性：
    - 多轮决策，上下文连贯
    - 上下文管理（仅保留决策摘要，节省 token）
    - 多实例隔离（同一 API key 互不影响）
    """
    
    # ========== 类常量 ==========
    DEFAULT_MODEL = "qwen3.5-397b-a17b"
    MAX_ROUNDS = 6  # 游戏最多 6 轮
    MAX_RETRIES = 3
    MAX_CONTEXT_ROUNDS = 5  # 摘要管理时保留的最大轮次数
    
    def __init__(
        self, 
        player_id: int,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        """
        【初始化】AI 顾问
        
        参数:
            api_key: DashScope API Key
            model: 模型名称
            game_id: 游戏实例 ID（用于日志/调试）
            context_management: 上下文管理策略
        """
        # ========== 步骤 0.1: 基础配置 ==========
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        self.model = model
        
        # ========== 步骤 0.2: 实例独立状态初始化 ==========
        self.player_id: int = player_id
        self.system_prompt: str = ''
        self.messages: List[Dict] = []
        self.valid_action_ids: List[int] = []
        self.current_round: int = 0
        
        # ========== 步骤 0.3: 游戏状态占位 ==========
        self.available_actions: Dict[int, str] = {}
        self.game_state: str = ""
        
        # ========== 步骤 0.4: 历史记录初始化 ==========
        self.decision_history: Dict[int, list[Dict]] = {round_idx: [] for round_idx in range(7)}
        self.round_summaries: Dict[int, str] = {round_idx: '' for round_idx in range(7)}
        
        # ========== 步骤 0.5: SDK 配置 ==========
        dashscope.api_key = self.api_key
        dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
        
        # ========== 步骤 0.6: 构建工具列表 ==========
        self.tools = self._define_tools()
        
        # ========== 步骤 0.7: 构建工具执行注册表 ==========
        self.tools_registry = self._build_tools_registry()

        # ========== 步骤 0.8: 初始化 system_prompt ==========
        self._build_system_prompt()

        # ========== 步骤 0.9: 初始化 messages ==========
        self._init_messages()

    # =============================== 核心接口 ===============================
    def decide(
        self, 
        available_actions: Dict[int, str], 
        game_state: str,
        current_round: Optional[int] = None
    ) -> Optional[Dict]:
        """
        【主函数】执行一次决策（对外唯一接口）
        
        参数:
            available_actions: 当前可用行动 {ID: 描述}
            game_state: 当前游戏状态
            current_round: 当前轮次（不传则自动递增）
        
        返回:
            {"action_id": int, "reason": str, "confidence": float}
        """
        # ========== 步骤 1: 更新游戏状态 ==========
        self.available_actions = available_actions
        self.game_state = game_state
        
        # ========== 步骤 2: 构建合法行动id ==========
        self.valid_action_ids = list(available_actions.keys())
        
        # ========== 步骤 3: 汇总上一回合上下文 ==========
        if self.current_round != current_round:
            # TODO 整合上一轮上下文
            self._manage_context()
            self.current_round = current_round
            
        # ========== 步骤 4: 构建当前轮次的用户消息 ==========
        self.messages.append({
            "role": "user",
            "content": self._build_user_prompt()
        })
        
        # ========== 步骤 5: 主循环 - 处理工具调用 ==========
        for attempt in range(self.MAX_RETRIES):
            try:
                # 步骤 5.1: 调用模型
                # 判断是否强制调用最终决策工具
                # 最后一次重试时强制调用 select_action_id，避免无限循环
                force_final = (attempt == self.MAX_RETRIES - 1)
                assistant_msg = self._call_model(force_final=force_final)
                self.messages.append(assistant_msg)
                
                # 步骤 5.2: 检查是否有工具调用
                if self._check_tool_calls(assistant_msg, force_final=force_final):
                    pass
                
                # 步骤 5.3: 处理并行工具调用
                has_final_decision, tool_results = self._process_tool_calls(assistant_msg)
                
                # ✅ 快速检查：如果没有最终决策，跳过 _check_final_decision
                if not has_final_decision:
                    print("🔄 继续分析...")
                    continue

                # 步骤 5.4: 检查是否包含最终决策工具
                final_decision = self._check_final_decision(tool_results)
                
                if final_decision:
                    # 步骤 5.5: 验证并返回最终决策
                    result = self._validate_and_return(final_decision)
                    
                    # 步骤 5.6: 生成该轮摘要（剔除本轮分析过程）
                    if result:
                        self._generate_action_summary(result)
                    
                    return result
                else:
                    print("🔄 继续分析...")
                    continue
                    
            except Exception as e:
                # 步骤 5.7: 错误处理
                should_retry = self._handle_error(e, attempt)
                if not should_retry:
                    break
                continue
        
        # ========== 步骤 6: 重试失败后的 fallback ==========
        return self._fallback()
    
    # =============================== 辅助方法 ===============================
    
    # ========== 步骤 0.6: 定义工具 Schema ==========
    def _define_tools(self) -> List[Dict]:
        """
        步骤 0.6: 定义工具 Schema（给 API 看的）
        
        参数:
            valid_action_ids: 合法行动 ID 列表
        
        返回:
            工具定义列表
        """
        return [
            # 🎯 最终决策工具（必须调用）
            {
                "type": "function",
                "function": {
                    "name": "select_action_id",
                    "description": "从可用行动列表中选择最佳行动并输出最终决策。这是必须调用的工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_id": {
                                "type": "integer",
                                "description": f"行动 ID，必须是以下值之一：{self.valid_action_ids}",
                            },
                            "reason": {
                                "type": "string",
                                "description": "选择该行动的详细理由，需结合当前游戏状态、回合目标、资源情况、派系能力进行分析"
                            },
                            "confidence": {
                                "type": "number",
                                "description": "决策置信度 0.0-1.0，表示你对该决策的把握程度",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["action_id", "reason", "confidence"]
                    },
                },
            },
            # 🔍 查询规则工具
            {
                "type": "function",
                "function": {
                    "name": "query_game_rule",
                    "description": "查询《Age of Innovation》的规则细节，如地形改造、城市建立、科学轨道等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "rule_topic": {
                                "type": "string",
                                "description": "要查询的规则主题，如 'terraforming', 'city founding', 'power cycle', 'science display', 'building upgrade' 等",
                                "enum": [
                                    "terraforming", "city_founding", "power_cycle", "science_display",
                                    "building_upgrade", "income", "sailing", "innovation", "competency",
                                    "palace", "round_score", "final_scoring", "faction_ability"
                                ]
                            }
                        },
                        "required": ["rule_topic"]
                    },
                },
            },
            # 💰 评估行动成本工具
            {
                "type": "function",
                "function": {
                    "name": "evaluate_action_cost",
                    "description": "评估某个行动的资源成本、机会成本和预期收益",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action_id": {
                                "type": "integer",
                                "description": "要评估的行动 ID",
                            },
                            "focus": {
                                "type": "string",
                                "description": "评估重点",
                                "enum": ["cost", "benefit", "opportunity", "risk", "all"]
                            }
                        },
                        "required": ["action_id"]
                    },
                },
            },
            # 📊 分析游戏状态工具
            {
                "type": "function",
                "function": {
                    "name": "analyze_game_state",
                    "description": "分析当前游戏状态的关键指标，如资源效率、扩张潜力、科技进度等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "description": "分析类型",
                                "enum": ["resource_efficiency", "expansion_potential", "science_progress", "area_control", "comprehensive"]
                            }
                        },
                        "required": ["analysis_type"]
                    },
                },
            },
        ]

    # ========== 步骤 0.7: 定义工具执行函数注册表 ==========
    def _build_tools_registry(self) -> Dict:
        """
        步骤 0.7: 定义工具执行函数注册表（本地代码执行的）
        
        参数:
            available_actions: {行动 ID: 行动描述} 字典
            game_state: 当前游戏状态描述
        
        返回:
            工具执行函数字典 {func_name: func}
        """
        
        # ========== 规则知识库（基于 PDF 规则书） ==========
        RULE_KNOWLEDGE = {
            "terraforming": """
            【地形改造规则】
            - 每个派系有原生地形（Native Terrain），只能在该地形上建造建筑
            - 改造成本：Terraforming Circle 上每远离原生地形 1 步 = 1 Spade
            - Spades 来源：Tools 兑换（初始 3 Tools = 1 Spade）、Power/Book/Special Actions、科学奖励
            - Spades 必须立即使用，不能储存
            - 改造后不一定要建造工坊，可留空供后续使用或再次改造
            """,
            
            "city_founding": """
            【城市建立规则】
            - 标准条件：4 个相邻建筑 + 总 Power 值≥7
            - 有 University：3 个建筑即可（仍需 Power≥7）
            - 有 Monument：2 个建筑即可（仍需 Power≥7）
            - 奖励：City Tile 上的分数 + 资源 + 1 个 Key（用于科学轨道 8 级+）
            - 每个城市 Tile 只能使用一次
            """,
            
            "power_cycle": """
            【Power 循环规则】
            - 3 个 Power Bowl：I → II → III → I（顺时针循环）
            - 获得 Power：从 Bowl I→II，若 I 空则 II→III，若 I+II 都空则无法获得
            - 花费 Power：只能从 Bowl III 花费，花费后回到 Bowl I
            - 建筑 Power 值：Workshop=1, Guild/School=2, Palace/University=3, Tower=2, Monument=4
            - 相邻对手建造时可获得 Power（需支付分数，1/2/3/4 Power 花费 0/1/2/3 分）
            """,
            
            "science_display": """
            【科学轨道规则】
            - 4 个学科：Banking（黄）、Law（蓝）、Engineering（棕）、Medicine（绿）
            - 升级方式：Send Scholar（占 2/3 格位）或返回 Scholar（升 1 级）
            - 关键等级：3/5/7/12 级获得 Power 循环奖励，9 级+ 获得每回合收入
            - 8 级+ 需要 City Key（每个学科独立需要 1 个 Key）
            - 每学科只有 1 个玩家能到达 12 级
            """,
            
            "building_upgrade": """
            【建筑升级规则】
            - Workshop → Guild：2 Tools + 6 Coins（有相邻对手建筑减为 3 Coins）
            - Guild → Palace：4 Tools + 6 Coins + 选择 Palace Tile
            - Guild → School：3 Tools + 5 Coins + 获得 Competency Tile
            - School → University：5 Tools + 8 Coins + 获得 Competency Tile
            - 升级视为建造新建筑，相邻对手可获得 Power
            """,
            
            "income": """
            【收入规则】
            - 每回合 Phase I 获得收入（Planning Display 上未被建筑覆盖的图标）
            - 来源：Planning Display、Round Bonus、Competency、Innovation、科学轨道 9 级+
            - 资源：Scholars（有限）、Coins/Tools/Books（无限）
            """,
            
            "sailing": """
            【航行规则】
            - Increase Sailing 行动：提升 Sailing Track，增加 Reach
            - Reach = Adjacent + 河流格数≤Sailing 值
            - 可通过河流扩张，使用 Bridges 连接两岸
            """,
            
            "innovation": """
            【创新规则】
            - Develop Innovation 行动：花费至少 5 Books（部分需特定学科）+ 5 Coins（未建 Palace 时）
            - 最多发展 3 个 Innovation
            - 类型：特殊能力、即时分数、额外建筑
            """,
            
            "competency": """
            【能力规则】
            - 来源：升级到 School 或 University 时选择
            - 共 12 种，每种 4 个，形成堆叠
            - 奖励：科学轨道等级 + Books（共 3 点）
            - 不能选择重复的 Competency
            """,
            
            "palace": """
            【宫殿规则】
            - 来源：Guild 升级到 Palace 时选择（17 种 Palace Tiles）
            - 每个 Palace 提供独特能力或特殊行动
            - 越晚建造选择越少（其他玩家已选的不能选）
            """,
            
            "round_score": """
            【回合分数规则】
            - 6 个 Round Score Tiles，每回合 1 个
            - 左侧：执行特定行动获得分数
            - 右侧：Phase III 科学奖励（第 6 回合不用）
            - 第 6 回合使用 Final Round Score Tile 替代科学奖励
            """,
            
            "final_scoring": """
            【终局计分规则】
            - Area Score：最大连通建筑群，第 1/2/3 名得 18/12/6 分
            - Science Score：每学科最高/次高/第三高得 8/4/2 分
            - Resource Score：剩余资源换 Coins，每 5 Coins = 1 分
            """,
            
            "faction_ability": """
            【派系能力规则】
            - 12 个派系各有特殊能力
            - 常见能力：起始学科等级、特殊行动、资源折扣、建造优惠等
            - 需结合具体派系 Tile 查看详细说明
            """
        }
        
        # ========== 工具执行函数 ==========
        
        def query_game_rule(arguments: Dict[str,str]) -> str:
            """查询规则细节"""
            rule_topic = arguments.get("rule_topic", "")
            topic_display = rule_topic.replace("_", " ").title()
            
            rule_content = RULE_KNOWLEDGE.get(rule_topic, f"未找到关于 '{rule_topic}' 的规则信息。")
            
            return f"【规则查询：{topic_display}】\n{rule_content.strip()}"
        
        def evaluate_action_cost(arguments: Dict) -> str:
            """评估行动成本"""
            action_id = arguments.get("action_id")
            focus = arguments.get("focus", "all")
            action_desc = self.available_actions.get(action_id, "未知行动")
            
            # 简单成本分析（实际可对接游戏状态计算）
            analysis = f"【行动评估：#{action_id} - {action_desc}】\n"
            
            if focus in ["cost", "all"]:
                analysis += "• 成本：需根据具体行动类型计算（Tools/Coins/Books/Scholars/Power）\n"
            if focus in ["benefit", "all"]:
                analysis += "• 收益：考虑 Round Score 奖励、长期战略价值、资源转化\n"
            if focus in ["opportunity", "all"]:
                analysis += "• 机会成本：执行此行动意味着放弃其他可选行动\n"
            if focus in ["risk", "all"]:
                analysis += "• 风险：资源断裂、被对手压制、偏离回合目标\n"
            
            analysis += "\n建议：结合当前 Round Score 目标、资源存量、派系能力综合评估。"
            
            return analysis
        
        def analyze_game_state(arguments: Dict) -> str:
            """分析游戏状态"""
            analysis_type = arguments.get("analysis_type", "comprehensive")
            
            analysis = f"【状态分析：{analysis_type}】\n"
            analysis += f"当前游戏状态摘要：{self.game_state[:200]}...\n"
            
            if analysis_type == "comprehensive":
                analysis += """
                分析维度：
                • 资源效率：Coins/Tools/Books/Scholars 的获取与消耗比
                • 扩张潜力：可改造地形、相邻空位、Sailing 值
                • 科技进度：4 学科等级、Keys 数量、9 级+ 收入潜力
                • 区域控制：最大连通建筑群、相邻对手数量
                """
            
            analysis += "\n建议：优先关注当前 Round Score 目标与派系长期战略的平衡。"
            
            return analysis
        
        return {
            "query_game_rule": query_game_rule,
            "evaluate_action_cost": evaluate_action_cost,
            "analyze_game_state": analyze_game_state,
        }

    # ========== 步骤 0.8: 初始化 system_prompt ==========
    def _build_system_prompt(self):
        """
        【步骤 0.8】构建系统提示词（仅初始化时调用一次）
        """
        
        # 格式化行动列表
        actions_formatted = "\n".join([
            f"  - 行动 #{aid}: {desc}" 
            for aid, desc in self.available_actions.items()
        ])
        
        self.system_prompt = f"""
            # 🎮 Role: Age of Innovation 策略大师

            你是一位精通桌游《Age of Innovation》（大创造时代）的顶级策略顾问。
            你熟悉游戏的所有核心机制：地形改造、Power 循环、建筑升级链、科学轨道、城市建立、12 派系能力、Innovation/Competency/Palace Tiles 选取等。

            # 📋 Current Available Actions（当前可用行动）
            {actions_formatted}

            # 📊 Current Game State（当前游戏状态）
            {self.game_state}

            # 🎯 Your Task（你的任务）
            根据当前游戏状态，从可用行动列表中选择**唯一最佳行动**，并通过调用 `select_action_id` 工具输出决策。

            #  Analysis Process（分析流程）
            在做出决策前，你可以（非强制）调用以下工具辅助分析（可以并行调用，但不能与`select_action_id`一同调用）：
            1. `query_game_rule` - 查询不确定的规则细节
            2. `evaluate_action_cost` - 评估特定行动的成本/收益/风险
            3. `analyze_game_state` - 分析当前游戏状态的关键指标

            **你有{self.MAX_RETRIES}次循环调起的机会，但无论是否调用上述工具，最后一轮必须调用 `select_action_id` 输出最终决策（也可以提前，不一定要在最后一轮）。**

            # ⚠️ Constraints（必须遵守的约束）
            1. **最终输出必须调用 `select_action_id` 工具**，不能直接回复自然语言。
            2. `action_id` 必须是**整数**，且严格属于 {self.valid_action_ids} 中的一个。
            3. `reason` 必须结合以下因素给出分析并整合关键信息（简要，不超过200字，推荐完成以下子目标）：
            - 【需分析】当前回合计分目标（如有）
            - 【需分析】资源存量与获取能力
            - 【需分析】长期战略（Area/Science/Resources 终局计分）
            - 【需记录】如获取能力、高科板块带来的持续的行动效果（这会影响未来的行动决策）
            - 【需记录】后续大致行动计划
            4. `confidence` 填写 0.0-1.0 的数值，表示你对该决策的把握程度。
            5. 禁止虚构不存在的行动 ID 或规则。
            6. 如果信息不足，可先调用查询工具，但**最后一轮必须输出决策**。

            # 📤 Output Format（工具参数格式）
            ```json
            {{
                "action_id": 1,
                "reason": "当前第 3 轮，Round Score 奖励建造工坊。你已有 2 个相邻工坊可升级，且工具充足（5 Tools）。优先扩张领土为后续城市奠基，同时利用相邻对手建筑获得 Power。工程学科已 4 级，符合 Moles 派系长期战略。",
                "confidence": 0.85
            }}
        """

    # ========== 步骤 0.9: 初始化 messages ==========
    def _init_messages(self):
        """【步骤 0.9】初始化对话历史（仅 system 消息）"""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
    
    # ========== 步骤 3: 管理上下文 ==========
    def _manage_context(self):
        """
        【步骤 3】管理上下文
        【轮次结束】汇总当前轮次的所有行动记录到 round_summaries
        
        功能：
        1. 调用模型将当前轮次的所有行动记录汇总为精炼摘要
        2. 包含历史行动总结 + 未来策略指导
        3. 存入 self.round_summaries[self.current_round]
        4. 清空 self.decision_history[self.current_round] 为下一轮准备
        
        调用时机：每轮结束后（所有玩家 Pass 后）
        """
        
        # ========== 1. 检查是否有行动记录 ==========
        if self.current_round not in self.decision_history or not self.decision_history[self.current_round]:
            print(f"⚠️ 第 {self.current_round} 轮无行动记录，跳过汇总")
            return
        
        actions = self.decision_history[self.current_round]
        
        # ========== 2. 构建行动历史文本 ==========
        action_history_text = "\n".join([
            f"  行动 #{i+1}: 选择行动 #{a['action_id']} - {a['reason']} (置信度 {a['confidence']*100:.0f}%)"
            for i, a in enumerate(actions)
        ])
        
        # ========== 3. 构建总结提示词 ==========
        summary_prompt = f"""
            你是《Age of Innovation》策略顾问。请简要总结第 {self.current_round} 轮的所有行动，并以此给出下轮指导。

            【第 {self.current_round} 轮行动历史】
            {action_history_text}

            【任务】
            1. 用 100-150 字总结本轮核心策略和执行情况
            2. 用 40-80 字总结获取的从能力/高科板块带来的（如有）、持续的行动效果（这会影响未来的行动决策）
            3. 用 50-100 字给出第 {self.current_round + 1} 轮的策略建议

            【输出格式】
            直接返回纯文本，不要 JSON 格式。格式如下：
            本轮总结：你的总结内容
            行动效果：你的能力/高科板块行动效果汇总（如有）
            下轮建议：你的建议内容
        """
        
        # ========== 4. 调用模型生成总结 ==========
        try:
            response = dashscope.MultiModalConversation.call(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是 Age of Innovation 策略专家，擅长总结决策历史并给出策略建议。"},
                    {"role": "user", "content": summary_prompt}
                ],
                result_format="message",
                stream=False,
                enable_thinking=True
            )
            
            if response.status_code == HTTPStatus.OK:
                # 提取模型返回的总结内容
                content = response.output.choices[0].message.get("content", "")
                
                # ========== 5. 存入轮次摘要 ==========
                self.round_summaries[self.current_round] = content
                
                print(f"📋 第 {self.current_round} 轮汇总完成（模型生成）")
                print(f"   总结：{content[:80]}...")
            else:
                raise Exception(f"API 调用失败：{response.code} - {response.message}")
                
        except Exception as e:
            # 模型调用失败，使用备用方案（简单拼接）
            print(f"⚠️ 模型总结失败，使用备用方案：{e}")
            
            action_summary = "\n".join([
                f"行动 #{i+1}: 选择行动 #{a['action_id']} (置信度 {a['confidence']*100:.0f}%)"
                for i, a in enumerate(actions)
            ])
            
            backup_summary = (
                f"第 {self.current_round} 轮共执行 {len(actions)} 个行动。\n"
                f"{action_summary}\n"
                f"整体策略：{actions[0]['reason'][:100] if actions else '无'}..."
            )
            
            self.round_summaries[self.current_round] = backup_summary
 
    # ========== 步骤 4: 构建用户 prompt ==========
    def _build_user_prompt(self) -> str:
        """【步骤 4】构建用户提示词（每次行动动态生成）"""
        # 格式化行动列表
        actions_formatted = "\n".join([
            f"  - 行动 #{aid}: {desc}" 
            for aid, desc in self.available_actions.items()
        ])
        
        # 添加合法行动 ID 列表（强化约束）
        valid_ids_str = ", ".join(map(str, self.valid_action_ids))
        
        return f"""
            当前轮次：第 {self.current_round} 轮

            当前可用行动：
            {actions_formatted}

            当前游戏状态：
            {self.game_state}

            请分析局势并选择最佳行动。

            ⚠️ 约束提醒：
            - action_id 必须是整数：[{valid_ids_str}]
            - 必须调用 select_action_id 工具输出决策
            - reason 需结合当前轮次目标、资源情况、派系能力分析，并为后续决策提供参考
        """

    # ========== 步骤 5.1: 调用模型 ==========
    def _call_model(self, force_final: bool = False) -> Dict:
        """
        【步骤 5.1】调用 DashScope 模型
        
        参数:
            force_final: 是否强制调用 select_action_id 工具（用于最后一轮）
        
        返回:
            assistant message 字典（含 content 和/或 tool_calls）
        """
        
        # 🔥 关键：使用 tool_choice 强制调用最终决策工具
        if force_final:
            tool_choice = {
                "type": "function",
                "function": {"name": "select_action_id"}
            }
            enable_thinking = False
        else:
            tool_choice = "auto"  # 让模型自行决定是否调用工具
            enable_thinking = True
        
        response = dashscope.MultiModalConversation.call(
            model=self.model,  # ✅ 使用实例配置的模型
            messages=self.messages,  # ✅ 使用实例的 messages
            tools=self.tools,  # ✅ 使用实例的 tools
            tool_choice=tool_choice,  # 🔥 强制/自动选择
            enable_thinking=enable_thinking,
            result_format="message",
        )
        
        # 状态码检查
        if response.status_code != HTTPStatus.OK:
            raise Exception(f"API 调用失败：{response.code} - {response.message}")
        
        # 提取 assistant message
        assistant_msg = response.output.choices[0].message

        # 如果是 Message 对象，转换为字典
        if hasattr(assistant_msg, '__dict__'):
            assistant_msg = {
                "role": "assistant",
                "content": assistant_msg.content if hasattr(assistant_msg, 'content') else [],
                "tool_calls": assistant_msg.tool_calls if hasattr(assistant_msg, 'tool_calls') else None,
            }
            # 清理 None 值
            assistant_msg = {k: v for k, v in assistant_msg.items() if v is not None}
        
        return assistant_msg
    
    # ========== 步骤 5.2: 检查工具调用 ==========
    def _check_tool_calls(self, assistant_msg: Dict, force_final: bool) -> bool:
        """
        【步骤 5.2】检查是否有工具调用
        
        参数:
            assistant_msg: 模型返回的 assistant message
            force_final: 是否最后一轮（强制要求工具调用）
        
        返回:
            True: 有工具调用 或 非最后一轮允许继续
            False: 最后一轮无工具调用，需要重试
        
        抛出:
            Exception: 最后一轮仍无工具调用，直接抛出异常
        """
        
        has_tool_calls = bool(assistant_msg.get("tool_calls"))
        
        # 🔥 最后一轮：强制要求工具调用，无工具则直接抛异常
        if force_final and not has_tool_calls:
            raise Exception("最后一轮模型仍未调用任何工具，无法输出决策")
        
        # ✅ 有工具调用：继续处理
        if has_tool_calls:
            return True
        
        # ⚠️ 前几轮无工具调用：允许仅分析，将分析内容加入上下文，鼓励下一轮调用工具
        content = assistant_msg.get("content", "")
        if content:
            self.messages.append({  # ✅ 使用 self.messages
                "role": "user",
                "content": (
                    f"收到你的分析：'{content[:300]}...'。\n\n"
                    f"建议：你可以调用以下工具进一步验证你的分析：\n"
                    f"- query_game_rule: 查询不确定的规则细节\n"
                    f"- evaluate_action_cost: 评估特定行动的资源成本和收益\n"
                    f"分析完成后，请调用 select_action_id 输出最终决策。"
                )
            })
        
        return True  # 非最后一轮，允许继续下一轮迭代

    # ========== 步骤 5.3: 处理并行工具调用 ==========
    def _process_tool_calls(self, assistant_msg: Dict) -> tuple[bool, List[Dict]]:
        """
        【步骤 5.3】处理并行工具调用
        
        参数:
            assistant_msg: 模型返回的 assistant message
        
        返回:
            (has_final_decision, tool_results)
            - has_final_decision: 是否包含最终决策工具 select_action_id
            - tool_results: 所有工具的执行结果列表
        """
        tool_calls = assistant_msg.get("tool_calls", [])
        
        if not tool_calls:
            return False, []
        
        has_final_decision = False
        tool_results = []
        
        # 🔥 遍历所有 tool_calls（支持并行调用）
        for tool_call in tool_calls:

            func_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call.get("id")
            
            print(f"🔧 调用工具：{func_name} | 参数：{arguments}")
            
            # 🎯 检查是否是最终决策工具
            if func_name == "select_action_id":
                has_final_decision = True
                # 🔥 最终决策工具也需要添加 tool 响应（否则 API 会报错）
                self.messages.append({  # ✅ 使用 self.messages
                    "role": "tool",
                    "content": "决策已接收，将执行行动。",
                    "tool_call_id": tool_call_id
                })
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "func_name": func_name,
                    "arguments": arguments,
                    "is_final": True
                })
            
            else:
                # 🔍 查询类工具：执行并返回结果
                if func_name in self.tools_registry:  # ✅ 使用 self.tools_registry
                    try:
                        result = self.tools_registry[func_name](arguments)
                        print(f"📦 工具返回：{result[:100]}...")
                    except Exception as e:
                        result = f"工具执行错误：{str(e)}"
                        print(f"❌ 工具错误：{e}")
                else:
                    result = f"❌ 未知工具：{func_name}"
                
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "func_name": func_name,
                    "arguments": arguments,
                    "is_final": False,
                    "result": result
                })
                
                # 将工具响应添加到消息历史（供模型下一轮参考）
                self.messages.append({  # ✅ 使用 self.messages
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call_id
                })
        
        return has_final_decision, tool_results

    # ========== 步骤 5.4: 检查最终决策 ==========
    def _check_final_decision(self, tool_results: List[Dict]) -> Optional[Dict]:
        """
        【步骤 5.4】检查是否包含最终决策工具 select_action_id
        
        参数:
            tool_results: 工具执行结果列表（来自 5.3）
        
        返回:
            最终决策的 arguments 字典（包含 action_id, reason, confidence）
            或 None（如果没有找到最终决策工具）
        """
        for tool_result in tool_results:
            
            if tool_result.get("is_final") and tool_result["func_name"] == "select_action_id":
                return tool_result["arguments"]

        return None

    # ========== 步骤 5.5: 验证并返回 ==========
    def _validate_and_return(self, final_decision: Dict) -> Optional[Dict]:
        """
        【步骤 5.5】验证最终决策并返回
        
        参数:
            final_decision: select_action_id 工具的 arguments 字典
        
        返回:
            验证通过的决策字典 {"action_id": int, "reason": str, "confidence": float}
            或 None（验证失败）
        
        抛出:
            ValueError: 验证失败时抛出具体错误信息
        """
        
        # ========== 1. 提取字段 ==========
        action_id = final_decision.get("action_id")
        reason = final_decision.get("reason")
        confidence = final_decision.get("confidence")
        
        # ========== 2. 字段存在性验证 ==========
        if action_id is None:
            raise ValueError("缺少必需字段：action_id")
        
        if not reason or not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason 必须是非空字符串")
        
        if confidence is None:
            raise ValueError("缺少必需字段：confidence")
        
        # ========== 3. 类型验证 ==========
        if not isinstance(action_id, int):
            # 尝试转换（模型可能返回字符串 "1" 而不是整数 1）
            try:
                action_id = int(action_id)
            except (ValueError, TypeError):
                raise ValueError(f"action_id 必须是整数，收到：{type(action_id).__name__}")
        
        if not isinstance(confidence, (int, float)):
            raise ValueError(f"confidence 必须是数值，收到：{type(confidence).__name__}")
        
        # ========== 4. 业务逻辑验证 ==========
        if action_id not in self.valid_action_ids:  # ✅ 使用 self.valid_action_ids
            raise ValueError(
                f"非法 action_id: {action_id}，必须是 {self.valid_action_ids} 之一"
            )
        
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(
                f"confidence 必须在 0.0-1.0 范围内，收到：{confidence}"
            )
        
        # ========== 5. 验证通过，返回标准化结果 ==========
        result = {
            "action_id": action_id,
            "reason": reason.strip(),
            "confidence": float(confidence)
        }
        
        print(f"✅ 决策验证通过:")
        print(f"   行动 ID: {action_id}")
        print(f"   理由：{reason[:80]}{'...' if len(reason) > 80 else ''}")
        print(f"   置信度：{confidence*100:.0f}%")
        
        return result
    
    # ========== 步骤 5.6: 生成该行动摘要（剔除本轮分析过程） ==========
    def _generate_action_summary(self, decision_result: Dict):
        """
        【步骤 5.6】生成该轮决策摘要
        
        功能：
        1. 清理本轮行动中产生的详细对话记录（至多 3 次循环的 user/assistant/tool 消息）
        2. 仅保留 select_action_id 的选择和理由作为该行动的决策记录
        3. 将决策记录存入 self.decision_history[self.current_round]
        4. 重建上下文：system + 历史轮次摘要 + 当前轮次已完成的行动记录
        
        参数:
            decision_result: 决策结果 {"action_id": int, "reason": str, "confidence": float}
        """
        
        # ========== 1. 提取决策信息 ==========
        action_id = decision_result.get("action_id")
        reason = decision_result.get("reason", "")
        confidence = decision_result.get("confidence", 0.0)
        
        # 截取理由前 150 字（避免行动记录过长）
        reason_short = reason[:150] + "..." if len(reason) > 150 else reason
        
        # ========== 2. 存入当前轮次的行动历史 ==========
        action_record = {
            "action_id": action_id,
            "reason": reason_short,
            "confidence": confidence
        }
        
        self.decision_history[self.current_round].append(action_record)
        
        print(f"📝 第 {self.current_round} 轮 - 行动 #{len(self.decision_history[self.current_round])} 已记录")
        
        # ========== 3. 重建上下文 ==========
        # 保留 system 消息
        system_msgs = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # 构建历史轮次摘要消息（所有已完成的轮次）
        round_summary_msgs = []
        for round_idx in range(self.current_round):
            round_summary_msgs.append({
                "role": "user",
                "content": f"【第 {round_idx} 轮决策汇总】{self.round_summaries[round_idx]}"
            })
        
        # 构建当前轮次已完成的行动记录消息
        current_round_action_msgs = []
        action_text = "\n".join([
            f"  - 行动 #{i+1}: 选择行动 #{a['action_id']} ({a['reason'][:50]}...)"
            for i, a in enumerate(self.decision_history[self.current_round])
        ])
        current_round_action_msgs.append({
            "role": "user",
            "content": f"【第 {self.current_round} 轮已执行行动】\n{action_text}"
        })
        
        # 重建 messages：system + 历史轮次摘要 + 当前轮次行动记录
        self.messages = system_msgs + round_summary_msgs + current_round_action_msgs
    
    # ========== 步骤 5.7: 错误处理 ==========
    def _handle_error(self, e: Exception, attempt: int) -> bool:
        """
        【步骤 5.6】错误处理
        
        参数:
            e: 捕获的异常对象
            attempt: 当前重试次数（从 0 开始）
        
        返回:
            True: 应该继续重试
            False: 应该放弃并进入 fallback
        """
        
        error_msg = str(e)
        is_last_attempt = (attempt >= self.MAX_RETRIES - 1)  # ✅ 使用 self.MAX_RETRIES
        
        # ========== 记录错误日志 ==========
        print(f"\n❌ 错误 (第 {attempt + 1}/{self.MAX_RETRIES} 次尝试): {error_msg}")
        
        # ========== 分类处理不同类型的错误 ==========
        
        # 1. API 调用失败（网络问题、限流等）
        if "API" in error_msg or "status_code" in error_msg or "network" in error_msg.lower():
            print("   → 类型：API 调用失败，建议重试")
            if not is_last_attempt:
                self.messages.append({  # ✅ 使用 self.messages
                    "role": "user",
                    "content": "上一轮响应因技术问题失败，请重新分析并调用 select_action_id 工具。"
                })
                return True  # 继续重试
        
        # 2. JSON 解析失败（模型输出格式错误）
        elif "JSON" in error_msg or "json" in error_msg.lower():
            print("   → 类型：JSON 解析失败，要求模型修正格式")
            if not is_last_attempt:
                self.messages.append({  # ✅ 使用 self.messages
                    "role": "user",
                    "content": (
                        "你的响应格式有误，无法解析。请重新调用 select_action_id 工具，确保：\n"
                        f"- action_id 是整数且属于 {self.valid_action_ids}\n"
                        "- reason 是非空字符串\n"
                        "- confidence 是 0.0-1.0 的数值\n"
                        "- 输出必须是合法的 JSON 格式"
                    )
                })
                return True  # 继续重试
        
        # 3. 验证失败（action_id 不合法、字段缺失等）
        elif "验证" in error_msg or "ValueError" in str(type(e).__name__):
            print("   → 类型：数据验证失败，要求模型修正内容")
            if not is_last_attempt:
                self.messages.append({  # ✅ 使用 self.messages
                    "role": "user",
                    "content": (
                        f"决策验证失败：{error_msg}\n\n"
                        f"请重新调用 select_action_id 工具，确保：\n"
                        f"- action_id 必须是 {self.valid_action_ids} 中的一个整数\n"
                        "- reason 必须是非空字符串，结合当前游戏状态分析\n"
                        "- confidence 必须是 0.0-1.0 的数值\n"
                        "- 这是最后一轮，必须输出有效决策"
                    )
                })
                return True  # 继续重试
        
        # 4. 模型未调用工具（最后一轮）
        elif "未调用任何工具" in error_msg:
            print("   → 类型：模型未调用工具，已到最后一次尝试")
            return False  # 放弃重试，进入 fallback
        
        # 5. 未知错误
        else:
            print(f"   → 类型：未知错误，尝试最后一次重试")
            if not is_last_attempt:
                self.messages.append({  # ✅ 使用 self.messages
                    "role": "user",
                    "content": f"处理过程中出现错误：{error_msg}。请重新分析并调用 select_action_id 工具输出决策。"
                })
                return True  # 继续重试
        
        # 最后一次尝试仍失败
        print("   → 已达到最大重试次数，将进入 fallback 默认决策")
        return False  # 放弃重试
    
    # ========== 步骤 6: Fallback ==========
    def _fallback(self) -> Dict:
        """
        【步骤 6】Fallback 默认决策
        
        当所有重试都失败时，返回一个安全的默认决策，确保游戏可以继续进行。
        
        返回:
            {"action_id": int, "reason": str, "confidence": float}
        """
        
        # ========== 选择默认行动 ID ==========
        # 策略：选择第一个合法行动 ID（最安全）
        default_action_id = self.valid_action_ids[0] if self.valid_action_ids else 1  # ✅ 使用 self.valid_action_ids
        
        # ========== 构建默认理由 ==========
        default_reason = (
            "⚠️ AI 决策系统多次尝试失败，使用默认行动。"
            "建议人工审查当前游戏状态，确认此行动是否合适。"
            f"可选行动 ID 范围：{self.valid_action_ids}"
        )
        
        # ========== 返回默认决策 ==========
        result = {
            "action_id": default_action_id,
            "reason": default_reason,
            "confidence": 0.0  # 置信度为 0，表示这是 fallback 决策
        }
        
        print(f"\n⚠️ Fallback 默认决策:")
        print(f"   行动 ID: {default_action_id}")
        print(f"   理由：{default_reason[:80]}...")
        print(f"   置信度：0%")
        
        return result
    
    # ==================== 实用方法 ====================
    def get_decision_history(self) -> List[Dict]:
        """获取决策历史记录"""
        pass
    
    def get_round_summaries(self) -> List[Dict]:
        """获取轮次摘要历史"""
        pass
    
# ========== 使用示例（类写法） ==========
if __name__ == "__main__":
    # ========== 1. 实例化 AI 顾问 ==========
    ai = AIAssistant(player_id= 0)
    
    # ========== 2. 第 1 轮决策 ==========
    print("\n" + "="*50)
    print("第 1 轮决策")
    print("="*50)
    
    available_actions_r1 = {
        1: "Terraform + Build Workshop (花费 2 Spades + 1 Tool + 2 Coins)",
        2: "Upgrade Workshop to Guild (花费 2 Tools + 3 Coins，有相邻对手)",
        3: "Send Scholar to Engineering (花费 1 Scholar)",
    }
    
    game_state_r1 = """
    - 当前轮次：Round 1
    - 派系：Moles (工程 +2, 可 Tunneling)
    - Round Score: 建造工坊 +2 分
    - 资源：8 Coins, 5 Tools, 2 Scholars
    - 地图：已有 2 个相邻工坊
    - 科技：Engineering Level 2
    """
    
    result_r1 = ai.decide(
        available_actions=available_actions_r1,
        game_state=game_state_r1,
        current_round=1
    )
    
    if result_r1:
        print(f"\n✅ 决策：行动 #{result_r1['action_id']}")
        print(f"💡 理由：{result_r1['reason']}")
        print(f"📊 置信度：{result_r1['confidence']*100:.0f}%")
    
    # ========== 3. 第 2 轮决策（上下文自动连贯） ==========
    print("\n" + "="*50)
    print("第 2 轮决策")
    print("="*50)
    
    available_actions_r2 = {
        1: "Terraform + Build Workshop (花费 1 Spade + 1 Tool + 2 Coins)",
        2: "Upgrade Workshop to Guild (花费 2 Tools + 6 Coins)",
        3: "Increase Sailing (花费 1 Scholar + 4 Coins)",
        4: "Power Action: Gain 3 Power (花费 3 Power from Bowl III)",
    }
    
    game_state_r2 = """
    - 当前轮次：Round 2
    - 派系：Moles
    - Round Score: 建造工坊 +2 分
    - 资源：6 Coins, 4 Tools, 1 Scholar
    - 地图：已有 3 个工坊，1 个相邻对手
    - 科技：Engineering Level 2
    - 上轮行动：执行了行动 #1（建造工坊）
    """
    
    result_r2 = ai.decide(
        available_actions=available_actions_r2,
        game_state=game_state_r2,
        current_round=2
    )
    
    if result_r2:
        print(f"\n✅ 决策：行动 #{result_r2['action_id']}")
        print(f"💡 理由：{result_r2['reason']}")
        print(f"📊 置信度：{result_r2['confidence']*100:.0f}%")
    