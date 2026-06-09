<template>
  <div class="generative-slot" :class="`slot-${slotName}`">
    <component
      v-for="item in activeComponents"
      :key="item.id"
      :is="item.resolved"
      v-bind="item.props"
      @interact="handleInteract(item.id, $event)"
      @destroy="removeComponent(item.id)"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, defineAsyncComponent } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { useNarrativeStore } from '@/stores/narrative'
import { getComponent, validateProps } from './registry'
import LoadingPlaceholder from './LoadingPlaceholder.vue'
import ErrorFallback from './ErrorFallback.vue'

const props = defineProps({
  slotName: { type: String, required: true },
})

const ws = useWebSocket()
const narrativeStore = useNarrativeStore()
const components = ref([])
const componentCache = new Map()

const activeComponents = computed(() => components.value)

function handleUIRender(msg) {
  if (msg.type !== 'ui.render') return

  for (const comp of (msg.components || [])) {
    if (comp.slot !== props.slotName) continue
    if (!validateProps(comp.component, comp.props || {})) {
      console.warn(`[DynamicRenderer] Invalid props for ${comp.component}`)
      continue
    }

    const meta = getComponent(comp.component)
    if (!meta) {
      console.warn(`[DynamicRenderer] Unknown component: ${comp.component}`)
      continue
    }

    if (!componentCache.has(comp.component)) {
      componentCache.set(comp.component, defineAsyncComponent({
        loader: meta.loader,
        loadingComponent: LoadingPlaceholder,
        errorComponent: ErrorFallback,
        delay: 100,
        timeout: 5000,
      }))
    }
    const asyncComp = componentCache.get(comp.component)

    const existingIdx = components.value.findIndex(c => c.id === comp.id)
    const entry = {
      id: comp.id,
      name: comp.component,
      props: comp.props || {},
      lifecycle: comp.lifecycle || meta.defaultLifecycle,
      resolved: asyncComp,
    }
    if (existingIdx >= 0) {
      components.value[existingIdx] = entry
    } else {
      components.value.push(entry)
    }
    narrativeStore.addGenerativeComponent({
      id: comp.id,
      component: comp.component,
      props: comp.props || {},
      slot: comp.slot,
      lifecycle: comp.lifecycle || meta.defaultLifecycle,
    })
  }
}

function handleUIDestroy(msg) {
  if (msg.type !== 'ui.destroy') return
  const ids = msg.component_ids || []
  components.value = components.value.filter(c => !ids.includes(c.id))
  for (const id of ids) {
    narrativeStore.removeGenerativeComponent(id)
  }
}

function handleUIUpdate(msg) {
  if (msg.type !== 'ui.update') return
  const comp = components.value.find(c => c.id === msg.component_id)
  if (comp) {
    comp.props = { ...comp.props, ...(msg.props || {}) }
    narrativeStore.updateGenerativeComponent(msg.component_id, msg.props || {})
  }
}

function handleInteract(componentId, eventData) {
  ws.sendUIInteract(componentId, eventData?.action || '', eventData?.value || eventData)
}

function removeComponent(id) {
  components.value = components.value.filter(c => c.id !== id)
}

let unsubRender = null
let unsubDestroy = null
let unsubUpdate = null

onMounted(() => {
  unsubRender = ws.on('ui.render', handleUIRender)
  unsubDestroy = ws.on('ui.destroy', handleUIDestroy)
  unsubUpdate = ws.on('ui.update', handleUIUpdate)
})

onUnmounted(() => {
  unsubRender?.()
  unsubDestroy?.()
  unsubUpdate?.()
})
</script>

<style scoped>
.generative-slot {
  width: 100%;
}

.slot-sidebar {
  width: 100%;
  max-width: var(--gen-sidebar-width);
}

.slot-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--gen-overlay-z);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.slot-overlay > :deep(*) {
  pointer-events: auto;
}

.slot-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 480px;
  max-width: 90vw;
  z-index: var(--gen-panel-z);
  background: var(--color-surface, #fff);
  border-left: 1px solid var(--color-border, #E5E0D8);
  box-shadow: var(--shadow-lg, 0 12px 40px rgba(44, 36, 22, 0.12));
  overflow-y: auto;
  padding: 20px;
}
</style>