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
              :disabled="borrowing"
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
import { ArrowLeft, BookOpen } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const book = ref(null)
const loading = ref(true)
const borrowing = ref(false)

const user = computed(() => currentUser.value)
const bookId = computed(() => route.params.id)

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
  } catch (e) {
    showError(e.message || '加载图书失败')
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  router.push('/login/')
}

async function handleBorrow() {
  borrowing.value = true
  try {
    await post('/api/borrows', { book_id: parseInt(bookId.value) })
    success('借阅成功！')
    await loadBook()
  } catch (e) {
    showError(e.message || '借阅失败')
  } finally {
    borrowing.value = false
  }
}
</script>
