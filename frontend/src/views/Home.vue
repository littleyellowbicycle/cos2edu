<template>
  <div class="home">
    <header class="hero">
      <div class="hero-content">
        <div class="hero-ornament">❧</div>
        <h1 class="hero-title">苏格拉底</h1>
        <p class="hero-subtitle">AI 教学系统</p>
        <p class="hero-description">
          通过苏格拉底式提问法，探索知识的本质。<br>
          与 AI 角色对话，在思考中领悟真理。
        </p>
        <div class="hero-actions">
          <router-link to="/characters" class="btn btn-primary">开始探索</router-link>
          <router-link to="/dashboard" class="btn btn-secondary">学习中心</router-link>
        </div>
      </div>
      <div class="hero-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </header>

    <section class="features">
      <div class="features-grid">
        <div class="feature-card" @click="$router.push('/characters')">
          <div class="feature-icon">◈</div>
          <h3>角色管理</h3>
          <p>创建和管理 AI 教学角色，每个角色都有独特的性格和背景</p>
          <span class="feature-arrow">→</span>
        </div>
        <div class="feature-card" @click="$router.push('/materials')">
          <div class="feature-icon">◇</div>
          <h3>教材中心</h3>
          <p>整理和导入教学材料，让 AI 基于教材进行个性化教学</p>
          <span class="feature-arrow">→</span>
        </div>
        <div class="feature-card" @click="$router.push('/conversations')">
          <div class="feature-icon">○</div>
          <h3>对话历史</h3>
          <p>保存和回顾所有对话记录，在历史中汲取智慧</p>
          <span class="feature-arrow">→</span>
        </div>
        <div class="feature-card" @click="$router.push('/settings')">
          <div class="feature-icon">⚙</div>
          <h3>设置</h3>
          <p>配置 AI 模型和 API Key，确保对话功能正常运行</p>
          <span class="feature-arrow">→</span>
        </div>
        <div class="feature-card" @click="$router.push('/editor')">
          <div class="feature-icon"></div>
          <h3>内容编辑器</h3>
          <p>可视化编辑课程大纲、角色配置和世界观设定 YAML</p>
          <span class="feature-arrow">→</span>
        </div>
        <div class="feature-card" @click="$router.push('/dashboard')">
          <div class="feature-icon">📊</div>
          <h3>学习中心</h3>
          <p>查看学习进度、掌握度分析和薄弱环节</p>
          <span class="feature-arrow">→</span>
        </div>
      </div>
    </section>

    <footer class="home-footer">
      <p class="quote">"我唯一知道的，就是我一无所知。" — 苏格拉底</p>
    </footer>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home {
  min-height: 100vh;
  background: var(--color-bg);
}

.hero {
  position: relative;
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px;
  overflow: hidden;
  background: linear-gradient(180deg, var(--color-bg-warm) 0%, var(--color-bg) 100%);
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
  max-width: 680px;
  animation: fadeInUp 1s ease-out;
}

.hero-ornament {
  font-size: 48px;
  color: var(--color-accent);
  margin-bottom: 24px;
  opacity: 0.8;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(56px, 10vw, 96px);
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: -0.02em;
  line-height: 1;
  margin-bottom: 8px;
}

.hero-subtitle {
  font-family: var(--font-display);
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 400;
  font-style: italic;
  color: var(--color-accent);
  margin-bottom: 32px;
  letter-spacing: 0.05em;
}

.hero-description {
  font-size: 18px;
  line-height: 1.8;
  color: var(--color-text-muted);
  margin-bottom: 48px;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  padding: 16px 36px;
  border-radius: 4px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.03em;
}

.btn-primary {
  background: var(--color-ink);
  color: white;
  border: 2px solid var(--color-ink);
}

.btn-primary:hover {
  background: var(--color-accent);
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background: transparent;
  color: var(--color-ink);
  border: 2px solid var(--color-border);
}

.btn-secondary:hover {
  border-color: var(--color-ink);
  transform: translateY(-2px);
}

.hero-decoration {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  pointer-events: none;
  z-index: 1;
}

.circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  opacity: 0.5;
}

.circle-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -50px;
  left: -50px;
  animation: float 10s ease-in-out infinite reverse;
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  left: 60%;
  animation: float 6s ease-in-out infinite;
}

.features {
  padding: 80px 40px;
  background: var(--color-surface);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  position: relative;
  padding: 40px 32px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--color-accent);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-accent-light);
}

.feature-icon {
  font-size: 32px;
  color: var(--color-accent);
  margin-bottom: 20px;
}

.feature-card h3 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: 12px;
}

.feature-card p {
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-muted);
}

.feature-arrow {
  display: inline-block;
  margin-top: 20px;
  font-size: 20px;
  color: var(--color-accent);
  transition: transform 0.3s ease;
}

.feature-card:hover .feature-arrow {
  transform: translateX(8px);
}

.home-footer {
  padding: 60px 40px;
  text-align: center;
  background: var(--color-bg);
}

.quote {
  font-family: var(--font-display);
  font-size: 20px;
  font-style: italic;
  color: var(--color-text-muted);
  max-width: 600px;
  margin: 0 auto;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(20px, -20px);
  }
}

@media (max-width: 768px) {
  .hero {
    padding: 40px 24px;
  }
  
  .features {
    padding: 60px 24px;
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .btn {
    width: 100%;
    max-width: 280px;
  }
}
</style>