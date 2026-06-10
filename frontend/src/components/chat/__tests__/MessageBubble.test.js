import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageBubble from '@/components/chat/MessageBubble.vue'

describe('MessageBubble', () => {
  const userMessage = {
    id: 1,
    role: 'user',
    content: 'Hello world',
    timestamp: new Date('2026-01-01T10:00:00'),
  }

  const assistantMessage = {
    id: 2,
    role: 'assistant',
    content: 'Hi there!',
    timestamp: new Date('2026-01-01T10:00:05'),
  }

  it('renders user message with user class', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: userMessage, characterName: 'Test' },
    })
    expect(wrapper.find('.message.user').exists()).toBe(true)
    expect(wrapper.text()).toContain('Hello world')
  })

  it('renders assistant message with assistant class', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: assistantMessage, characterName: '苏格拉底' },
    })
    expect(wrapper.find('.message.assistant').exists()).toBe(true)
    expect(wrapper.text()).toContain('Hi there!')
  })

  it('displays character avatar for assistant messages', () => {
    const wrapper = mount(MessageBubble, {
      props: {
        message: assistantMessage,
        characterName: '苏格拉底',
        characterAvatar: '🧠',
        characterAvatarType: 'emoji',
      },
    })
    expect(wrapper.find('.message-avatar').text()).toContain('🧠')
  })

  it('shows copy button for assistant messages', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: assistantMessage, characterName: 'Test' },
    })
    expect(wrapper.find('.msg-action-btn').exists()).toBe(true)
  })

  it('does not show copy button for user messages', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: userMessage, characterName: 'Test' },
    })
    expect(wrapper.find('.msg-action-btn').exists()).toBe(false)
  })

  it('emits copy event when copy button clicked', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: assistantMessage, characterName: 'Test' },
    })
    wrapper.find('.msg-action-btn').trigger('click')
    expect(wrapper.emitted('copy')).toBeTruthy()
  })

  it('shows timestamp when provided', () => {
    const wrapper = mount(MessageBubble, {
      props: { message: userMessage, characterName: 'Test' },
    })
    expect(wrapper.find('.message-time').exists()).toBe(true)
  })

  it('hides timestamp when not provided', () => {
    const msg = { ...userMessage, timestamp: undefined }
    const wrapper = mount(MessageBubble, {
      props: { message: msg, characterName: 'Test' },
    })
    expect(wrapper.find('.message-time').exists()).toBe(false)
  })
})