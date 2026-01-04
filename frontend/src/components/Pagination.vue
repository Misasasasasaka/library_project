<template>
  <div v-if="totalPages > 1" class="flex items-center justify-center gap-1">
    <!-- 上一页 -->
    <button
      @click="goTo(currentPage - 1)"
      :disabled="currentPage === 1"
      class="px-3 py-2 text-sm rounded-lg border border-border bg-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-sidebar transition-colors"
    >
      上一页
    </button>

    <!-- 页码 -->
    <template v-for="page in visiblePages" :key="page">
      <span v-if="page === '...'" class="px-2 text-text-muted">...</span>
      <button
        v-else
        @click="goTo(page)"
        :class="[
          'px-3 py-2 text-sm rounded-lg border transition-colors',
          page === currentPage
            ? 'bg-claude-500 text-white border-claude-500'
            : 'border-border bg-white hover:bg-sidebar'
        ]"
      >
        {{ page }}
      </button>
    </template>

    <!-- 下一页 -->
    <button
      @click="goTo(currentPage + 1)"
      :disabled="currentPage === totalPages"
      class="px-3 py-2 text-sm rounded-lg border border-border bg-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-sidebar transition-colors"
    >
      下一页
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: {
    type: Number,
    required: true
  },
  totalPages: {
    type: Number,
    required: true
  },
  maxVisible: {
    type: Number,
    default: 5
  }
})

const emit = defineEmits(['change'])

const visiblePages = computed(() => {
  const pages = []
  const total = props.totalPages
  const current = props.currentPage
  const max = props.maxVisible

  if (total <= max) {
    for (let i = 1; i <= total; i++) pages.push(i)
    return pages
  }

  const middleSlots = Math.max(1, max - 2)
  const half = Math.floor(middleSlots / 2)

  let start = current - half
  let end = start + middleSlots - 1

  if (start < 2) {
    start = 2
    end = start + middleSlots - 1
  }

  if (end > total - 1) {
    end = total - 1
    start = Math.max(2, end - middleSlots + 1)
  }

  pages.push(1)
  if (start > 2) pages.push('...')

  for (let i = start; i <= end; i++) pages.push(i)

  if (end < total - 1) pages.push('...')
  pages.push(total)

  return pages
})

function goTo(page) {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    emit('change', page)
  }
}
</script>
