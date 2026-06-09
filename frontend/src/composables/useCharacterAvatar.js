const SAFE_URL_PROTOCOLS = ['data:image/', 'https://', 'http://', '/']
const FILENAME_PATTERN = /^[\w][\w.-]{0,127}$/

function isSafeAvatarUrl(value) {
  if (typeof value !== 'string' || value.length === 0) return false
  return SAFE_URL_PROTOCOLS.some(prefix => value.startsWith(prefix))
}

function isSafeFilename(value) {
  if (typeof value !== 'string' || value.length === 0) return false
  if (value.includes('..') || value.includes('/') || value.includes('\\')) {
    return false
  }
  return FILENAME_PATTERN.test(value)
}

export function getAvatarDisplay(item) {
  if (item.avatar_type === 'emoji' && item.avatar) {
    return item.avatar
  }
  if (item.avatar_type === 'image') {
    return ''
  }
  return item.name ? item.name.charAt(0) : '?'
}

export function getAvatarStyle(item) {
  if (item.avatar_type !== 'image' || typeof item.avatar !== 'string') {
    return {}
  }
  if (isSafeAvatarUrl(item.avatar)) {
    return {
      backgroundImage: `url(${item.avatar})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  if (isSafeFilename(item.avatar)) {
    return {
      backgroundImage: `url(/api/v1/uploads/avatars/${encodeURIComponent(item.avatar)})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
    }
  }
  return {}
}
