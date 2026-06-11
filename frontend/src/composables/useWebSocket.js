import { ref, readonly } from 'vue'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000`
const WS_PATH = '/api/v1/ws/ws'

const MAX_RECONNECT_DELAY = 30000
const BASE_RECONNECT_DELAY = 1000

class NarrativeWebSocket {
  constructor() {
    this.ws = null
    this.reconnectAttempts = 0
    this.connected = ref(false)
    this.connectionState = ref('disconnected')
    this.handlers = new Map()
    this._url = ''
    this._intentionalDisconnect = false
    this._reconnectTimer = null
  }

  connect(modelConfigId = null) {
    const params = new URLSearchParams()
    if (modelConfigId) {
      params.set('model_config_id', modelConfigId)
    }
    const url = `${WS_BASE_URL}${WS_PATH}?${params.toString()}`
    this._url = url
    this._doConnect(url)
  }

  _doConnect(url) {
    if (this.ws) {
      this.ws.close()
    }
    this.connectionState.value = 'connecting'
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectAttempts = 0
      this.connected.value = true
      this.connectionState.value = 'connected'
      console.log('[WS] Connected')
      this.send({ type: 'state.sync' })
    }

    this.ws.onclose = () => {
      this.connected.value = false
      this.connectionState.value = 'disconnected'
      console.log('[WS] Disconnected')
      if (!this._intentionalDisconnect) {
        this._scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error)
      if (this.ws) {
        this.ws.close()
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        this._dispatch(msg)
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }
  }

  _scheduleReconnect() {
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer)
    }
    const delay = Math.min(
      BASE_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempts),
      MAX_RECONNECT_DELAY
    )
    this.reconnectAttempts++
    this.connectionState.value = 'reconnecting'
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    this._reconnectTimer = setTimeout(() => {
      if (!this.connected.value) {
        this._doConnect(this._url)
      }
      this._reconnectTimer = null
    }, delay)
  }

  _dispatch(msg) {
    const type = msg.type
    if (this.handlers.has(type)) {
      this.handlers.get(type).forEach(cb => cb(msg))
    }
    if (this.handlers.has('*')) {
      this.handlers.get('*').forEach(cb => cb(msg))
    }
  }

  on(type, callback) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type).push(callback)
    return () => {
      const handlers = this.handlers.get(type)
      const idx = handlers.indexOf(callback)
      if (idx > -1) handlers.splice(idx, 1)
    }
  }

  off(type, callback) {
    if (!this.handlers.has(type)) return
    if (callback) {
      const handlers = this.handlers.get(type)
      const idx = handlers.indexOf(callback)
      if (idx > -1) handlers.splice(idx, 1)
    } else {
      this.handlers.delete(type)
    }
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('[WS] Cannot send, not connected')
    }
  }

  sendChat(conversationId, content, characterId) {
    this.send({
      type: 'chat.send',
      payload: { content, conversation_id: conversationId, character_id: characterId },
      id: `chat_${Date.now()}`,
    })
  }

  switchScene(sceneId) {
    this.send({
      type: 'scene.switch',
      payload: { scene_id: sceneId },
    })
  }

  requestStateSync() {
    this.send({ type: 'state.sync' })
  }

  confirmSyllabus(materialId) {
    this.send({
      type: 'syllabus.confirm',
      payload: { material_id: materialId },
    })
  }

  rejectSyllabus(materialId) {
    this.send({
      type: 'syllabus.reject',
      payload: { material_id: materialId },
    })
  }

  activateSyllabus(materialId) {
    this.send({
      type: 'syllabus.activate',
      payload: { material_id: materialId },
    })
  }

  generateAssessment(pointId, characterId) {
    this.send({
      type: 'assessment.generate',
      payload: { point_id: pointId, character_id: characterId },
    })
  }

  submitAssessment(pointId, characterId, answers, conversationId) {
    this.send({
      type: 'assessment.answer',
      payload: {
        point_id: pointId,
        character_id: characterId,
        answers: answers,
        conversation_id: conversationId,
      },
    })
  }

  advanceTime(days = 1) {
    this.send({
      type: 'time.advance',
      payload: { days },
    })
  }

  ping() {
    this.send({ type: 'ping' })
  }

  sendUIInteract(componentId, action, value) {
    this.send({
      type: 'ui.interact',
      payload: { component_id: componentId, action, value },
    })
  }

  disconnect() {
    this._intentionalDisconnect = true
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer)
      this._reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

const wsInstance = new NarrativeWebSocket()

export function useWebSocket() {
  return {
    connected: readonly(wsInstance.connected),
    connectionState: readonly(wsInstance.connectionState),
    connect: wsInstance.connect.bind(wsInstance),
    disconnect: wsInstance.disconnect.bind(wsInstance),
    send: wsInstance.send.bind(wsInstance),
    sendChat: wsInstance.sendChat.bind(wsInstance),
    switchScene: wsInstance.switchScene.bind(wsInstance),
    requestStateSync: wsInstance.requestStateSync.bind(wsInstance),
    confirmSyllabus: wsInstance.confirmSyllabus.bind(wsInstance),
    rejectSyllabus: wsInstance.rejectSyllabus.bind(wsInstance),
    activateSyllabus: wsInstance.activateSyllabus.bind(wsInstance),
    generateAssessment: wsInstance.generateAssessment.bind(wsInstance),
    submitAssessment: wsInstance.submitAssessment.bind(wsInstance),
    advanceTime: wsInstance.advanceTime.bind(wsInstance),
    on: wsInstance.on.bind(wsInstance),
    off: wsInstance.off.bind(wsInstance),
    ping: wsInstance.ping.bind(wsInstance),
    sendUIInteract: wsInstance.sendUIInteract.bind(wsInstance),
  }
}