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
        label: '随机 · 完全',
        description: '在所有可用行动中均匀随机选择',
        icon: 'fas fa-shuffle',
        isAvailable: true
      },
      {
        id: 'random_fast_action',
        label: '随机 · 经快速行动优化',
        description: '优先选择可快速执行的行动',
        icon: 'fas fa-bolt',
        isAvailable: true
      },
      {
        id: 'random_weighted',
        label: '随机 · 加权',
        description: '根据权重偏向更优行动',
        icon: 'fas fa-scale-balanced',
        isAvailable: false
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
        icon: 'fas fa-calculator',
        isAvailable: false
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
        icon: 'fas fa-brain',
        isAvailable: false
      }
    ]
  }
])

// 当前支持的后端策略ID
export const SUPPORTED_STRATEGY_IDS = Object.freeze(new Set([
  'random_pure',
  'random_fast_action'
]))

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

// 前端可选的策略分组（显示所有策略，包括暂不可用的）
export const SELECTABLE_STRATEGY_GROUPS = Object.freeze(STRATEGY_GROUPS)

// 前端可选的策略选项的扁平列表
export const SELECTABLE_STRATEGY_OPTIONS = Object.freeze(
  SELECTABLE_STRATEGY_GROUPS.flatMap((group) =>
    group.options.map((strategy) => ({
      ...strategy,
      groupId: group.id,
      groupLabel: group.label
    }))
  )
)

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
