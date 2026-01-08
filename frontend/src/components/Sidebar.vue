<template>
  <aside
    :class="[
      'fixed left-0 top-0 h-full bg-sidebar transition-all duration-300 z-40 flex flex-col border-r border-sidebar-border overflow-hidden',
      collapsed ? 'w-16' : 'w-60'
    ]"
  >
    <!-- Logo 区域 -->
    <router-link to="/books/" class="h-16 flex items-center px-4 border-b border-sidebar-border hover:bg-sidebar-hover transition-colors">
      <div class="w-9 h-9 bg-claude-500 rounded-xl flex items-center justify-center flex-shrink-0">
        <Library class="w-5 h-5 text-white" :stroke-width="2" />
      </div>
      <span
        :class="[
          'ml-3 text-lg font-semibold text-text-primary whitespace-nowrap transition-all duration-300',
          collapsed ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'
        ]"
      >
        图书馆
      </span>
    </router-link>

    <!-- 收起/展开按钮 -->
    <button
      @click="toggleCollapse"
      class="h-11 flex items-center px-4 text-text-secondary hover:text-text-primary hover:bg-sidebar-hover transition-colors"
    >
      <component :is="collapsed ? ChevronsRight : ChevronsLeft" class="w-5 h-5 flex-shrink-0" :stroke-width="1.75" />
      <span
        :class="[
          'ml-3 text-sm whitespace-nowrap transition-all duration-300',
          collapsed ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'
        ]"
      >
        收起菜单
      </span>
    </button>

    <!-- 导航菜单 -->
    <nav class="flex-1 py-4 overflow-y-auto overflow-x-hidden">
      <!-- 公共菜单 -->
      <router-link
        v-for="item in visiblePublicMenus"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex items-center mx-2 px-3 py-2.5 rounded-xl transition-all duration-200',
          isActive(item.path)
            ? 'bg-claude-500 text-white shadow-sm'
            : 'text-text-secondary hover:text-text-primary hover:bg-sidebar-hover'
        ]"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" :stroke-width="1.75" />
        <span
          :class="[
            'ml-3 text-sm font-medium whitespace-nowrap transition-all duration-300',
            collapsed ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'
          ]"
        >
          {{ item.label }}
        </span>
      </router-link>

      <!-- 管理员菜单 -->
      <template v-if="isAdminUser">
        <div class="mx-4 my-4">
          <div
            :class="[
              'text-xs text-text-muted uppercase tracking-wider whitespace-nowrap transition-all duration-300',
              collapsed ? 'opacity-0' : 'opacity-100'
            ]"
          >
            管理功能
          </div>
          <div
            :class="[
              'border-t border-sidebar-border transition-all duration-300',
              collapsed ? 'opacity-100' : 'opacity-0 h-0'
            ]"
          ></div>
        </div>
        <router-link
          v-for="item in adminMenus"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center mx-2 px-3 py-2.5 rounded-xl transition-all duration-200',
            isActive(item.path)
              ? 'bg-claude-500 text-white shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-sidebar-hover'
          ]"
        >
          <component :is="item.icon" class="w-5 h-5 flex-shrink-0" :stroke-width="1.75" />
          <span
            :class="[
              'ml-3 text-sm font-medium whitespace-nowrap transition-all duration-300',
              collapsed ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'
            ]"
          >
            {{ item.label }}
          </span>
        </router-link>
      </template>
    </nav>

    <!-- 用户信息区域 -->
    <div class="border-t border-sidebar-border p-4">
      <template v-if="user">
        <div class="flex items-center">
          <div class="w-9 h-9 bg-gradient-to-br from-claude-400 to-claude-600 rounded-xl flex items-center justify-center text-white text-sm font-medium shadow-sm flex-shrink-0">
            {{ user.username.charAt(0).toUpperCase() }}
          </div>
          <div
            :class="[
              'ml-3 overflow-hidden whitespace-nowrap transition-all duration-300',
              collapsed ? 'opacity-0 translate-x-4 w-0' : 'opacity-100 translate-x-0 w-auto'
            ]"
          >
            <div class="text-sm text-text-primary truncate font-medium">{{ user.username }}</div>
            <div class="text-xs text-text-muted">{{ user.role === 'admin' ? '管理员' : '普通用户' }}</div>
          </div>
        </div>
        <button
          @click="handleLogout"
          :class="[
            'mt-3 w-full py-2 text-sm text-text-secondary hover:text-claude-600 border border-border rounded-xl hover:border-claude-300 hover:bg-claude-50 transition-all duration-300 whitespace-nowrap overflow-hidden',
            collapsed ? 'opacity-0 h-0 mt-0 py-0 border-0' : 'opacity-100'
          ]"
        >
          退出登录
        </button>
      </template>
      <template v-else>
        <div class="flex flex-col gap-2">
          <router-link
            to="/login/"
            :class="[
              'block py-2 text-center text-sm bg-claude-500 text-white rounded-xl hover:bg-claude-600 transition-all duration-200 shadow-sm whitespace-nowrap',
              collapsed ? 'px-0' : 'px-4'
            ]"
          >
            <span :class="collapsed ? 'hidden' : ''">登录</span>
            <LogIn v-if="collapsed" class="w-5 h-5 mx-auto" :stroke-width="1.75" />
          </router-link>
          <router-link
            to="/register/"
            :class="[
              'block py-2 text-center text-sm border border-border text-text-secondary rounded-xl hover:border-claude-300 hover:bg-claude-50 transition-all duration-300 whitespace-nowrap overflow-hidden',
              collapsed ? 'opacity-0 h-0 py-0 border-0' : 'opacity-100'
            ]"
          >
            注册
          </router-link>
        </div>
      </template>
    </div>
  </aside>
</template>

<script setup>
import { computed, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { currentUser, logout, isAdmin } from '@utils/auth'
import { sidebarCollapsed, toggleSidebar } from '@utils/sidebar'
import {
  BookOpen,
  ClipboardList,
  Package,
  BarChart3,
  FileUp,
  Bell,
  LogOut,
  LogIn,
  ChevronsLeft,
  ChevronsRight,
  Library
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const collapsed = computed(() => sidebarCollapsed.value)

const user = computed(() => currentUser.value)
const isAdminUser = computed(() => isAdmin())

const publicMenus = [
  { path: '/books/', icon: markRaw(BookOpen), label: '图书浏览', requireAuth: false },
  { path: '/my/borrows/', icon: markRaw(ClipboardList), label: '我的借阅', requireAuth: true },
]

const adminMenus = [
  { path: '/manage/books/', icon: markRaw(Package), label: '图书管理' },
  { path: '/manage/borrows/', icon: markRaw(BarChart3), label: '借阅记录' },
  { path: '/manage/import-export/', icon: markRaw(FileUp), label: '导入/导出' },
  { path: '/manage/overdue/', icon: markRaw(Bell), label: '逾期通知' },
]

const visiblePublicMenus = computed(() => {
  return publicMenus.filter(item => {
    if (item.requireAuth && !user.value) return false
    return true
  })
})

function isActive(path) {
  return route.path === path || route.path.startsWith(path)
}

function toggleCollapse() {
  toggleSidebar()
}

async function handleLogout() {
  try {
    await logout()
    router.push('/login/')
  } catch (e) {
    console.error('登出失败', e)
  }
}
</script>
