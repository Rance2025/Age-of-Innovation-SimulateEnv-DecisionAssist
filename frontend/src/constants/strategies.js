/**
 * 策略配置常量
 * 
 * 集中管理所有策略数据，供 StrategyPickerModal 和其他组件共享使用
 */

// 策略分组配置
export const STRATEGY_GROUPS = Object.freeze([
  {
    id: 'random',
    label: '随机策略',
    icon: 'fas fa-dice',
    description: '基于随机算法的策略',
    options: [
      {
        id: 'random_pure',
        label: '完全随机',
        description: '在所有可用行动中均匀随机选择',
        icon: 'fas fa-shuffle'
      },
      {
        id: 'random_fast_action',
        label: '快速随机',
        description: '优先选择可快速执行的行动',
        icon: 'fas fa-bolt'
      },
      {
        id: 'random_weighted',
        label: '加权随机',
        description: '根据权重偏向更优行动',
        icon: 'fas fa-scale-balanced'
      },
      {
        id: 'random_placeholder_1',
        label: '占位策略 1',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_2',
        label: '占位策略 2',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_3',
        label: '占位策略 3',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_4',
        label: '占位策略 4',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_5',
        label: '占位策略 5',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_6',
        label: '占位策略 6',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_7',
        label: '占位策略 7',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_8',
        label: '占位策略 8',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_9',
        label: '占位策略 9',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_10',
        label: '占位策略 10',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_11',
        label: '占位策略 11',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      },
      {
        id: 'random_placeholder_12',
        label: '占位策略 12',
        description: '预留策略位置，待后续实现',
        icon: 'fas fa-circle'
      }
    ]
  },
  {
    id: 'metric',
    label: '指标策略',
    icon: 'fas fa-chart-line',
    description: '基于指标计算的策略',
    options: [
      {
        id: 'metric_single_step_best',
        label: '单步最优',
        description: '计算当前步骤的最优解',
        icon: 'fas fa-calculator'
      }
    ]
  },
  {
    id: 'ai',
    label: 'AI 策略',
    icon: 'fas fa-robot',
    description: '基于人工智能的策略',
    options: [
      {
        id: 'ai_llm_reasoning',
        label: 'LLM 推理',
        description: '使用大语言模型进行推理决策',
        icon: 'fas fa-brain'
      }
    ]
  }
])

// 所有策略选项的扁平列表（包含分组信息）
export const STRATEGY_OPTIONS = Object.freeze(
  STRATEGY_GROUPS.flatMap((group) =>
    group.options.map((strategy) => ({
      ...strategy,
      groupId: group.id,
      groupLabel: group.label
    }))
  )
)

// 当前支持的后端策略ID
export const SUPPORTED_STRATEGY_IDS = Object.freeze(new Set([
  'random_pure',
  'random_fast_action'
]))

// 获取策略图标
export function getStrategyIcon(strategyId) {
  const strategy = STRATEGY_OPTIONS.find(s => s.id === strategyId)
  return strategy?.icon || 'fas fa-chess-pawn'
}

// 获取策略名称
export function getStrategyLabel(strategyId) {
  const strategy = STRATEGY_OPTIONS.find(s => s.id === strategyId)
  return strategy?.label || '未知策略'
}
