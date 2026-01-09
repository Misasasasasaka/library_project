<template>
  <router-link
    :to="{ name: 'book-detail', params: { id: book.id } }"
    class="block bg-white rounded-2xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden border border-border hover:-translate-y-0.5"
  >
    <!-- 封面 -->
    <div class="aspect-[3/4] bg-sidebar relative">
      <img
        v-if="book.cover_url"
        :src="book.cover_url"
        :alt="book.title"
        class="w-full h-full object-cover"
      />
      <div
        v-else
        class="w-full h-full flex items-center justify-center text-text-light"
      >
        <BookOpen class="w-16 h-16" :stroke-width="1" />
      </div>
    </div>

    <!-- 信息 -->
    <div class="p-3 md:p-4">
      <h3 class="font-medium text-text-primary truncate text-sm md:text-base" :title="book.title">
        {{ book.title }}
      </h3>
      <p class="text-xs md:text-sm text-text-muted truncate mt-1">{{ book.author }}</p>

      <!-- 状态标签 -->
      <div class="mt-2 md:mt-3">
        <span
          :class="[
            'inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg',
            statusClass
          ]"
        >
          <span class="w-1.5 h-1.5 rounded-full mr-1.5" :class="dotClass"></span>
          {{ statusText }}
        </span>
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { BookOpen } from 'lucide-vue-next'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const canBorrow = computed(() => {
  return props.book.status === 'on_shelf' && props.book.available_copies > 0
})

const statusText = computed(() => {
  if (props.book.status === 'off_shelf') return '已下架'
  if (props.book.available_copies === 0) return '已借完'
  return '可借阅'
})

const statusClass = computed(() => {
  if (!canBorrow.value) return 'bg-border-light text-text-muted'
  return 'bg-emerald-50 text-emerald-600'
})

const dotClass = computed(() => {
  if (!canBorrow.value) return 'bg-text-muted'
  return 'bg-emerald-500'
})
</script>
