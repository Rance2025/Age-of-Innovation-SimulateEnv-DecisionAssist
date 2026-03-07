import os
import dashscope
import json
from typing import Dict, List, Optional
from http import HTTPStatus

def ai_assistant(
    available_actions: Dict[int, str],
    game_state: str,
    max_retries: int = 3
) -> Optional[Dict]:
    """
    Age of Innovation AI 策略顾问
    
    参数:
        available_actions: {行动ID: 行动描述} 字典
        game_state: 当前游戏状态描述
        max_retries: 最大重试次数
    
    返回:
        {"action_id": int, "reason": str, "confidence": float} 或 None
    """
    
    # ========== 配置 ==========
    dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
    dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
    
    valid_action_ids = list(available_actions.keys())
    
    # ========== 步骤1: 定义工具列表 ==========
    tools = _define_tools(valid_action_ids)
    
    # ========== 步骤2: 定义工具执行函数 ==========
    tools_registry = _build_tools_registry(available_actions, game_state)
    
    # ========== 步骤3: 构建系统提示词 ==========
    system_prompt = _build_system_prompt(available_actions, game_state, valid_action_ids, max_retries)
    
    # ========== 步骤4: 初始化对话历史 ==========
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "请分析局势并选择最佳行动。"}
    ]
    
    # ========== 步骤5: 主循环 - 处理工具调用 ==========
    for attempt in range(max_retries):
        try:
            # 5.1 调用模型
            # 判断是否强制调用最终决策工具
            # 最后一次重试时强制调用 select_action_id，避免无限循环
            force_final = (attempt == max_retries - 1)
            assistant_msg = _call_model(messages, tools, force_final=force_final)
            messages.append(assistant_msg)
            
            # 🔥 5.2 检查是否有工具调用（最后一轮无工具直接抛异常）
            if not _check_tool_calls(assistant_msg, messages, force_final=force_final):
                continue  # 非最后一轮无工具，继续下一轮
            
            # 🔥 5.3 处理并行工具调用
            has_final_decision, tool_results = _process_tool_calls(
                assistant_msg, messages, tools_registry
            )
            
            # 🔥 5.4 检查是否包含最终决策工具
            has_final_decision = _check_final_decision(tool_results)
            
            if has_final_decision:
                # 🔥 5.5 验证并返回最终决策
                result = _validate_and_return(has_final_decision, valid_action_ids)
                return result  # ✅ 验证通过，返回结果
            else:
                print("🔄 继续分析...")
                continue
                
        except Exception as e:
            # 🔥 5.6 错误处理
            should_retry = _handle_error(e, attempt, max_retries, messages, valid_action_ids)
            if not should_retry:
                break  # 放弃重试，进入 fallback
            continue
    
    # ========== 步骤6: 重试失败后的 fallback ==========
    return _fallback(valid_action_ids)


# ========== 辅助函数 ==========

# 步骤1
def _define_tools(valid_action_ids: List[int]) -> List[Dict]:
    """
    步骤 1: 定义工具 Schema（给 API 看的）
    
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
                            "description": f"行动 ID，必须是以下值之一：{valid_action_ids}",
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

# 步骤2
def _build_tools_registry(available_actions: Dict[int, str], game_state: str) -> Dict:
    """
    步骤 2: 定义工具执行函数注册表（本地代码执行的）
    
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
    
    def query_game_rule(arguments: Dict) -> str:
        """查询规则细节"""
        rule_topic = arguments.get("rule_topic", "")
        topic_display = rule_topic.replace("_", " ").title()
        
        rule_content = RULE_KNOWLEDGE.get(rule_topic, f"未找到关于 '{rule_topic}' 的规则信息。")
        
        return f"【规则查询：{topic_display}】\n{rule_content.strip()}"
    
    def evaluate_action_cost(arguments: Dict) -> str:
        """评估行动成本"""
        action_id = arguments.get("action_id")
        focus = arguments.get("focus", "all")
        action_desc = available_actions.get(action_id, "未知行动")
        
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
        analysis += f"当前游戏状态摘要：{game_state[:200]}...\n"
        
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

