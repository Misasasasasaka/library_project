<template>
  <div>
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4 md:mb-8">
      <h1 class="text-xl md:text-2xl font-semibold text-text-primary">借阅记录</h1>
      <button @click="exportCsv" class="btn-secondary">
        导出 CSV
      </button>
    </div>

    <!-- 搜索和筛选 -->
    <div class="flex flex-col md:flex-row items-stretch md:items-center gap-3 md:gap-4 mb-6">
      <div class="flex-1 relative">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索用户名、书名..."
          class="w-full pl-12 pr-4 py-2.5 input"
          @keyup.enter="loadBorrows"
        />
        <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" :stroke-width="2" />
      </div>
      <select v-model="statusFilter" class="input w-full md:w-40" @change="loadBorrows">
        <option value="">全部状态</option>
        <option value="borrowed">借阅中</option>
        <option value="overdue">逾期</option>
        <option value="returned">已归还</option>
      </select>
      <button @click="loadBorrows" class="btn-primary">搜索</button>
    </div>

    <!-- 借阅列表 -->
    <DataTable
      :columns="columns"
      :data="pagedBorrows"
      :loading="loading"
      row-key="id"
    >
      <template #user="{ row }">
        <div>
          <div class="font-medium text-text-primary">{{ row.user?.username }}</div>
          <div class="text-xs text-text-muted">{{ row.user?.mail || '-' }}</div>
        </div>
      </template>
      <template #book="{ row }">
        <div>
          <div class="font-medium text-text-primary">{{ row.book?.title }}</div>
          <div class="text-xs text-text-muted font-mono">{{ row.book?.isbn }}</div>
        </div>
      </template>
      <template #copy="{ row }">
        <span class="font-mono text-xs bg-sidebar px-2 py-1 rounded">{{ row.copy?.code || '-' }}</span>
      </template>
      <template #borrow_date="{ value }">
        <span class="whitespace-nowrap">{{ formatDate(value) }}</span>
      </template>
      <template #due_date="{ value }">
        <span class="whitespace-nowrap">{{ formatDate(value) }}</span>
      </template>
      <template #return_date="{ value }">
        <span class="whitespace-nowrap">{{ value ? formatDate(value) : '-' }}</span>
      </template>
      <template #status="{ row }">
        <span
          :class="[
            'inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-lg whitespace-nowrap',
            getStatusClass(row)
          ]"
        >
          {{ getStatusText(row) }}
        </span>
      </template>
      <template #actions="{ row }">
        <button
          v-if="!row.return_date"
          @click="confirmForceReturn(row)"
          class="btn-danger px-2.5 py-1 text-xs whitespace-nowrap"
        >
          强制归还
        </button>
        <span v-else class="text-text-light text-sm">-</span>
      </template>
    </DataTable>

    <!-- 分页 -->
    <div class="mt-8">
      <Pagination
        :current-page="currentPage"
        :total-pages="totalPages"
        @change="handlePageChange"
      />
    </div>

    <!-- 强制归还确认弹窗 -->
    <Modal v-model="showReturnModal" title="确认强制归还" size="sm">
      <p class="text-text-secondary">
        确认将《{{ returningBorrow?.book?.title }}》从 {{ returningBorrow?.user?.username }} 的借阅中强制归还吗？
      </p>
      <template #footer>
        <button @click="showReturnModal = false" class="btn-secondary">取消</button>
        <button @click="handleForceReturn" :disabled="returning" class="btn-danger">
          {{ returning ? '归还中...' : '确认归还' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import DataTable from '@components/DataTable.vue'
import Modal from '@components/Modal.vue'
import Pagination from '@components/Pagination.vue'
import { get, post, download } from '@utils/api'
import { success, error as showError } from '@utils/toast'
import { Search } from 'lucide-vue-next'

const PAGE_SIZE = 20

const columns = [
  { key: 'id', title: 'ID', width: '60px' },
  { key: 'user', title: '用户' },
  { key: 'book', title: '图书' },
  { key: 'copy', title: '副本', width: '90px' },
  { key: 'borrow_date', title: '借阅日期', width: '110px' },
  { key: 'due_date', title: '应还日期', width: '110px' },
  { key: 'return_date', title: '归还日期', width: '110px' },
  { key: 'status', title: '状态', width: '110px' },
  { key: 'actions', title: '操作', width: '120px' },
]

const borrows = ref([])
const serverPaginated = ref(false)
const loading = ref(true)
const searchKeyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const totalCount = ref(0)
const showReturnModal = ref(false)
const returningBorrow = ref(null)
const returning = ref(false)

const filteredBorrows = computed(() => {
  if (serverPaginated.value) return borrows.value

  let list = borrows.value

  // 后端 borrowed 过滤不会排除逾期，这里做一次修正
  if (statusFilter.value === 'borrowed') {
    list = list.filter(b => !b.return_date && !b.is_overdue)
  }

  const kw = searchKeyword.value.trim().toLowerCase()
  if (!kw) return list

  return list.filter(b => {
    const user = b.user?.username || ''
    const title = b.book?.title || ''
    const isbn = b.book?.isbn || ''
    return [user, title, isbn].some(v => String(v).toLowerCase().includes(kw))
  })
})

const totalPages = computed(() => {
  const count = serverPaginated.value ? totalCount.value : filteredBorrows.value.length
  return Math.max(1, Math.ceil(count / PAGE_SIZE))
})

const pagedBorrows = computed(() => {
  if (serverPaginated.value) return borrows.value
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredBorrows.value.slice(start, start + PAGE_SIZE)
})

onMounted(async () => {
  await loadBorrows()
})

watch([serverPaginated, filteredBorrows], () => {
  if (serverPaginated.value) return
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  if (currentPage.value < 1) currentPage.value = 1
})

async function loadBorrows({ keepPage = false } = {}) {
  if (!keepPage) currentPage.value = 1
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchKeyword.value) params.set('kw', searchKeyword.value)
    if (statusFilter.value) params.set('status', statusFilter.value)
    params.set('page', currentPage.value)

    const data = await get('/api/borrows?' + params.toString())
    const results = data.results || data.borrows || []
    borrows.value = results
    totalCount.value = data.count || results.length
    serverPaginated.value = !!(data.count && data.count > results.length)
  } catch (e) {
    showError(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
  if (serverPaginated.value) {
    loadBorrows({ keepPage: true })
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function getStatusText(borrow) {
  if (borrow.return_date) return '已归还'
  if (borrow.is_overdue) return '逾期'
  return '借阅中'
}

function getStatusClass(borrow) {
  if (borrow.return_date) return 'bg-border-light text-text-muted'
  if (borrow.is_overdue) return 'bg-red-50 text-red-600'
  return 'bg-claude-50 text-claude-600'
}

async function exportCsv() {
  try {
    await download('/api/admin/borrows/export', 'borrows.csv')
    success('导出成功')
  } catch (e) {
    showError(e.message || '导出失败')
  }
}

function confirmForceReturn(borrow) {
  returningBorrow.value = borrow
  showReturnModal.value = true
}

async function handleForceReturn() {
  if (!returningBorrow.value) return

  returning.value = true
  try {
    await post(`/api/borrows/${returningBorrow.value.id}/return`)
    success('已强制归还')
    showReturnModal.value = false
    returningBorrow.value = null
    await loadBorrows({ keepPage: true })
  } catch (e) {
    showError(e.message || '归还失败')
  } finally {
    returning.value = false
  }
}
</script>
