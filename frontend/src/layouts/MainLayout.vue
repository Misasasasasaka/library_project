<template>
  <div class="min-h-screen bg-content">
    <Sidebar />
    <main :class="['p-8 transition-all duration-300', sidebarCollapsed ? 'ml-16' : 'ml-60']">
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
import { sidebarCollapsed } from '@utils/sidebar'
</script>
