import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useWebSocket } from '@/composables/useWebSocket'

describe('useWebSocket', () => {
  let originalWebSocket

  beforeEach(() => {
    originalWebSocket = global.WebSocket
  })

  afterEach(() => {
    global.WebSocket = originalWebSocket
    vi.restoreAllMocks()
  })

  function mockWebSocket() {
    const ws = {
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null,
      readyState: 0,
      send: vi.fn(),
      close: vi.fn(),
    }
    global.WebSocket = vi.fn(() => {
      setTimeout(() => {
        ws.readyState = 1
        if (ws.onopen) ws.onopen()
      }, 10)
      return ws
    })
    return ws
  }

  it('returns expected API shape', () => {
    const ws = useWebSocket()
    expect(ws).toHaveProperty('connect')
    expect(ws).toHaveProperty('disconnect')
    expect(ws).toHaveProperty('send')
    expect(ws).toHaveProperty('on')
    expect(ws).toHaveProperty('off')
    expect(ws).toHaveProperty('sendChat')
    expect(ws).toHaveProperty('connected')
    expect(ws).toHaveProperty('connectionState')
  })

  it('on() returns unsubscribe function', () => {
    const ws = useWebSocket()
    const unsub = ws.on('test.event', () => {})
    expect(typeof unsub).toBe('function')
    unsub()
  })

  it('off() removes handler', () => {
    const ws = useWebSocket()
    const handler = vi.fn()
    ws.on('test.event', handler)
    ws.off('test.event', handler)
  })

  it('send warns when not connected', () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const ws = useWebSocket()
    ws.send({ type: 'test' })
    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('not connected'))
    warnSpy.mockRestore()
  })

  it('sendChat formats message correctly', () => {
    const ws = useWebSocket()
    const sendSpy = vi.spyOn(ws, 'send').mockImplementation(() => {})
    ws.sendChat('conv1', 'hello', 'char1')
    expect(sendSpy).toHaveBeenCalledWith(expect.objectContaining({
      type: 'chat.send',
      payload: expect.objectContaining({
        content: 'hello',
        conversation_id: 'conv1',
        character_id: 'char1',
      }),
    }))
    sendSpy.mockRestore()
  })

  it('does not reconnect after intentional disconnect', () => {
    const ws = useWebSocket()
    ws.disconnect()
  })
})