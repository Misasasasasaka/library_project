<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[100] flex flex-col gap-2">
      <TransitionGroup name="toast" tag="div">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="[
            'px-4 py-3 rounded-xl shadow-lg flex items-center gap-3 min-w-[280px] max-w-md backdrop-blur-sm',
            typeClass[toast.type]
          ]"
        >
          <!-- 图标 -->
          <Check v-if="toast.type === 'success'" class="w-5 h-5 flex-shrink-0" :stroke-width="2.5" />
          <X v-else-if="toast.type === 'error'" class="w-5 h-5 flex-shrink-0" :stroke-width="2.5" />
          <AlertTriangle v-else-if="toast.type === 'warning'" class="w-5 h-5 flex-shrink-0" :stroke-width="2" />
          <Info v-else class="w-5 h-5 flex-shrink-0" :stroke-width="2" />

          <p class="flex-1 text-sm font-medium">{{ toast.message }}</p>

          <button @click="removeToast(toast.id)" class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity">
            <X class="w-4 h-4" :stroke-width="2" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { toasts, removeToast } from '@utils/toast'
import { Check, X, AlertTriangle, Info } from 'lucide-vue-next'

const typeClass = {
  success: 'bg-emerald-500 text-white',
  error: 'bg-red-500 text-white',
  warning: 'bg-amber-500 text-white',
  info: 'bg-claude-500 text-white',
}
</script>

<style scoped>
.toast-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
