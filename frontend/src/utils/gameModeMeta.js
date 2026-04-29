export const GAME_MODE_OPTIONS = Object.freeze([
  {
    value: 'standard',
    name: '标准模式',
    desc: '45min 基础时间 + 45s 读秒\n超时采用随机 · 经快速行动优化',
    icon: 'fas fa-chess',
  },
  {
    value: 'quick',
    name: '快速模式',
    desc: '25min 基础时间 + 25s 读秒\n超时采用随机 · 经快速行动优化',
    icon: 'fas fa-bolt',
  },
  {
    value: 'custom',
    name: '自定义',
    desc: '自由配置各项参数',
    icon: 'fas fa-cogs',
  },
])

export function getGameModeMeta(mode) {
  return GAME_MODE_OPTIONS.find((item) => item.value === mode) || null
}

export function getGameModeIcon(mode) {
  return getGameModeMeta(mode)?.icon || 'fas fa-gamepad'
}

export function getGameModeName(mode) {
  return getGameModeMeta(mode)?.name || mode
}
