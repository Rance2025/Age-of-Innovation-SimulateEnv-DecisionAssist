<template>
  <div class="hero" @click="startGame">
    <div class="hero-content">
      <div class="hero-title">
        <span class="title-cn">大创造时代</span>
        <span class="title-divider"></span>
        <span class="title-en">Age of Innovation</span>
      </div>

      <p class="hero-description">
        在这个前所未有的创新纪元，策略与想象力交织，创造无限可能。我们正站在历史与未来的交汇点，每一次决策都将重塑世界。
      </p>

      <div class="hero-keywords">
        <span>探索</span>
        <span class="keyword-dot">•</span>
        <span>建造</span>
        <span class="keyword-dot">•</span>
        <span>征服</span>
      </div>

      <p class="hero-hint">
        点击任意位置开始游戏
      </p>
    </div>

    <!-- 背景装饰 -->
    <div class="hero-bg">
      <div class="bg-grid"></div>
      <div class="bg-glow"></div>
    </div>

    <!-- 浮动元素 -->
    <div class="floating-elements">
      <div class="float-item float-1"><i class="fas fa-cube"></i></div>
      <div class="float-item float-2"><i class="fas fa-coins"></i></div>
      <div class="float-item float-3"><i class="fas fa-user"></i></div>
      <div class="float-item float-4"><i class="fas fa-university"></i></div>
      <div class="float-item float-5"><i class="fas fa-city"></i></div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useGameStore } from '../stores/game'

defineOptions({
  name: 'HomeView'
})

const router = useRouter()
const gameStore = useGameStore()

function startGame() {
  if (gameStore.isPlaying) {
    router.push('/game')
  } else {
    router.push('/setup')
  }
}
</script>

<style scoped>
.hero {
  position: relative;
  width: 100%;
  height: calc(100vh - 56px);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}

.hero-content {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 80px 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 48px;
  max-width: 900px;
  width: 90%;
  margin-top: 100px;
  min-height: calc(100vh - 260px);
}

.hero-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  animation: fadeInUp 0.8s ease 0.2s both;
}

.title-cn {
  font-size: 7rem;
  font-weight: 600;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 12px;
  filter: drop-shadow(0 0 60px var(--accent-glow));
}

.title-en {
  font-size: 1.8rem;
  font-weight: 400;
  color: var(--text-secondary);
  letter-spacing: 10px;
  text-transform: uppercase;
}

.title-divider {
  width: 140px;
  height: 4px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  border-radius: 2px;
  box-shadow: 0 0 20px var(--accent), 0 0 40px var(--accent-glow);
  animation: pulse-glow 2s ease-in-out infinite;
}

.hero-description {
  font-size: 1.15rem;
  color: var(--text-secondary);
  line-height: 2;
  max-width: 700px;
  animation: fadeInUp 0.8s ease 0.4s both;
}

.hero-keywords {
  display: flex;
  align-items: center;
  gap: 20px;
  font-size: 1.3rem;
  color: var(--text-primary);
  letter-spacing: 6px;
  animation: fadeInUp 0.8s ease 0.5s both;
}

.keyword-dot {
  color: var(--accent-light);
  font-size: 1rem;
}

.hero-hint {
  font-size: 1rem;
  color: var(--text-secondary);
  opacity: 1;
  margin-top: 16px;
  animation: fadeInUp 0.8s ease 0.6s both, hint-pulse 4s ease-in-out infinite 2.4s;
}

/* 背景装饰 */
.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(0, 123, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 123, 255, 0.08) 1px, transparent 1px);
  background-size: 60px 60px;
  animation: gridMove 20s linear infinite;
}

.bg-glow {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  height: 500px;
  background: radial-gradient(ellipse at center, rgba(0, 123, 255, 0.25) 0%, rgba(0, 123, 255, 0.1) 40%, transparent 70%);
  opacity: 0.8;
  animation: pulse 4s ease-in-out infinite;
}

/* 浮动元素 */
.floating-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  pointer-events: none;
}

.float-item {
  position: absolute;
  font-size: 1.4rem;
  color: rgba(0, 123, 255, 0.35);
  animation: float 8s ease-in-out infinite;
  filter: drop-shadow(0 0 10px rgba(0, 123, 255, 0.3));
}

.float-1 { top: 18%; left: 12%; animation-delay: 0s; }
.float-2 { top: 28%; right: 18%; animation-delay: 1.5s; }
.float-3 { bottom: 32%; left: 18%; animation-delay: 3s; }
.float-4 { bottom: 22%; right: 12%; animation-delay: 4.5s; }
.float-5 { top: 55%; left: 8%; animation-delay: 6s; }

/* 响应式 */
@media (max-width: 768px) {
  .title-cn {
    font-size: 4rem;
    letter-spacing: 6px;
  }

  .title-en {
    font-size: 1.2rem;
    letter-spacing: 6px;
  }

  .title-divider {
    width: 100px;
    height: 3px;
  }

  .hero-description {
    font-size: 1rem;
    padding: 0 20px;
  }

  .hero-keywords {
    font-size: 1.1rem;
    gap: 16px;
  }

  .hero-content {
    padding: 40px 24px;
    gap: 32px;
  }
}
</style>
