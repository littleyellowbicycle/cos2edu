<template>
  <div
    class="markdown-content"
    :class="{ 'is-streaming': streaming }"
    :ref="setContentRef"
    v-html="renderedHtml"
  ></div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import mermaid from 'mermaid'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  content: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
})

const emit = defineEmits(['rendered'])

const contentRef = ref(null)

function setContentRef(el) {
  if (el) contentRef.value = el
}

const emojiSectionRegex = /^([\p{Emoji_Presentation}\p{Extended_Pictographic}\u{1F300}-\u{1F9FF}]+)\s+(.+)$/u

const customRenderer = new marked.Renderer()

customRenderer.heading = function (data) {
  const text = data.text
  const depth = data.depth
  const match = text.match(emojiSectionRegex)
  if (match) {
    const emoji = match[1]
    const title = match[2]
    return `<h${depth} class="ai-heading ai-heading--emoji"><span class="ai-heading-emoji">${emoji}</span><span class="ai-heading-text">${title}</span></h${depth}>`
  }
  return `<h${depth} class="ai-heading">${text}</h${depth}>`
}

customRenderer.table = function (data) {
  const headers = data.header.map(h => `<th>${h.text}</th>`).join('')
  const rows = data.rows.map(row => {
    const cells = row.map(cell => `<td>${cell.text}</td>`).join('')
    return `<tr>${cells}</tr>`
  }).join('')
  return `<div class="ai-table-wrapper"><table class="ai-table"><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table></div>`
}

customRenderer.blockquote = function (data) {
  const text = data.text
  const match = text.match(emojiSectionRegex)
  if (match) {
    return `<div class="ai-callout"><span class="ai-callout-emoji">${match[1]}</span><div class="ai-callout-content">${match[2]}${text.replace(match[0], '')}</div></div>`
  }
  return `<blockquote class="ai-blockquote">${text}</blockquote>`
}

customRenderer.list = function (data) {
  const tag = data.ordered ? 'ol' : 'ul'
  const items = data.items.map(item => `<li>${item.text}</li>`).join('')
  const cls = data.ordered ? 'ai-list ai-list--ordered' : 'ai-list'
  return `<${tag} class="${cls}">${items}</${tag}>`
}

customRenderer.paragraph = function (data) {
  const text = data.text
  if (text.startsWith('<h') || text.startsWith('<div class="ai-') || text.startsWith('<details')) {
    return text
  }
  const strongMatch = text.match(/^<strong>([^<]+)<\/strong>\s*(.*)$/)
  if (strongMatch) {
    return `<p class="ai-paragraph"><strong class="ai-highlight">${strongMatch[1]}</strong>${strongMatch[2]}</p>`
  }
  return `<p class="ai-paragraph">${text}</p>`
}

customRenderer.hr = function () {
  return `<hr class="ai-divider" />`
}

customRenderer.code = function (data) {
  const lang = data.lang || ''
  const code = data.text
  if (lang === 'mermaid') {
    return `<pre class="mermaid">${code}</pre>`
  }
  return `<div class="ai-code-block"><div class="ai-code-header"><span class="ai-code-lang">${lang || 'code'}</span></div><pre class="ai-code-content"><code>${code}</code></pre></div>`
}

marked.setOptions({
  breaks: true,
  gfm: true,
  renderer: customRenderer
})

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function renderLatex(text) {
  text = text.replace(/\$\$(.*?)\$\$/gs, (_, math) => {
    try {
      return `<div class="math-block">${katex.renderToString(math, { displayMode: true, throwOnError: false })}</div>`
    } catch (e) {
      return `<div class="math-block math-error">${escapeHtml(math)}</div>`
    }
  })
  text = text.replace(/\$(.*?)\$/g, (_, math) => {
    try {
      return katex.renderToString(math, { displayMode: false, throwOnError: false })
    } catch (e) {
      return `<span class="math-error">${escapeHtml(math)}</span>`
    }
  })
  return text
}

function preprocessMarkdown(text) {
  text = renderLatex(text)
  return text
}

async function renderMermaid(element) {
  const mermaidBlocks = element.querySelectorAll('pre.mermaid')
  for (const block of mermaidBlocks) {
    const code = block.textContent
    try {
      const id = 'mermaid-' + Math.random().toString(36).substr(2, 9)
      const { svg } = await mermaid.render(id, code)
      const wrapper = document.createElement('div')
      wrapper.className = 'mermaid-svg'
      wrapper.innerHTML = svg
      block.replaceWith(wrapper)
    } catch (e) {
      block.className = 'mermaid-error'
      block.textContent = code
    }
  }
}

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose'
})

