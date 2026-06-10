import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatInput from '@/components/chat/ChatInput.vue'

describe('ChatInput', () => {
  it('renders textarea and send button', () => {
    const wrapper = mount(ChatInput, {
      props: { modelValue: '', sending: false },
    })
    expect(wrapper.find('textarea').exists()).toBe(true)
    expect(wrapper.find('.btn-send').exists()).toBe(true)
  })

  it('disables send button when input is empty', () => {
    const wrapper = mount(ChatInput, {
      props: { modelValue: '', sending: false },
    })
    expect(wrapper.find('.btn-send').element.disabled).toBe(true)
  })

  it('enables send button when input has content', async () => {
    const wrapper = mount(ChatInput, {
      props: { modelValue: 'Hello', sending: false },
    })
    expect(wrapper.find('.btn-send').element.disabled).toBe(false)
  })

  it('disables send button when sending', () => {
    const wrapper = mount(ChatInput, {
      props: { modelValue: 'Hello', sending: true },
    })
    expect(wrapper.find('.btn-send').element.disabled).toBe(true)
  })

  it('emits send event on button click', async () => {
    const wrapper = mount(ChatInput, {
      props: { modelValue: 'Hello', sending: false },
    })
    await wrapper.find('.btn-send').trigger('click')
    expect(wrapper.emitted('send')).toBeTruthy()
    expect(wrapper.emitted('send')[0]).toEqual(['Hello'])
  })

  it('emits update:modelValue on input', async () => {
    const wrapper = mount(ChatInput, {
      props: { modelValue: '', sending: false },
    })
    await wrapper.find('textarea').setValue('test input')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })
})