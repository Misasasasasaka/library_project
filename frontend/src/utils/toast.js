/**
 * Toast 消息管理
 */
import { ref } from 'vue'

const toasts = ref([])
let toastId = 0

/**
 * 显示 Toast 消息
 * @param {string} message - 消息内容
 * @param {string} type - 类型：success, error, warning, info
 * @param {number} duration - 持续时间（毫秒）
 */
export function showToast(message, type = 'info', duration = 3000) {
  const id = ++toastId
  const toast = { id, message, type }

  toasts.value.push(toast)

  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

export function removeToast(id) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

// 便捷方法
export const success = (msg, duration) => showToast(msg, 'success', duration)
export const error = (msg, duration) => showToast(msg, 'error', duration)
export const warning = (msg, duration) => showToast(msg, 'warning', duration)
export const info = (msg, duration) => showToast(msg, 'info', duration)

// 导出 toasts 供 Toast 组件使用
export { toasts }