# 步骤3
def _build_system_prompt(
    available_actions: Dict[int, str], 
    game_state: str, 
    valid_action_ids: List[int],
    max_retries: int
) -> str:
    """
    步骤 3: 构建系统提示词
    
    参数:
        available_actions: {行动 ID: 行动描述} 字典
        game_state: 当前游戏状态描述
        valid_action_ids: 合法行动 ID 列表
    
    返回:
        系统提示词字符串
    """
    
    # 格式化行动列表
    actions_formatted = "\n".join([
        f"  - 行动 #{aid}: {desc}" 
        for aid, desc in available_actions.items()
    ])
    
    return f"""
        # 🎮 Role: Age of Innovation 策略大师

        你是一位精通桌游《Age of Innovation》（大创造时代）的顶级策略顾问。
        你熟悉游戏的所有核心机制：地形改造、Power 循环、建筑升级链、科学轨道、城市建立、12 派系能力、Innovation/Competency/Palace Tiles 选取等。

        # 📋 Current Available Actions（当前可用行动）
        {actions_formatted}

        # 📊 Current Game State（当前游戏状态）
        {game_state}

        # 🎯 Your Task（你的任务）
        根据当前游戏状态，从可用行动列表中选择**唯一最佳行动**，并通过调用 `select_action_id` 工具输出决策。

        #  Analysis Process（分析流程）
        在做出决策前，你可以（非强制）调用以下工具辅助分析（可以并行调用，但不能与`select_action_id`一同调用）：
        1. `query_game_rule` - 查询不确定的规则细节
        2. `evaluate_action_cost` - 评估特定行动的成本/收益/风险
        3. `analyze_game_state` - 分析当前游戏状态的关键指标

        **你有{max_retries}次循环调起的机会，但无论是否调用上述工具，最后一轮必须调用 `select_action_id` 输出最终决策（也可以提前，不一定要在最后一轮）。**

        # ⚠️ Constraints（必须遵守的约束）
        1. **最终输出必须调用 `select_action_id` 工具**，不能直接回复自然语言。
        2. `action_id` 必须是**整数**，且严格属于 {valid_action_ids} 中的一个。
        3. `reason` 必须结合以下因素给出分析（简要，150字左右）：
        - 当前 Round Score 目标（如有）
        - 资源存量与获取能力
        - 派系特殊能力
        - 长期战略（Area/Science/Resources 终局计分）
        - 相邻对手的影响（Power 获取/压制）
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

# 步骤5.1
def _call_model(messages: List[Dict], tools: List[Dict], force_final: bool = False) -> Dict:
    """
    步骤 5.1: 调用 DashScope 模型
    
    参数:
        messages: 对话历史
        tools: 工具定义列表
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
        model="qwen3.5-plus",  # ✅ 多模态模型，支持 tool calling
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,  # 🔥 强制/自动选择
        enable_thinking = enable_thinking,
        result_format="message",
        stream=False,  # ✅ 单次输出，非流式
    )
    
    # 状态码检查
    if response.status_code != HTTPStatus.OK:
        raise Exception(f"API 调用失败: {response.code} - {response.message}")
    
    # 提取 assistant message
    assistant_msg = response.output.choices[0].message
    
    return assistant_msg

# 步骤5.2
def _check_tool_calls(assistant_msg: Dict, messages: List[Dict], force_final: bool) -> bool:
    """
    步骤 5.2: 检查是否有工具调用
    
    参数:
        assistant_msg: 模型返回的 assistant message
        messages: 对话历史（用于追加提示）
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
        messages.append({
            "role": "user",
            "content": (
                f"收到你的分析：'{content[:20]}...'。\n\n"
                f"建议：你可以调用以下工具进一步验证你的分析：\n"
                f"- query_game_rule: 查询不确定的规则细节\n"
                f"- evaluate_action_cost: 评估特定行动的资源成本和收益\n"
                f"分析完成后，请调用 select_action_id 输出最终决策。"
            )
        })
    
    return True  # 非最后一轮，允许继续下一轮迭代

# 步骤5.3
def _process_tool_calls(
    assistant_msg: Dict, 
    messages: List[Dict], 
    tools_registry: Dict
) -> tuple[bool, List[Dict]]:
    """
    步骤 5.3: 处理并行工具调用
    
    参数:
        assistant_msg: 模型返回的 assistant message
        messages: 对话历史（用于追加工具响应）
        tools_registry: 工具执行函数注册表 {func_name: func}
    
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
        
        print(f"🔧 调用工具: {func_name} | 参数: {arguments}")
        
        # 🎯 检查是否是最终决策工具
        if func_name == "select_action_id":
            has_final_decision = True
            # 最终决策工具不执行，留待 5.4 验证
            tool_results.append({
                "tool_call_id": tool_call_id,
                "func_name": func_name,
                "arguments": arguments,
                "is_final": True
            })
        else:
            # 🔍 查询类工具：执行并返回结果
            if func_name in tools_registry:
                try:
                    result = tools_registry[func_name](arguments)
                    print(f"📦 工具返回: {result[:100]}...")
                except Exception as e:
                    result = f"工具执行错误: {str(e)}"
                    print(f"❌ 工具错误: {e}")
            else:
                result = f"❌ 未知工具: {func_name}"
            
            tool_results.append({
                "tool_call_id": tool_call_id,
                "func_name": func_name,
                "arguments": arguments,
                "is_final": False,
                "result": result
            })
            
            # 将工具响应添加到消息历史（供模型下一轮参考）
            messages.append({
                "role": "tool",
                "content": result,
                "tool_call_id": tool_call_id
            })
    
    return has_final_decision, tool_results

