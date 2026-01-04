<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- 遮罩 -->
        <div
          class="absolute inset-0 bg-text-primary/50 backdrop-blur-sm"
          @click="handleClose"
        ></div>

        <!-- 弹窗内容 -->
        <div
          :class="[
            'relative bg-white rounded-2xl shadow-xl max-h-[90vh] overflow-auto',
            sizeClass
          ]"
        >
          <!-- 标题栏 -->
          <div v-if="title" class="flex items-center justify-between px-6 py-5 border-b border-border">
            <h3 class="text-lg font-semibold text-text-primary">{{ title }}</h3>
            <button
              @click="handleClose"
              class="text-text-muted hover:text-text-secondary transition-colors"
            >
              <X class="w-5 h-5" :stroke-width="2" />
            </button>
          </div>

          <!-- 内容区 -->
          <div class="p-6">
            <slot></slot>
          </div>

          <!-- 底部按钮 -->
          <div v-if="$slots.footer" class="px-6 py-4 border-t border-border flex justify-end gap-3 bg-sidebar rounded-b-2xl">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: Boolean,
  title: String,
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md', 'lg', 'xl'].includes(v)
  },
  closable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

const sizeClass = computed(() => {
  const sizes = {
    sm: 'w-full max-w-sm',
    md: 'w-full max-w-md',
    lg: 'w-full max-w-lg',
    xl: 'w-full max-w-xl',
  }
  return sizes[props.size]
})

function handleClose() {
  if (props.closable) {
    emit('update:modelValue', false)
    emit('close')
  }
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
