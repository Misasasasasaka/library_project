<template>
  <div class="bg-white rounded-2xl border border-border p-4 hover:shadow-sm transition-shadow">
    <div class="flex gap-4">
      <!-- 封面 -->
      <div class="w-20 h-28 bg-sidebar rounded-xl flex-shrink-0 overflow-hidden">
        <img
          v-if="borrow.book?.cover_url"
          :src="borrow.book.cover_url"
          :alt="borrow.book?.title"
          class="w-full h-full object-cover"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-text-light">
          <BookOpen class="w-8 h-8" :stroke-width="1" />
        </div>
      </div>

      <!-- 信息 -->
      <div class="flex-1 min-w-0">
        <h4 class="font-medium text-text-primary truncate">{{ borrow.book?.title }}</h4>
        <p class="text-sm text-text-muted mt-1">
          借阅: {{ formatDate(borrow.borrow_date) }} · 应还: {{ formatDate(borrow.due_date) }}
        </p>

        <!-- 状态 -->
        <div class="flex items-center gap-2 mt-2">
          <span v-if="borrow.is_overdue" class="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg bg-red-50 text-red-600">
            逾期 {{ overdueDays }} 天
          </span>
          <span v-else-if="daysRemaining <= 3 && daysRemaining > 0" class="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg bg-amber-50 text-amber-600">
            剩余 {{ daysRemaining }} 天
          </span>
          <span v-else-if="daysRemaining > 0" class="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg bg-claude-50 text-claude-600">
            借阅中
          </span>
        </div>

        <!-- 操作按钮 -->
        <div class="flex gap-2 mt-3">
          <button
            v-if="!borrow.return_date && !borrow.is_overdue"
            @click="$emit('renew', borrow.id)"
            class="px-3 py-1.5 text-sm border border-border text-text-secondary rounded-lg hover:bg-sidebar transition-colors"
            :disabled="loading"
          >
            续借
          </button>
          <button
            v-if="!borrow.return_date"
            @click="$emit('return', borrow.id)"
            class="px-3 py-1.5 text-sm bg-claude-500 text-white rounded-lg hover:bg-claude-600 transition-colors"
            :disabled="loading"
          >
            {{ borrow.is_overdue ? '立即归还' : '归还' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { BookOpen } from 'lucide-vue-next'

const props = defineProps({
  borrow: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['renew', 'return'])

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

const daysRemaining = computed(() => {
  if (!props.borrow.due_date) return 0
  const due = new Date(props.borrow.due_date)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  due.setHours(0, 0, 0, 0)
  return Math.ceil((due - today) / (1000 * 60 * 60 * 24))
})

const overdueDays = computed(() => {
  return Math.abs(daysRemaining.value)
})
</script>
