<template>
  <header class="hero">
    <div class="hero-content">
      <div class="hero-ornament" aria-hidden="true">❧</div>
      <h1 class="hero-title">试问：何为生命的第一因？</h1>
      <div class="hero-actions">
        <router-link to="/characters" class="btn btn-primary">开始探索</router-link>
      </div>
    </div>
    <p class="hero-footnote">通过苏格拉底式提问法，探索知识的本质。与 AI 角色对话，在思考中领悟真理。</p>
    <div class="hero-decoration" aria-hidden="true">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </header>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 40px 80px;
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
  font-size: 100px;
  color: var(--color-accent);
  margin-bottom: 20px;
  opacity: 0.7;
  display: block;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(40px, 7vw, 60px);
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: -0.01em;
  line-height: 1.15;
  margin-bottom: 48px;
  white-space: nowrap;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  font-family: var(--font-body);
  font-size: 17px;
  font-weight: 600;
  text-decoration: none;
  padding: 18px 44px;
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

.hero-footnote {
  position: absolute;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
  font-size: 12px;
  color: var(--color-text-muted);
  opacity: 0.5;
  letter-spacing: 0.05em;
  text-align: center;
  white-space: nowrap;
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
    padding: 40px 24px 80px;
  }

  .hero-actions {
    flex-direction: column;
    align-items: center;
  }

  .btn {
    width: 100%;
    max-width: 280px;
  }

  .hero-footnote {
    white-space: normal;
    padding: 0 24px;
    bottom: 20px;
  }
}
</style>
