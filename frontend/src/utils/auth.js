/**
 * 认证状态管理
 */
import { ref, readonly } from 'vue'
import { get, post } from './api'

// 全局用户状态
const user = ref(null)
const loading = ref(true)
const initialized = ref(false)

/**
 * 初始化认证状态（页面加载时调用）
 */
export async function initAuth() {
  if (initialized.value) return user.value

  loading.value = true
  try {
    // 先获取 CSRF Token
    await get('/api/auth/csrf')
    // 获取当前用户信息
    const data = await get('/api/auth/me')
    user.value = data.user
  } catch (e) {
    user.value = null
  } finally {
    loading.value = false
    initialized.value = true
  }

  return user.value
}

/**
 * 登录
 */
export async function login(username, password) {
  const data = await post('/api/auth/login', { username, password })
  user.value = data.user
  return data.user
}

/**
 * 注册
 */
export async function register(username, password, mail) {
  const data = await post('/api/auth/register', { username, password, mail })
  user.value = data.user
  return data.user
}

/**
 * 登出
 */
export async function logout() {
  await post('/api/auth/logout')
  user.value = null
}

/**
 * 检查是否为管理员
 */
export function isAdmin() {
  if (!user.value) return false
  return user.value.role === 'admin'
}

/**
 * 检查是否已登录
 */
export function isAuthenticated() {
  return !!user.value
}

// 导出响应式状态（只读）
export const currentUser = readonly(user)
export const authLoading = readonly(loading)
