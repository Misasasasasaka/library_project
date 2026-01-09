import { ref } from 'vue'

// 移动端断点
const MOBILE_BREAKPOINT = 768

// 检测是否为移动端
function checkIsMobile() {
  if (typeof window === 'undefined') return false
  return window.innerWidth < MOBILE_BREAKPOINT
}

// 侧边栏折叠状态（桌面端）
export const sidebarCollapsed = ref(checkIsMobile())

// 移动端侧边栏是否打开
export const mobileMenuOpen = ref(false)

// 是否为移动端
export const isMobile = ref(checkIsMobile())

// 监听窗口大小变化
if (typeof window !== 'undefined') {
  window.addEventListener('resize', () => {
    const mobile = checkIsMobile()
    isMobile.value = mobile
    // 切换到桌面端时关闭移动菜单
    if (!mobile) {
      mobileMenuOpen.value = false
    }
  })
}

// 切换折叠状态（桌面端）
export function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 设置折叠状态
export function setSidebarCollapsed(collapsed) {
  sidebarCollapsed.value = collapsed
}

// 切换移动端菜单
export function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

// 关闭移动端菜单
export function closeMobileMenu() {
  mobileMenuOpen.value = false
}
