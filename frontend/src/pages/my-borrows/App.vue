<template>
  <div>
    <h1 class="text-xl md:text-2xl font-semibold text-text-primary mb-4 md:mb-8">我的借阅</h1>

    <div v-if="loading" class="text-center py-16 text-text-muted">
      加载中...
    </div>

    <template v-else>
      <!-- 当前借阅 -->
      <section class="mb-10">
        <h2 class="text-lg font-medium text-text-primary mb-4 flex items-center">
          <span class="w-1 h-5 bg-claude-500 rounded mr-3"></span>
          当前借阅
        </h2>

        <div v-if="currentBorrows.length === 0" class="text-center py-12 text-text-muted bg-white rounded-2xl border border-border">
          暂无借阅记录
        </div>

        <div v-else class="space-y-4">
          <BorrowCard
            v-for="borrow in currentBorrows"
            :key="borrow.id"
            :borrow="borrow"
            :loading="operatingId === borrow.id"
            @renew="handleRenew"
            @return="handleReturn"
          />
        </div>
      </section>

      <!-- 历史记录 -->
      <section>
        <h2 class="text-lg font-medium text-text-primary mb-4 flex items-center">
          <span class="w-1 h-5 bg-text-light rounded mr-3"></span>
          历史记录
        </h2>

        <div v-if="historyBorrows.length === 0" class="text-center py-12 text-text-muted bg-white rounded-2xl border border-border">
          暂无历史记录
        </div>

        <div v-else class="bg-white rounded-2xl border border-border overflow-x-auto">
          <table class="w-full">
            <thead class="bg-sidebar border-b border-border">
              <tr>
                <th class="px-6 py-4 text-left text-sm font-medium text-text-secondary">书名</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-text-secondary">副本</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-text-secondary">借阅日期</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-text-secondary">归还日期</th>
                <th class="px-6 py-4 text-left text-sm font-medium text-text-secondary">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr v-for="borrow in historyBorrows" :key="borrow.id" class="hover:bg-sidebar transition-colors">
                <td class="px-6 py-4 text-sm text-text-primary">{{ borrow.book?.title }}</td>
                <td class="px-6 py-4 text-sm text-text-muted font-mono">{{ borrow.copy?.code || '-' }}</td>
                <td class="px-6 py-4 text-sm text-text-muted">{{ formatDate(borrow.borrow_date) }}</td>
                <td class="px-6 py-4 text-sm text-text-muted">{{ formatDate(borrow.return_date) }}</td>
                <td class="px-6 py-4">
                  <span class="inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg bg-border-light text-text-muted">
                    已归还
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BorrowCard from '@components/BorrowCard.vue'
import { get, post } from '@utils/api'
import { currentUser, isAdmin } from '@utils/auth'
import { success, error as showError } from '@utils/toast'

const borrows = ref([])
const loading = ref(true)
const operatingId = ref(null)

const currentBorrows = computed(() =>
  borrows.value.filter(b => !b.return_date)
)

const historyBorrows = computed(() =>
  borrows.value.filter(b => b.return_date)
)

onMounted(async () => {
  await loadBorrows()
})

async function loadBorrows() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (isAdmin() && currentUser.value?.id != null) {
      params.set('user_id', String(currentUser.value.id))
    }
    const url = '/api/borrows' + (params.toString() ? `?${params.toString()}` : '')
    const data = await get(url)
    borrows.value = data.results || data.borrows || []
  } catch (e) {
    showError(e.message || '加载借阅记录失败')
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function parseYmd(dateStr) {
  const [y, m, d] = String(dateStr || '').split('-').map(Number)
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

function formatYmd(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

async function handleRenew(id) {
  operatingId.value = id
  try {
    const borrow = borrows.value.find(b => b.id === id)
    const baseDate = parseYmd(borrow?.due_date) || new Date()
    const nextDue = new Date(baseDate)
    nextDue.setDate(nextDue.getDate() + 14)
    await post(`/api/borrows/${id}/renew`, { due_date: formatYmd(nextDue) })
    success('续借成功！')
    await loadBorrows()
  } catch (e) {
    showError(e.message || '续借失败')
  } finally {
    operatingId.value = null
  }
}

async function handleReturn(id) {
  operatingId.value = id
  try {
    await post(`/api/borrows/${id}/return`)
    success('归还成功！')
    await loadBorrows()
  } catch (e) {
    showError(e.message || '归还失败')
  } finally {
    operatingId.value = null
  }
}
</script>
