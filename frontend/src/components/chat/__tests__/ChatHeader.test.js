import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatHeader from '@/components/chat/ChatHeader.vue'

describe('ChatHeader', () => {
  it('renders character name', () => {
    const wrapper = mount(ChatHeader, {
      props: { characterName: '苏格拉底' },
    })
    expect(wrapper.text()).toContain('苏格拉底')
  })

  it('shows material title when provided', () => {
    const wrapper = mount(ChatHeader, {
      props: { characterName: '苏格拉底', materialTitle: 'Python基础' },
    })
    expect(wrapper.text()).toContain('Python基础')
  })

  it('shows typing status when isTyping is true', () => {
    const wrapper = mount(ChatHeader, {
      props: { characterName: '苏格拉底', isTyping: true },
    })
    expect(wrapper.text()).toContain('正在思考')
  })

  it('emits toggle-sidebar event', () => {
    const wrapper = mount(ChatHeader, {
      props: { characterName: '苏格拉底' },
    })
    wrapper.find('.btn-sidebar').trigger('click')
    expect(wrapper.emitted('toggle-sidebar')).toBeTruthy()
  })
})