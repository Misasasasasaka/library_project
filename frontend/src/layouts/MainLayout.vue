<template>
  <div class="min-h-screen bg-content">
    <Sidebar />

    <!-- 移动端顶部导航栏 -->
    <header v-if="isMobileDevice" class="fixed top-0 left-0 right-0 h-16 bg-sidebar border-b border-sidebar-border z-30 flex items-center px-4">
      <button
        @click="handleToggleMobile"
        class="w-12 h-12 flex items-center justify-center text-text-secondary hover:text-text-primary hover:bg-sidebar-hover rounded-xl transition-colors"
      >
        <Menu class="w-7 h-7" :stroke-width="1.75" />
      </button>
      <span class="ml-3 text-lg font-semibold text-text-primary">图书馆</span>
    </header>

    <main
      :class="[
        'transition-all duration-300',
        // 移动端：无左边距，有顶部边距（为顶部导航留空间）
        isMobileDevice
          ? 'ml-0 pt-20 px-4 pb-4'
          : (sidebarCollapsed ? 'ml-16 p-8' : 'ml-60 p-8')
      ]"
    >
      <router-view />
    </main>
    <Toast />
    <AIChatWidget />
  </div>
</template>

<script setup>
import Sidebar from '@components/Sidebar.vue'
import Toast from '@components/Toast.vue'
import AIChatWidget from '@components/AIChatWidget.vue'
import { sidebarCollapsed, isMobile, toggleMobileMenu } from '@utils/sidebar'
import { Menu } from 'lucide-vue-next'
import { computed } from 'vue'

const isMobileDevice = computed(() => isMobile.value)

function handleToggleMobile() {
  toggleMobileMenu()
}
</script>
