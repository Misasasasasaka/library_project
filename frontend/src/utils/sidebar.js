import { ref } from 'vue'

// 侧边栏折叠状态
export const sidebarCollapsed = ref(false)

// 切换折叠状态
export function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 设置折叠状态
export function setSidebarCollapsed(collapsed) {
  sidebarCollapsed.value = collapsed
}
