/**
 * API 请求封装
 */

/**
 * 获取 Cookie 值
 */
function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) {
    return parts.pop().split(';').shift()
  }
  return ''
}

/**
 * 统一 API 请求封装
 * @param {string} path - API 路径
 * @param {Object} options - 请求选项
 * @returns {Promise<Object>}
 */
export async function api(path, { method = 'GET', body, isFormData = false } = {}) {
  const headers = {}

  // 非 GET 请求添加 CSRF Token
  if (method !== 'GET') {
    headers['X-CSRFToken'] = getCookie('csrftoken')
  }

  // JSON 请求设置 Content-Type
  if (body && !isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const config = {
    method,
    headers,
    credentials: 'include',
  }

  if (body) {
    config.body = isFormData ? body : JSON.stringify(body)
  }

  const response = await fetch(path, config)

  // 处理非 JSON 响应（如 CSV 下载）
  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    if (!response.ok) {
      throw new Error('请求失败')
    }
    return response
  }

  const data = await response.json()

  // 统一错误处理
  if (!data.ok) {
    const error = new Error(data.message || '请求失败')
    error.data = data
    error.status = response.status
    throw error
  }

  return data
}

// 便捷方法
export const get = (path) => api(path)
export const post = (path, body) => api(path, { method: 'POST', body })
export const patch = (path, body) => api(path, { method: 'PATCH', body })
export const del = (path) => api(path, { method: 'DELETE' })

/**
 * 文件上传（FormData）
 */
export const upload = (path, formData, params = {}) => {
  const url = new URL(path, window.location.origin)
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.set(key, value)
  })
  return api(url.pathname + url.search, {
    method: 'POST',
    body: formData,
    isFormData: true
  })
}

/**
 * 文件下载
 */
export async function download(path, filename) {
  const response = await fetch(path, { credentials: 'include' })
  if (!response.ok) {
    throw new Error('下载失败')
  }
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'download'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}