const renderedHtml = computed(() => {
  if (!props.content) return ''
  let text = props.content
  // Convert think tags to collapsible details
  text = text.replace(/<think>([\s\S]*?)<\/think>/gi, (_, thought) => {
    const preview = thought.trim().slice(0, 60)
    return `<details class="think-block"><summary>💭 思考过程 · ${preview}${thought.trim().length > 60 ? '…' : ''}</summary><div class="think-content">${marked.parse(preprocessMarkdown(thought.trim()))}</div></details>`
  })
  text = preprocessMarkdown(text)
  let html = marked.parse(text)
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ['details', 'summary', 'canvas'],
    ADD_ATTR: ['collapsible'],
  })
})

watch(renderedHtml, () => {
  nextTick(() => {
    if (contentRef.value) {
      renderMermaid(contentRef.value)
      emit('rendered')
    }
  })
})

onMounted(() => {
  if (contentRef.value) {
    renderMermaid(contentRef.value)
  }
})
</script>

<style scoped>
.markdown-content {
  line-height: 1.8;
  font-size: 15px;
  color: var(--color-ink);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.markdown-content :deep(.think-block) {
  background: var(--color-bg-warm);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 12px;
  font-size: 14px;
}

.markdown-content :deep(.think-block summary) {
  cursor: pointer;
  color: var(--color-text-muted);
  font-weight: 500;
  user-select: none;
}

.markdown-content :deep(.think-block summary:hover) {
  color: var(--color-ink);
}

.markdown-content :deep(.think-content) {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border);
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.markdown-content.is-streaming::after {
  content: '▍';
  display: inline;
  animation: cursor-blink 0.8s step-end infinite;
  color: var(--color-accent);
  margin-left: 1px;
}

@keyframes cursor-blink {
  50% { opacity: 0; }
}

.message-footer {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-content:hover .message-footer {
  opacity: 1;
}

.msg-action-btn {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all 0.15s;
}

.msg-action-btn:hover {
  background: var(--color-bg-warm);
  color: var(--color-ink);
}

.message-time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.message.user .message-time {
  text-align: right;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 20px 24px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--color-text-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

.input-area {
  padding: 20px 32px 24px;
  background: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: stretch;
  position: relative;
}

.input-wrapper textarea {
  flex: 1;
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.5;
  padding: 14px 18px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg);
  color: var(--color-text);
  resize: none;
  min-height: 52px;
  max-height: 150px;
  transition: border-color 0.2s;
  pointer-events: auto;
  z-index: 1;
  width: 100%;
}

.input-wrapper textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.input-wrapper textarea::placeholder {
  color: var(--color-text-muted);
}

.input-wrapper textarea:disabled {
  background: var(--color-bg-warm);
  cursor: not-allowed;
}

.btn-send {
  height: 52px;
  padding: 0 28px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  background: var(--color-ink);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-send:hover:not(:disabled) {
  background: var(--color-accent);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sending-dots {
  animation: pulse 1s infinite;
}

.input-hint {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 8px;
  text-align: center;
}

.chat-sidebar {
  width: 300px;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
}

.sidebar-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.history-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 14px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.history-item:hover {
  background: var(--color-bg);
}

.history-item.active {
  background: var(--color-bg-warm);
  border-left: 3px solid var(--color-accent);
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.history-date {
  font-size: 12px;
  color: var(--color-text-muted);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (max-width: 768px) {
  .chat-header {
    padding: 16px 20px;
  }
  
  .messages {
    padding: 20px;
  }
  
  .message {
    max-width: 90%;
  }
  
  .input-area {
    padding: 16px 20px;
  }
  
  .chat-sidebar {
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    box-shadow: var(--shadow-lg);
  }
}

.markdown-content :deep(.math-block) {
  margin: 12px 0;
  overflow-x: auto;
}

.markdown-content :deep(.math-error) {
  color: #C75050;
  background: #FEF2F2;
  padding: 4px 8px;
  border-radius: 4px;
}

.markdown-content :deep(.mermaid-svg) {
  margin: 16px 0;
  display: flex;
  justify-content: center;
}

.markdown-content :deep(.mermaid-svg svg) {
  max-width: 100%;
  height: auto;
}

.markdown-content :deep(.mermaid-error) {
  background: #FEF2F2;
  color: #C75050;
  padding: 12px 16px;
border-radius: 4px;
  border: 1px solid #FFCDD2;
  font-family: var(--font-mono, monospace);
  font-size: 13px;
}

.markdown-content :deep(code ) {
  background: var(--color-bg-warm);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono, 'Fira Code', 'Monaco', monospace);
  font-size: 0.9em;
}

.markdown-content :deep(.ai-heading ) {
  margin: 20px 0 10px;
  font-weight: 700;
  color: var(--color-ink);
  line-height: 1.4;
}

.markdown-content :deep(.ai-heading:first-child ){
  margin-top: 0;
}

.markdown-content :deep(.ai-heading--emoji ) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-border);
}

.markdown-content :deep(.ai-heading-emoji ){
  font-size: 1.2em;
  flex-shrink: 0;
}

.markdown-content :deep(.ai-heading-text ){
  flex: 1;
}

.markdown-content :deep(h1.ai-heading ){ font-size: 1.4em; }
.markdown-content :deep(h2.ai-heading ){ font-size: 1.25em; }
.markdown-content :deep(h3.ai-heading ){ font-size: 1.1em; }
.markdown-content :deep(h4.ai-heading ){ font-size: 1em; }

.markdown-content :deep(.ai-paragraph ){
  margin: 8px 0;
  line-height: 1.75;
}

.markdown-content :deep(.ai-highlight ) {
  color: var(--color-accent);
  font-weight: 700;
}

.markdown-content :deep(.ai-list ){
  margin: 10px 0;
  padding-left: 0;
  list-style: none;
}

.markdown-content :deep(.ai-list li ){
  position: relative;
  padding: 6px 0 6px 24px;
  margin: 0;
  line-height: 1.7;
}

.markdown-content :deep(.ai-list li::before ) {
  content: '';
  position: absolute;
  left: 6px;
  top: 14px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent);
}

.markdown-content :deep(.ai-list--ordered ){
  counter-reset: ai-counter;
}

.markdown-content :deep(.ai-list--ordered li ){
  padding-left: 28px;
}

.markdown-content :deep(.ai-list--ordered li::before ) {
  content: counter(ai-counter);
  counter-increment: ai-counter;
  width: auto;
  height: auto;
  border-radius: 0;
  background: none;
  color: var(--color-accent);
  font-weight: 700;
  font-size: 0.9em;
  left: 4px;
  top: 7px;
}

.markdown-content :deep(.ai-table-wrapper ) {
  margin: 14px 0;
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.markdown-content :deep(.ai-table ){
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.markdown-content :deep(.ai-table th ) {
  background: var(--color-ink);
  color: white;
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.markdown-content :deep(.ai-table td ) {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  line-height: 1.5;
}

.markdown-content :deep(.ai-table tbody tr:last-child td ) {
  border-bottom: none;
}

.markdown-content :deep(.ai-table tbody tr:nth-child(even)) {
  background: var(--color-bg-warm);
}

.markdown-content :deep(.ai-table tbody tr:hover ) {
  background: rgba(0, 0, 0, 0.03);
}

.markdown-content :deep(.ai-callout ) {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 14px 0;
  padding: 12px 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-bg-warm), var(--color-surface));
  border: 1px solid var(--color-border);
}

.markdown-content :deep(.ai-callout-emoji ){
  font-size: 1.3em;
  flex-shrink: 0;
  margin-top: 1px;
}

.markdown-content :deep(.ai-callout-content ){
  flex: 1;
  line-height: 1.6;
}

.markdown-content :deep(.ai-blockquote ) {
  margin: 12px 0;
  padding: 10px 16px;
  border-left: 4px solid var(--color-accent);
  background: var(--color-bg-warm);
  border-radius: 0 6px 6px 0;
  color: var(--color-text-muted);
  line-height: 1.6;
}

.markdown-content :deep(.ai-divider ) {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-border), transparent);
  margin: 20px 0;
}

.markdown-content :deep(.ai-code-block ) {
  margin: 14px 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.markdown-content :deep(.ai-code-header ) {
  padding: 6px 14px;
  background: var(--color-ink);
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  font-family: var(--font-body);
}

.markdown-content :deep(.ai-code-lang ){
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.markdown-content :deep(.ai-code-content ) {
  margin: 0;
  padding: 14px;
  background: #1e1e2e;
  color: #cdd6f4;
  overflow-x: auto;
  font-family: var(--font-mono, 'Fira Code', 'Monaco', monospace);
  font-size: 13px;
  line-height: 1.6;
}

.markdown-content :deep(a ) {
  color: var(--color-accent);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-content :deep(a:hover ) {
  color: var(--color-ink);
}

.markdown-content :deep(img ){
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 10px 0;
}

.markdown-content :deep(strong ) {
  color: var(--color-ink);
  font-weight: 700;
}

.markdown-content :deep(em ) {
  color: var(--color-text-muted);
  font-style: italic;
}
</style>