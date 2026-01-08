<template>
  <div>
    <!-- 返回按钮 -->
    <router-link to="/books/" class="inline-flex items-center text-text-muted hover:text-claude-600 mb-6 transition-colors">
      <ArrowLeft class="w-5 h-5 mr-2" :stroke-width="2" />
      返回图书列表
    </router-link>

    <div v-if="loading" class="text-center py-16 text-text-muted">
      加载中...
    </div>

    <div v-else-if="!book" class="text-center py-16 text-text-muted">
      图书不存在
    </div>

    <div v-else class="bg-white rounded-2xl border border-border p-8">
      <div class="flex gap-10">
        <!-- 封面 -->
        <div class="w-56 flex-shrink-0">
          <div class="aspect-[3/4] bg-sidebar rounded-2xl overflow-hidden shadow-sm">
            <img
              v-if="book.cover_url"
              :src="book.cover_url"
              :alt="book.title"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-text-light">
              <BookOpen class="w-20 h-20" :stroke-width="1" />
            </div>
          </div>
        </div>

        <!-- 信息 -->
        <div class="flex-1">
          <h1 class="text-3xl font-semibold text-text-primary">{{ book.title }}</h1>

          <div class="mt-6 space-y-3 text-text-secondary">
            <p><span class="text-text-muted">作者：</span>{{ book.author }}</p>
            <p v-if="book.publisher"><span class="text-text-muted">出版社：</span>{{ book.publisher }}</p>
            <p v-if="book.isbn"><span class="text-text-muted">ISBN：</span><span class="font-mono">{{ book.isbn }}</span></p>
            <p v-if="book.category?.name"><span class="text-text-muted">分类：</span>{{ book.category.name }}</p>
            <p v-if="book.location"><span class="text-text-muted">位置：</span>{{ book.location }}</p>
            <p>
              <span class="text-text-muted">库存：</span>
              <span :class="book.available_copies > 0 ? 'text-emerald-600 font-medium' : 'text-red-500'">
                可借 {{ book.available_copies }}
              </span>
              <span class="text-text-muted"> / 共 {{ book.total_copies }} 本</span>
            </p>
          </div>

          <!-- 借阅按钮 -->
          <div class="mt-8">
            <div v-if="book.available_copies > 0" class="mb-5">
              <label class="block text-sm font-medium text-text-secondary mb-2">选择副本</label>
              <div class="relative w-56">
                <button
                  type="button"
                  @click="dropdownOpen = !dropdownOpen"
                  :disabled="availableCopies.length === 0"
                  class="w-full flex items-center justify-between px-4 py-3 bg-white border border-border rounded-xl text-left transition-all duration-200 hover:border-claude-300 focus:outline-none focus:ring-2 focus:ring-claude-500/20 focus:border-claude-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-claude-50 rounded-lg flex items-center justify-center">
                      <Hash class="w-4 h-4 text-claude-500" :stroke-width="2" />
                    </div>
                    <span class="text-text-primary font-medium">{{ selectedCopyCode || '请选择' }}</span>
                  </div>
                  <ChevronDown
                    class="w-5 h-5 text-text-muted transition-transform duration-200"
                    :class="{ 'rotate-180': dropdownOpen }"
                    :stroke-width="2"
                  />
                </button>
                <transition
                  enter-active-class="transition ease-out duration-150"
                  enter-from-class="opacity-0 translate-y-1"
                  enter-to-class="opacity-100 translate-y-0"
                  leave-active-class="transition ease-in duration-100"
                  leave-from-class="opacity-100 translate-y-0"
                  leave-to-class="opacity-0 translate-y-1"
                >
                  <div
                    v-if="dropdownOpen"
                    class="absolute z-20 mt-2 w-full bg-white border border-border rounded-xl shadow-lg overflow-hidden"
                  >
                    <div class="max-h-48 overflow-y-auto py-1">
                      <button
                        v-for="c in availableCopies"
                        :key="c.copy_no"
                        type="button"
                        @click="selectCopy(c.copy_no)"
                        class="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-claude-50"
                        :class="selectedCopyNo === c.copy_no ? 'bg-claude-50' : ''"
                      >
                        <div
                          class="w-8 h-8 rounded-lg flex items-center justify-center"
                          :class="selectedCopyNo === c.copy_no ? 'bg-claude-500 text-white' : 'bg-gray-100 text-text-muted'"
                        >
                          <Hash class="w-4 h-4" :stroke-width="2" />
                        </div>
                        <span
                          class="font-medium"
                          :class="selectedCopyNo === c.copy_no ? 'text-claude-600' : 'text-text-primary'"
                        >{{ c.code }}</span>
                        <Check
                          v-if="selectedCopyNo === c.copy_no"
                          class="w-4 h-4 text-claude-500 ml-auto"
                          :stroke-width="2.5"
                        />
                      </button>
                    </div>
                  </div>
                </transition>
                <div v-if="dropdownOpen" @click="dropdownOpen = false" class="fixed inset-0 z-10"></div>
              </div>
            </div>
            <button
              v-if="!user"
              @click="goToLogin"
              class="btn-primary px-8 py-3 text-base"
            >
              登录后借阅
            </button>
            <button
              v-else-if="book.available_copies === 0"
              disabled
              class="btn-primary px-8 py-3 text-base opacity-50 cursor-not-allowed"
            >
              暂无库存
            </button>
            <button
              v-else
              @click="handleBorrow"
              :disabled="borrowing || !selectedCopyNo"
              class="btn-primary px-8 py-3 text-base"
            >
              {{ borrowing ? '借阅中...' : '立即借阅' }}
            </button>
          </div>

          <!-- 描述 -->
          <div v-if="book.description" class="mt-10 pt-8 border-t border-border">
            <h3 class="text-lg font-medium text-text-primary mb-3">简介</h3>
            <p class="text-text-secondary leading-relaxed">{{ book.description }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { currentUser } from '@utils/auth'
import { get, post } from '@utils/api'
import { success, error as showError } from '@utils/toast'
import { ArrowLeft, BookOpen, Hash, ChevronDown, Check } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const book = ref(null)
const loading = ref(true)
const borrowing = ref(false)
const availableCopies = ref([])
const selectedCopyNo = ref(null)
const dropdownOpen = ref(false)

const user = computed(() => currentUser.value)
const bookId = computed(() => route.params.id)
const selectedCopyCode = computed(() => {
  const copy = availableCopies.value.find(c => c.copy_no === selectedCopyNo.value)
  return copy?.code || ''
})

onMounted(async () => {
  await loadBook()
})

// 监听路由参数变化，重新加载图书
watch(() => route.params.id, () => {
  loadBook()
})

async function loadBook() {
  loading.value = true
  try {
    const data = await get(`/api/books/${bookId.value}`)
    book.value = data.book
    await loadAvailableCopies()
  } catch (e) {
    showError(e.message || '加载图书失败')
    availableCopies.value = []
    selectedCopyNo.value = null
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  router.push('/login/')
}

function selectCopy(copyNo) {
  selectedCopyNo.value = copyNo
  dropdownOpen.value = false
}

async function handleBorrow() {
  if (!selectedCopyNo.value) return
  borrowing.value = true
  try {
    await post('/api/borrows', { book_id: parseInt(bookId.value), copy_no: selectedCopyNo.value })
    success('借阅成功！')
    await loadBook()
  } catch (e) {
    showError(e.message || '借阅失败')
  } finally {
    borrowing.value = false
  }
}

async function loadAvailableCopies() {
  if (!bookId.value) return
  try {
    const data = await get(`/api/books/${bookId.value}/available-copies`)
    const results = data.results || []
    availableCopies.value = results
    selectedCopyNo.value = results[0]?.copy_no ?? null
  } catch (e) {
    availableCopies.value = []
    selectedCopyNo.value = null
  }
}
</script>
