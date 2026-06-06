export interface PropDefinition {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  required: boolean
  enum?: string[]
  min?: number
  max?: number
  default?: any
}

export type ComponentSlot = 'inline' | 'sidebar' | 'overlay' | 'panel'
export type ComponentLifecycle = 'persistent' | 'ephemeral' | 'sticky'

export interface GenerativeComponentMeta {
  name: string
  version: string
  description: string
  propsSchema: Record<string, PropDefinition>
  slot: ComponentSlot
  defaultLifecycle: ComponentLifecycle
  loader: () => Promise<any>
}

const registry = new Map<string, GenerativeComponentMeta>()

export function registerComponent(meta: GenerativeComponentMeta): void {
  registry.set(meta.name, meta)
}

export function getComponent(name: string): GenerativeComponentMeta | undefined {
  return registry.get(name)
}

export function getAllComponents(): GenerativeComponentMeta[] {
  return Array.from(registry.values())
}

export function validateProps(name: string, props: Record<string, any>): boolean {
  const meta = registry.get(name)
  if (!meta) return false

  for (const [key, schema] of Object.entries(meta.propsSchema)) {
    if (schema.required && (props[key] === undefined || props[key] === null)) {
      console.warn(`[GenerativeUI] Missing required prop "${key}" for component "${name}"`)
      return false
    }
    if (props[key] !== undefined && schema.enum) {
      if (!schema.enum.includes(props[key])) {
        console.warn(`[GenerativeUI] Invalid value for prop "${key}" of component "${name}"`)
        return false
      }
    }
    if (props[key] !== undefined && schema.type === 'number') {
      if (typeof props[key] !== 'number') {
        console.warn(`[GenerativeUI] Prop "${key}" of component "${name}" should be number`)
        return false
      }
      if (schema.min !== undefined && props[key] < schema.min) {
        console.warn(`[GenerativeUI] Prop "${key}" of component "${name}" is below min (${props[key]} < ${schema.min})`)
        return false
      }
      if (schema.max !== undefined && props[key] > schema.max) {
        console.warn(`[GenerativeUI] Prop "${key}" of component "${name}" is above max (${props[key]} > ${schema.max})`)
        return false
      }
    }
  }
  return true
}