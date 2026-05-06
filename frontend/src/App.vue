<template>
  <div id="app">
    <div v-if="hasError" class="error-boundary">
      <div class="error-content">
        <h2>出错了</h2>
        <p>{{ errorMessage }}</p>
        <button @click="retry">重试</button>
      </div>
    </div>
    <router-view v-else />
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'

const hasError = ref(false)
const errorMessage = ref('')

onErrorCaptured((err) => {
  console.error('App error:', err)
  hasError.value = true
  errorMessage.value = err.message || '发生了一些问题'
  return false
})

function retry() {
  hasError.value = false
  errorMessage.value = ''
  window.location.reload()
}
</script>

<style>
:root {
  --font-display: 'Cormorant Garamond', Georgia, serif;
  --font-body: 'Source Sans 3', -apple-system, BlinkMacSystemFont, sans-serif;
  
  --color-bg: #FAF8F5;
  --color-bg-warm: #F5F1EB;
  --color-surface: #FFFFFF;
  --color-text: #1A1A1A;
  --color-text-muted: #6B6B6B;
  --color-accent: #8B4513;
  --color-accent-light: #C4956A;
  --color-border: #E5E0D8;
  --color-ink: #2C2416;
  --color-error: #C75050;
  
  --shadow-sm: 0 1px 3px rgba(44, 36, 22, 0.06);
  --shadow-md: 0 4px 12px rgba(44, 36, 22, 0.08);
  --shadow-lg: 0 12px 40px rgba(44, 36, 22, 0.12);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: var(--font-body);
  background-color: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

::selection {
  background-color: var(--color-accent);
  color: white;
}

::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-warm);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}

.error-boundary {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}

.error-content {
  text-align: center;
  padding: 48px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  max-width: 400px;
}

.error-content h2 {
  font-family: var(--font-display);
  font-size: 28px;
  color: var(--color-error);
  margin-bottom: 12px;
}

.error-content p {
  color: var(--color-text-muted);
  margin-bottom: 24px;
}

.error-content button {
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  padding: 12px 24px;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.error-content button:hover {
  background: var(--color-error);
}
</style>