<template>
  <div>
    <h1 class="text-xl md:text-2xl font-semibold text-text-primary mb-4 md:mb-8">逾期通知</h1>

      <!-- 逾期用户预览 -->
      <section class="bg-white rounded-2xl border border-border p-4 md:p-8 mb-4 md:mb-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-medium text-text-primary">逾期用户预览</h2>
          <button @click="loadPreview" :disabled="loadingPreview" class="btn-secondary text-sm">
            {{ loadingPreview ? '刷新中...' : '刷新' }}
          </button>
        </div>

        <div v-if="loadingPreview" class="text-center py-12 text-text-muted">
          加载中...
        </div>

        <div v-else-if="!preview || preview.results?.length === 0" class="text-center py-12 text-text-muted">
          暂无逾期用户
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-sidebar border-b border-border">
              <tr>
                <th class="px-5 py-4 text-left text-sm font-medium text-text-secondary">用户</th>
                <th class="px-5 py-4 text-left text-sm font-medium text-text-secondary">邮箱</th>
                <th class="px-5 py-4 text-left text-sm font-medium text-text-secondary">逾期数量</th>
                <th class="px-5 py-4 text-left text-sm font-medium text-text-secondary">今日已发</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr v-for="item in preview.results" :key="item.user.id" class="hover:bg-sidebar transition-colors">
                <td class="px-5 py-4 text-sm font-medium text-text-primary">{{ item.user.username }}</td>
                <td class="px-5 py-4 text-sm text-text-muted">
                  {{ item.user.mail || '(无邮箱)' }}
                </td>
                <td class="px-5 py-4 text-sm">
                  <span class="text-red-500 font-semibold">{{ item.items.length }} 本</span>
                </td>
                <td class="px-5 py-4">
                  <span v-if="!item.user.mail" class="text-text-light">-</span>
                  <span v-else-if="item.already_sent" class="text-emerald-500 font-medium">已发</span>
                  <span v-else class="text-text-muted">未发</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 发送选项 -->
      <section class="bg-white rounded-2xl border border-border p-4 md:p-8">
        <h2 class="text-lg font-medium text-text-primary mb-6">发送选项</h2>

        <div class="space-y-4 mb-8">
          <label class="flex items-center gap-3 text-sm text-text-secondary cursor-pointer">
            <input v-model="sendDryRun" type="checkbox" class="rounded border-border text-claude-500 focus:ring-claude-400" />
            试运行（仅预览，不发送邮件）
          </label>
          <label class="flex items-center gap-3 text-sm text-text-secondary cursor-pointer">
            <input v-model="sendForce" type="checkbox" class="rounded border-border text-claude-500 focus:ring-claude-400" />
            强制发送（忽略今日已发送）
          </label>
        </div>

        <button
          @click="handleSend"
          :disabled="sending"
          class="btn-primary"
        >
          {{ sending ? '发送中...' : '发送逾期通知邮件' }}
        </button>

        <!-- 发送结果 -->
        <div v-if="sendResult" class="mt-8 p-6 bg-sidebar rounded-xl">
          <h3 class="font-medium text-text-primary mb-4">发送结果</h3>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div class="text-2xl font-semibold text-emerald-600">{{ sendResult.sent }}</div>
              <div class="text-xs text-text-muted mt-1">已发送</div>
            </div>
            <div>
              <div class="text-2xl font-semibold text-text-muted">{{ sendResult.skipped_no_mail }}</div>
              <div class="text-xs text-text-muted mt-1">无邮箱</div>
            </div>
            <div>
              <div class="text-2xl font-semibold text-text-muted">{{ sendResult.skipped_already_sent }}</div>
              <div class="text-xs text-text-muted mt-1">已发过</div>
            </div>
            <div>
              <div class="text-2xl font-semibold text-red-500">{{ sendResult.failed }}</div>
              <div class="text-xs text-text-muted mt-1">失败</div>
            </div>
          </div>
        </div>
      </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { get, post } from '@utils/api'
import { success, error as showError } from '@utils/toast'

const preview = ref(null)
const loadingPreview = ref(true)
const sendDryRun = ref(false)
const sendForce = ref(false)
const sending = ref(false)
const sendResult = ref(null)

onMounted(async () => {
  await loadPreview()
})

async function loadPreview() {
  loadingPreview.value = true
  try {
    const data = await get('/api/admin/overdue/preview')
    preview.value = data
  } catch (e) {
    showError(e.message || '加载失败')
  } finally {
    loadingPreview.value = false
  }
}

async function handleSend() {
  sending.value = true
  sendResult.value = null

  try {
    const params = new URLSearchParams()
    if (sendDryRun.value) params.set('dry_run', '1')
    if (sendForce.value) params.set('force', '1')

    const result = await post('/api/admin/overdue/send?' + params.toString())
    sendResult.value = result

    if (result.sent > 0) {
      success(`成功发送 ${result.sent} 封邮件`)
    } else if (sendDryRun.value) {
      success('试运行完成')
    } else {
      success('没有需要发送的邮件')
    }

    // 刷新预览
    await loadPreview()
  } catch (e) {
    showError(e.message || '发送失败')
  } finally {
    sending.value = false
  }
}
</script>