# 步骤5.4
def _check_final_decision(tool_results: List[Dict]) -> Optional[Dict]:
    """
    步骤 5.4: 检查是否包含最终决策工具 select_action_id
    
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

# 步骤5.5
def _validate_and_return(
    final_decision: Dict, 
    valid_action_ids: List[int]
) -> Optional[Dict]:
    """
    步骤 5.5: 验证最终决策并返回
    
    参数:
        final_decision: select_action_id 工具的 arguments 字典
        valid_action_ids: 合法行动 ID 列表
    
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
    if action_id not in valid_action_ids:
        raise ValueError(
            f"非法 action_id: {action_id}，必须是 {valid_action_ids} 之一"
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

# 步骤5.6
def _handle_error(
    e: Exception, 
    attempt: int, 
    max_retries: int, 
    messages: List[Dict], 
    valid_action_ids: List[int]
) -> bool:
    """
    步骤 5.6: 错误处理
    
    参数:
        e: 捕获的异常对象
        attempt: 当前重试次数（从 0 开始）
        max_retries: 最大重试次数
        messages: 对话历史（用于追加错误提示）
        valid_action_ids: 合法行动 ID 列表
    
    返回:
        True: 应该继续重试
        False: 应该放弃并进入 fallback
    """
    
    error_msg = str(e)
    is_last_attempt = (attempt >= max_retries - 1)
    
    # ========== 记录错误日志 ==========
    print(f"\n❌ 错误 (第 {attempt + 1}/{max_retries} 次尝试): {error_msg}")
    
    # ========== 分类处理不同类型的错误 ==========
    
    # 1. API 调用失败（网络问题、限流等）
    if "API" in error_msg or "status_code" in error_msg or "network" in error_msg.lower():
        print("   → 类型：API 调用失败，建议重试")
        if not is_last_attempt:
            messages.append({
                "role": "user",
                "content": "上一轮响应因技术问题失败，请重新分析并调用 select_action_id 工具。"
            })
            return True  # 继续重试
    
    # 2. JSON 解析失败（模型输出格式错误）
    elif "JSON" in error_msg or "json" in error_msg.lower():
        print("   → 类型：JSON 解析失败，要求模型修正格式")
        if not is_last_attempt:
            messages.append({
                "role": "user",
                "content": (
                    "你的响应格式有误，无法解析。请重新调用 select_action_id 工具，确保：\n"
                    f"- action_id 是整数且属于 {valid_action_ids}\n"
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
            messages.append({
                "role": "user",
                "content": (
                    f"决策验证失败：{error_msg}\n\n"
                    f"请重新调用 select_action_id 工具，确保：\n"
                    f"- action_id 必须是 {valid_action_ids} 中的一个整数\n"
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
            messages.append({
                "role": "user",
                "content": f"处理过程中出现错误：{error_msg}。请重新分析并调用 select_action_id 工具输出决策。"
            })
            return True  # 继续重试
    
    # 最后一次尝试仍失败
    print("   → 已达到最大重试次数，将进入 fallback 默认决策")
    return False  # 放弃重试

# 步骤6
def _fallback(valid_action_ids: List[int]) -> Dict:
    """
    步骤 6: Fallback 默认决策
    
    当所有重试都失败时，返回一个安全的默认决策，确保游戏可以继续进行。
    
    参数:
        valid_action_ids: 合法行动 ID 列表
    
    返回:
        {"action_id": int, "reason": str, "confidence": float}
    """
    
    # ========== 选择默认行动 ID ==========
    # 策略：选择第一个合法行动 ID（最安全）
    default_action_id = valid_action_ids[0]
    
    # ========== 构建默认理由 ==========
    default_reason = (
        "⚠️ AI 决策系统多次尝试失败，使用默认行动。"
        "建议人工审查当前游戏状态，确认此行动是否合适。"
        f"可选行动 ID 范围：{valid_action_ids}"
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


# ========== 使用示例（占位） ==========
if __name__ == "__main__":
    available_actions = {
        1: "Terraform + Build Workshop",
        2: "Upgrade Workshop to Guild",
        3: "Send Scholar to Engineering"
    }
    
    game_state = "Round 3, Moles faction, 8 Coins, 5 Tools..."
    
    result = ai_assistant(available_actions, game_state)
    
    if result:
        print(f"决策：行动 #{result['action_id']}")
        print(f"理由：{result['reason']}")