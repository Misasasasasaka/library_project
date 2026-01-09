<template>
  <div>
    <h1 class="text-xl md:text-2xl font-semibold text-text-primary mb-4 md:mb-8">导入 / 导出</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8">
      <!-- 导出 -->
      <section class="bg-white rounded-2xl border border-border p-4 md:p-8">
        <h2 class="text-lg font-medium text-text-primary mb-4">导出数据</h2>
        <p class="text-sm text-text-muted mb-6">将数据导出为 CSV 文件，可用于备份或在其他系统中使用。</p>

        <div class="space-y-3">
          <button @click="exportBooks" class="w-full btn-secondary flex items-center justify-center gap-2">
            <Download class="w-5 h-5" :stroke-width="1.75" />
            导出图书 CSV
          </button>
          <button @click="exportBorrows" class="w-full btn-secondary flex items-center justify-center gap-2">
            <Download class="w-5 h-5" :stroke-width="1.75" />
            导出借阅记录 CSV
          </button>
        </div>
      </section>

      <!-- 导入 -->
      <section class="bg-white rounded-2xl border border-border p-4 md:p-8">
        <h2 class="text-lg font-medium text-text-primary mb-4">导入数据</h2>
        <p class="text-sm text-text-muted mb-6">上传 CSV 文件批量导入图书数据。支持新增和更新（按 ISBN 匹配）。</p>

        <FileUpload
          ref="fileUploadRef"
          accept=".csv"
          hint="支持 UTF-8 编码的 CSV 文件"
          @change="handleFileChange"
        />

        <div class="mt-5 space-y-3">
          <label class="flex items-center gap-3 text-sm text-text-secondary cursor-pointer">
            <input v-model="dryRun" type="checkbox" class="rounded border-border text-claude-500 focus:ring-claude-400" />
            试运行（仅预览，不写入数据库）
          </label>
          <label class="flex items-center gap-3 text-sm text-text-secondary cursor-pointer">
            <input v-model="atomic" type="checkbox" class="rounded border-border text-claude-500 focus:ring-claude-400" />
            原子导入（任一行失败则全部回滚）
          </label>
        </div>

        <button
          @click="handleImport"
          :disabled="!selectedFile || importing"
          class="mt-5 w-full btn-primary"
        >
          {{ importing ? '导入中...' : '开始导入' }}
        </button>
      </section>
    </div>

    <!-- 导入结果 -->
    <section v-if="importResult" class="mt-4 md:mt-8 bg-white rounded-2xl border border-border p-4 md:p-8">
      <h2 class="text-lg font-medium text-text-primary mb-6">导入结果</h2>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="text-center p-5 bg-emerald-50 rounded-xl">
          <div class="text-3xl font-semibold text-emerald-600">{{ importResult.created }}</div>
          <div class="text-sm text-text-muted mt-1">新增</div>
        </div>
        <div class="text-center p-5 bg-claude-50 rounded-xl">
          <div class="text-3xl font-semibold text-claude-600">{{ importResult.updated }}</div>
          <div class="text-sm text-text-muted mt-1">更新</div>
        </div>
        <div class="text-center p-5 bg-sidebar rounded-xl">
          <div class="text-3xl font-semibold text-text-muted">{{ importResult.skipped }}</div>
          <div class="text-sm text-text-muted mt-1">跳过</div>
        </div>
        <div class="text-center p-5 bg-red-50 rounded-xl">
          <div class="text-3xl font-semibold text-red-500">{{ importResult.errors?.length || 0 }}</div>
          <div class="text-sm text-text-muted mt-1">错误</div>
        </div>
      </div>

      <div v-if="importResult.applied === false" class="p-4 bg-amber-50 text-amber-700 text-sm rounded-xl mb-6">
        {{ dryRun ? '试运行模式：数据未写入数据库' : '原子导入失败：所有更改已回滚' }}
      </div>

      <!-- 错误列表 -->
      <div v-if="importResult.errors?.length">
        <h3 class="text-sm font-medium text-text-primary mb-3">错误详情</h3>
        <div class="max-h-60 overflow-auto border border-border rounded-xl">
          <table class="w-full text-sm">
            <thead class="bg-sidebar sticky top-0">
              <tr>
                <th class="px-4 py-3 text-left text-text-secondary">行号</th>
                <th class="px-4 py-3 text-left text-text-secondary">ISBN</th>
                <th class="px-4 py-3 text-left text-text-secondary">错误信息</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-border">
              <tr v-for="err in importResult.errors" :key="err.row" class="hover:bg-sidebar">
                <td class="px-4 py-3">{{ err.row }}</td>
                <td class="px-4 py-3 font-mono text-xs">{{ err.isbn }}</td>
                <td class="px-4 py-3 text-red-600">{{ err.message }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import FileUpload from '@components/FileUpload.vue'
import { download, upload } from '@utils/api'
import { success, error as showError } from '@utils/toast'
import { Download } from 'lucide-vue-next'

const fileUploadRef = ref(null)
const selectedFile = ref(null)
const dryRun = ref(true)
const atomic = ref(false)
const importing = ref(false)
const importResult = ref(null)

function handleFileChange(file) {
  selectedFile.value = file
  importResult.value = null
}

async function exportBooks() {
  try {
    await download('/api/admin/books/export', 'books.csv')
    success('导出成功')
  } catch (e) {
    showError(e.message || '导出失败')
  }
}

async function exportBorrows() {
  try {
    await download('/api/admin/borrows/export', 'borrows.csv')
    success('导出成功')
  } catch (e) {
    showError(e.message || '导出失败')
  }
}

async function handleImport() {
  if (!selectedFile.value) return

  importing.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const params = {}
    if (dryRun.value) params.dry_run = '1'
    if (atomic.value) params.atomic = '1'

    const result = await upload('/api/admin/books/import', formData, params)
    importResult.value = result

    if (result.applied) {
      success(`导入成功：新增 ${result.created}，更新 ${result.updated}`)
    }
  } catch (e) {
    showError(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}
</script>
