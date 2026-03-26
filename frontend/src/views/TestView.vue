<template>
  <main class="test-page">
    <div class="test-container">
      <div class="test-header">
        <h1 class="test-title">游戏设置</h1>
        <p class="test-subtitle">配置你的对局参数，开始一场史诗般的文明之旅</p>
      </div>

      <form class="test-form" @submit.prevent="handleSubmit">
        <!-- 玩家数量设置 -->
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-users"></i>
            <span>玩家配置</span>
          </div>
          <div class="form-group">
            <label class="form-label">玩家数量</label>
            <div class="player-count-selector">
              <button
                v-for="count in [2, 3, 4, 5]"
                :key="count"
                type="button"
                class="count-btn"
                :class="{ active: form.playerCount === count }"
                @click="form.playerCount = count"
              >
                {{ count }}人
              </button>
            </div>
          </div>
        </div>

        <!-- 游戏模式设置 -->
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-gamepad"></i>
            <span>游戏模式</span>
          </div>
          <div class="form-group">
            <label class="form-label">选择模式</label>
            <div class="mode-selector">
              <div
                v-for="mode in gameModes"
                :key="mode.value"
                class="mode-card"
                :class="{ active: form.gameMode === mode.value }"
                @click="form.gameMode = mode.value"
              >
                <div class="mode-icon"><i :class="mode.icon"></i></div>
                <div class="mode-name">{{ mode.name }}</div>
                <div class="mode-desc">{{ mode.desc }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 高级选项 -->
        <div class="form-section">
          <div class="section-title">
            <i class="fas fa-sliders-h"></i>
            <span>高级选项</span>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label class="form-label">地图类型</label>
              <select class="form-select" v-model="form.mapType">
                <option value="random">随机地图</option>
                <option value="balanced">平衡地图</option>
                <option value="custom">自定义地图</option>
              </select>
            </div>
            <div class="form-group half">
              <label class="form-label">回合时限</label>
              <select class="form-select" v-model="form.turnTime">
                <option value="0">无限制</option>
                <option value="300">5分钟</option>
                <option value="600">10分钟</option>
                <option value="900">15分钟</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.enableAI">
              <span class="checkmark"></span>
              <span class="checkbox-text">启用AI助手</span>
            </label>
          </div>
        </div>

        <!-- 按钮区域 -->
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" @click="goBack">
            <i class="fas fa-arrow-left"></i>
            返回
          </button>
          <button type="submit" class="btn btn-primary">
            开始游戏
            <i class="fas fa-play"></i>
          </button>
        </div>
      </form>
    </div>
  </main>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'

const router = useRouter()
const gameStore = useGameStore()

const gameModes = [
  { value: 'standard', name: '标准模式', desc: '经典游戏规则，完整体验', icon: 'fas fa-chess' },
  { value: 'quick', name: '快速模式', desc: '缩短回合，快速对局', icon: 'fas fa-bolt' },
  { value: 'custom', name: '自定义', desc: '自由配置各项参数', icon: 'fas fa-cogs' }
]

const form = reactive({
  playerCount: 3,
  gameMode: 'standard',
  mapType: 'random',
  turnTime: '0',
  enableAI: false
})

function goBack() {
  // 返回Hero页时重置游戏状态，使导航栏显示"开始游戏"
  gameStore.resetGame()
  router.push('/')
}

function handleSubmit() {
  gameStore.setSettings({ ...form })
  gameStore.startGame()
  router.push('/game')
}
</script>

<style scoped>
.test-page {
  min-height: 100vh;
  padding-top: 80px;
  padding-bottom: 40px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  background: var(--bg-primary);
  position: relative;
}

.test-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(0, 123, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 123, 255, 0.02) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
}

.test-container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 0 24px;
  position: relative;
  z-index: 1;
}

.test-header {
  text-align: center;
  margin-bottom: 40px;
}

.test-title {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 12px;
}

.test-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
}

.test-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  transition: border-color 0.2s;
}

.form-section:hover {
  border-color: rgba(0, 123, 255, 0.3);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.section-title i {
  color: var(--accent);
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group.half {
  flex: 1;
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.player-count-selector {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.count-btn {
  flex: 1;
  min-width: 80px;
  padding: 12px 20px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.count-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.count-btn.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.mode-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}

.mode-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-card:hover {
  border-color: rgba(0, 123, 255, 0.5);
  transform: translateY(-2px);
}

.mode-card.active {
  border-color: var(--accent);
  background: rgba(0, 123, 255, 0.1);
}

.mode-icon {
  font-size: 2rem;
  color: var(--accent);
  margin-bottom: 12px;
}

.mode-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.mode-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.95rem;
  cursor: pointer;
  transition: border-color 0.2s;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23a0a0a0' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
}

.form-select:focus {
  outline: none;
  border-color: var(--accent);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 0;
}

.checkbox-label input {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checkmark::after {
  content: '\f00c';
  font-family: 'Font Awesome 6 Free';
  font-weight: 900;
  font-size: 12px;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.checkbox-label input:checked + .checkmark {
  background: var(--accent);
  border-color: var(--accent);
}

.checkbox-label input:checked + .checkmark::after {
  opacity: 1;
}

.checkbox-text {
  font-size: 0.95rem;
  color: var(--text-primary);
}

.form-actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 28px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-primary {
  background: var(--accent);
  color: white;
}

.btn-primary:hover {
  background: #0069d9;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

@media (max-width: 768px) {
  .test-title {
    font-size: 1.8rem;
  }

  .form-section {
    padding: 16px;
  }

  .form-row {
    flex-direction: column;
    gap: 16px;
  }

  .mode-selector {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
