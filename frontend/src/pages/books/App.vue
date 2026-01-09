<template>
  <div>
    <!-- 搜索栏 -->
    <div class="mb-4 md:mb-8">
      <div class="flex flex-col md:flex-row items-stretch md:items-center gap-3 md:gap-4">
        <div class="flex-1 relative">
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索书名、作者、ISBN..."
            class="w-full pl-12 pr-4 py-3 input"
            @keyup.enter="handleSearch"
          />
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" :stroke-width="2" />
        </div>
        <button
          @click="handleSearch"
          class="btn-primary px-6 py-3"
        >
          搜索
        </button>
      </div>
    </div>

    <!-- 分类标签 -->
    <div class="mb-4 md:mb-8 flex flex-wrap gap-2">
      <button
        v-for="cat in categories"
        :key="cat.id ?? 'all'"
        @click="selectCategory(cat.id)"
        :class="[
          'px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200',
          selectedCategory === cat.id
            ? 'bg-claude-500 text-white shadow-sm'
            : 'bg-white text-text-secondary border border-border hover:border-claude-400 hover:text-claude-600'
        ]"
      >
        {{ cat.name }}
      </button>
    </div>

    <!-- 图书列表 -->
    <div v-if="loading" class="text-center py-16 text-text-muted">
      <Loader2 class="animate-spin h-10 w-10 mx-auto mb-4 text-claude-500" :stroke-width="2" />
      加载中...
    </div>

    <div v-else-if="books.length === 0" class="text-center py-16 text-text-muted">
      <BookOpen class="w-20 h-20 mx-auto mb-4 text-text-light" :stroke-width="1" />
      <p class="text-lg">暂无图书</p>
    </div>

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 md:gap-6">
      <BookCard
        v-for="book in pagedBooks"
        :key="book.id"
        :book="book"
      />
    </div>

    <!-- 分页 -->
    <div class="mt-10">
      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import BookCard from '@components/BookCard.vue'
import Pagination from '@components/Pagination.vue'
import { get } from '@utils/api'
import { error as showError } from '@utils/toast'
import { Search, Loader2, BookOpen } from 'lucide-vue-next'

const PAGE_SIZE = 20

const searchKeyword = ref('')
const selectedCategory = ref(null)
const books = ref([])
const serverPaginated = ref(false)
const categories = ref([{ id: null, name: '全部' }])
const loading = ref(true)
const currentPage = ref(1)
const totalCount = ref(0)

const totalPages = computed(() => Math.ceil(totalCount.value / PAGE_SIZE))
const pagedBooks = computed(() => {
  if (serverPaginated.value) return books.value
  const start = (currentPage.value - 1) * PAGE_SIZE
  return books.value.slice(start, start + PAGE_SIZE)
})

onMounted(async () => {
  await loadBooks()
})

async function loadBooks() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchKeyword.value) params.set('kw', searchKeyword.value)
    if (selectedCategory.value) params.set('category', selectedCategory.value)
    params.set('page', currentPage.value)

    const url = '/api/books' + (params.toString() ? '?' + params.toString() : '')
    const data = await get(url)

    const results = data.results || data.books || []
    books.value = results
    totalCount.value = data.count || results.length
    serverPaginated.value = !!(data.count && data.count > results.length)

    // 从结果集中提取可用分类（后端暂未提供 categories API）
    const catMap = new Map()
    results.forEach(book => {
      const cat = book.category
      if (cat?.id != null) catMap.set(cat.id, cat.name)
    })
    const catList = Array.from(catMap, ([id, name]) => ({ id, name }))
      .sort((a, b) => String(a.name).localeCompare(String(b.name), 'zh-CN'))
    categories.value = [{ id: null, name: '全部' }, ...catList]
  } catch (e) {
    showError(e.message || '加载图书失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadBooks()
}

function selectCategory(catId) {
  selectedCategory.value = catId
  currentPage.value = 1
  loadBooks()
}

function handlePageChange(page) {
  currentPage.value = page
  if (serverPaginated.value) loadBooks()
}
</script>
