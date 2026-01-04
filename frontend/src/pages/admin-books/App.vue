<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-semibold text-text-primary">图书管理</h1>
      <div class="flex gap-3">
        <button @click="openAddModal" class="btn-primary">
          + 新增图书
        </button>
        <button @click="openCategoryManager" class="btn-secondary">
          分类管理
        </button>
        <router-link to="/manage/import-export/" class="btn-secondary">
          导入/导出
        </router-link>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="flex items-center gap-4 mb-6">
      <div class="flex-1 relative">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索书名、作者、ISBN..."
          class="w-full pl-12 pr-4 py-2.5 input"
          @keyup.enter="loadBooks"
        />
        <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" :stroke-width="2" />
      </div>
      <select v-model="statusFilter" class="input w-40" @change="loadBooks">
        <option value="">全部状态</option>
        <option value="on_shelf">已上架</option>
        <option value="off_shelf">已下架</option>
      </select>
      <button @click="loadBooks" class="btn-primary">搜索</button>
    </div>

    <!-- 图书列表 -->
    <DataTable
      :columns="columns"
      :data="pagedBooks"
      :loading="loading"
      row-key="id"
    >
      <template #isbn="{ value }">
        <span class="font-mono text-xs bg-sidebar px-2 py-1 rounded">{{ value }}</span>
      </template>
      <template #status="{ row }">
        <span
          :class="[
            'inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg',
            row.status === 'on_shelf' ? 'bg-emerald-50 text-emerald-600' : 'bg-border-light text-text-muted'
          ]"
        >
          {{ row.status === 'on_shelf' ? '上架' : '下架' }}
        </span>
      </template>
      <template #copies="{ row }">
        <span class="text-text-secondary">{{ row.available_copies }}</span>
        <span class="text-text-muted"> / {{ row.total_copies }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex gap-3">
          <button @click="editBook(row)" class="text-claude-600 hover:text-claude-700 text-sm font-medium">
            编辑
          </button>
          <button
            @click="toggleStatus(row)"
            class="text-amber-600 hover:text-amber-700 text-sm font-medium"
          >
            {{ row.status === 'on_shelf' ? '下架' : '上架' }}
          </button>
          <button @click="confirmDelete(row)" class="text-red-500 hover:text-red-600 text-sm font-medium">
            删除
          </button>
        </div>
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

    <!-- 新增/编辑弹窗 -->
    <Modal
      v-model="showAddModal"
      :title="editingBook ? '编辑图书' : '新增图书'"
      size="lg"
      @close="closeFormModal"
    >
      <form @submit.prevent="handleSubmit">
        <div class="grid grid-cols-2 gap-5">
          <div>
            <label class="label">ISBN <span class="text-red-500">*</span></label>
            <input v-model="form.isbn" type="text" class="input" required />
          </div>
          <div>
            <label class="label">书名 <span class="text-red-500">*</span></label>
            <input v-model="form.title" type="text" class="input" required />
          </div>
          <div>
            <label class="label">作者 <span class="text-red-500">*</span></label>
            <input v-model="form.author" type="text" class="input" required />
          </div>
          <div>
            <label class="label">出版社</label>
            <input v-model="form.publisher" type="text" class="input" />
          </div>
          <div>
            <label class="label">出版日期</label>
            <input v-model="form.publish_date" type="date" class="input" />
          </div>
          <div>
            <label class="label">分类</label>
            <select v-model="form.category_id" class="input">
              <option :value="null">无</option>
              <option v-for="cat in categoryOptions" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="label">总库存</label>
            <input v-model.number="form.total_copies" type="number" min="0" class="input" />
          </div>
          <div>
            <label class="label">位置</label>
            <input v-model="form.location" type="text" class="input" placeholder="如 A-01" />
          </div>
          <div class="col-span-2">
            <label class="label">封面</label>
            <div class="flex items-center gap-4">
              <div class="w-20 h-28 bg-sidebar rounded-xl overflow-hidden border border-border flex-shrink-0">
                <img
                  v-if="coverPreviewUrl"
                  :src="coverPreviewUrl"
                  alt="封面预览"
                  class="w-full h-full object-cover"
                />
                <div v-else class="w-full h-full flex items-center justify-center text-text-light">
                  <BookOpen class="w-8 h-8" :stroke-width="1" />
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <input
                  ref="coverInputRef"
                  type="file"
                  accept="image/*"
                  class="input"
                  @change="handleCoverChange"
                />
                <div class="mt-2 flex items-center justify-between gap-4">
                  <p class="text-xs text-text-muted whitespace-nowrap">支持图片，≤ 5MB</p>
                  <button
                    v-if="coverFile"
                    type="button"
                    class="text-xs text-text-muted hover:text-red-500 whitespace-nowrap"
                    @click="clearCover"
                  >
                    移除
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div class="col-span-2">
            <label class="label">简介</label>
            <textarea v-model="form.description" rows="3" class="input"></textarea>
          </div>
        </div>

        <div v-if="formError" class="mt-4 p-3 bg-red-50 text-red-600 text-sm rounded-xl">
          {{ formError }}
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" @click="closeFormModal" class="btn-secondary">取消</button>
          <button type="submit" :disabled="submitting" class="btn-primary">
            {{ submitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- 删除确认弹窗 -->
    <Modal v-model="showDeleteModal" title="确认删除" size="sm">
      <p class="text-text-secondary">确定要删除《{{ deletingBook?.title }}》吗？此操作不可恢复。</p>
      <template #footer>
        <button @click="showDeleteModal = false" class="btn-secondary">取消</button>
        <button @click="handleDelete" :disabled="deleting" class="btn-danger">
          {{ deleting ? '删除中...' : '确认删除' }}
        </button>
      </template>
    </Modal>

    <!-- 分类管理弹窗 -->
    <Modal v-model="showCategoryManagerModal" title="分类管理" size="lg" @close="closeCategoryManager">
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-text-muted">新增/编辑/删除图书分类</p>
        <button @click="openCategoryForm()" class="btn-primary">
          + 新增分类
        </button>
      </div>

      <DataTable
        :columns="categoryColumns"
        :data="categories"
        :loading="categoriesLoading"
        row-key="id"
        empty-text="暂无分类"
      >
        <template #description="{ value }">
          <span class="text-text-muted">{{ value || '-' }}</span>
        </template>
        <template #actions="{ row }">
          <div class="flex gap-3">
            <button @click="openCategoryForm(row)" class="text-claude-600 hover:text-claude-700 text-sm font-medium">
              编辑
            </button>
            <button @click="confirmCategoryDelete(row)" class="text-red-500 hover:text-red-600 text-sm font-medium">
              删除
            </button>
          </div>
        </template>
      </DataTable>
    </Modal>

    <!-- 新增/编辑分类弹窗 -->
    <Modal
      v-model="showCategoryFormModal"
      :title="editingCategory ? '编辑分类' : '新增分类'"
      size="md"
      @close="closeCategoryForm"
    >
      <form @submit.prevent="handleCategorySubmit">
        <div class="space-y-5">
          <div>
            <label class="label">分类名称 <span class="text-red-500">*</span></label>
            <input v-model="categoryForm.name" type="text" class="input" required />
          </div>
          <div>
            <label class="label">简介</label>
            <textarea v-model="categoryForm.description" rows="3" class="input"></textarea>
          </div>
        </div>

        <div v-if="categoryFormError" class="mt-4 p-3 bg-red-50 text-red-600 text-sm rounded-xl">
          {{ categoryFormError }}
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" @click="closeCategoryForm" class="btn-secondary">取消</button>
          <button type="submit" :disabled="categorySubmitting" class="btn-primary">
            {{ categorySubmitting ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- 删除分类确认弹窗 -->
    <Modal v-model="showCategoryDeleteModal" title="确认删除分类" size="sm">
      <p class="text-text-secondary">
        确定要删除分类「{{ deletingCategory?.name }}」吗？删除后该分类下的图书将变为未分类。
      </p>
      <template #footer>
        <button @click="showCategoryDeleteModal = false" class="btn-secondary">取消</button>
        <button @click="handleCategoryDelete" :disabled="categoryDeleting" class="btn-danger">
          {{ categoryDeleting ? '删除中...' : '确认删除' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import DataTable from '@components/DataTable.vue'
import Modal from '@components/Modal.vue'
import Pagination from '@components/Pagination.vue'
import { get, post, patch, del, upload } from '@utils/api'
import { success, error as showError } from '@utils/toast'
import { BookOpen, Search } from 'lucide-vue-next'

const PAGE_SIZE = 20

const columns = [
  { key: 'isbn', title: 'ISBN', width: '130px' },
  { key: 'title', title: '书名' },
  { key: 'author', title: '作者', width: '120px' },
  { key: 'copies', title: '库存', width: '100px' },
  { key: 'status', title: '状态', width: '90px' },
  { key: 'actions', title: '操作', width: '160px' },
]

const categoryColumns = [
  { key: 'name', title: '分类名称', width: '180px' },
  { key: 'description', title: '简介' },
  { key: 'actions', title: '操作', width: '140px' },
]

const books = ref([])
const categories = ref([])
const serverPaginated = ref(false)
const loading = ref(true)
const categoriesLoading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const totalCount = ref(0)

const showAddModal = ref(false)
const showDeleteModal = ref(false)
const showCategoryManagerModal = ref(false)
const showCategoryFormModal = ref(false)
const showCategoryDeleteModal = ref(false)
const editingBook = ref(null)
const deletingBook = ref(null)
const editingCategory = ref(null)
const deletingCategory = ref(null)
const submitting = ref(false)
const deleting = ref(false)
const categorySubmitting = ref(false)
const categoryDeleting = ref(false)
const formError = ref('')
const categoryFormError = ref('')
const coverInputRef = ref(null)
const coverFile = ref(null)
const coverPreviewUrl = ref('')
let coverObjectUrl = null

const form = reactive({
  isbn: '',
  title: '',
  author: '',
  publisher: '',
  publish_date: '',
  category_id: null,
  total_copies: 1,
  location: '',
  description: '',
})

const categoryForm = reactive({
  name: '',
  description: '',
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / PAGE_SIZE)))
const pagedBooks = computed(() => {
  if (serverPaginated.value) return books.value
  const start = (currentPage.value - 1) * PAGE_SIZE
  return books.value.slice(start, start + PAGE_SIZE)
})

const categoryOptions = computed(() => categories.value)

onMounted(async () => {
  await Promise.all([loadBooks(), loadCategories()])
})

watch([serverPaginated, totalPages], () => {
  if (serverPaginated.value) return
  if (currentPage.value > totalPages.value) currentPage.value = totalPages.value
  if (currentPage.value < 1) currentPage.value = 1
})

async function loadCategories() {
  categoriesLoading.value = true
  try {
    const data = await get('/api/categories')
    categories.value = data.results || data.categories || []
  } catch (e) {
    showError(e.message || '加载分类失败')
  } finally {
    categoriesLoading.value = false
  }
}

async function loadBooks({ keepPage = false } = {}) {
  if (!keepPage) currentPage.value = 1
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchKeyword.value) params.set('kw', searchKeyword.value)
    if (statusFilter.value) params.set('status', statusFilter.value)
    params.set('page', currentPage.value)

    const data = await get('/api/books?' + params.toString())
    const results = data.results || data.books || []
    books.value = results
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
    loadBooks({ keepPage: true })
  }
}

function resetForm() {
  Object.assign(form, {
    isbn: '',
    title: '',
    author: '',
    publisher: '',
    publish_date: '',
    category_id: null,
    total_copies: 1,
    location: '',
    description: '',
  })
  formError.value = ''
  resetCover()
}

function resetCover(baseUrl = '') {
  coverFile.value = null
  if (coverInputRef.value) {
    coverInputRef.value.value = ''
  }
  if (coverObjectUrl) {
    URL.revokeObjectURL(coverObjectUrl)
    coverObjectUrl = null
  }
  coverPreviewUrl.value = baseUrl
}

function handleCoverChange(e) {
  const file = e.target.files?.[0]
  if (!file) return

  if (file.type && !file.type.startsWith('image/')) {
    formError.value = '封面必须是图片文件'
    resetCover(editingBook.value?.cover_url || '')
    return
  }

  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    formError.value = '封面大小不能超过 5MB'
    resetCover(editingBook.value?.cover_url || '')
    return
  }

  coverFile.value = file
  if (coverObjectUrl) URL.revokeObjectURL(coverObjectUrl)
  coverObjectUrl = URL.createObjectURL(file)
  coverPreviewUrl.value = coverObjectUrl
}

function clearCover() {
  resetCover(editingBook.value?.cover_url || '')
}

function openAddModal() {
  editingBook.value = null
  if (categories.value.length === 0) loadCategories()
  resetForm()
  showAddModal.value = true
}

function closeFormModal() {
  showAddModal.value = false
  editingBook.value = null
  resetForm()
}

function resetCategoryForm() {
  Object.assign(categoryForm, { name: '', description: '' })
  categoryFormError.value = ''
}

function openCategoryManager() {
  showCategoryManagerModal.value = true
  loadCategories()
}

function closeCategoryManager() {
  showCategoryManagerModal.value = false
}

function openCategoryForm(category = null) {
  editingCategory.value = category
  Object.assign(categoryForm, {
    name: category?.name || '',
    description: category?.description || '',
  })
  categoryFormError.value = ''
  showCategoryFormModal.value = true
}

function closeCategoryForm() {
  showCategoryFormModal.value = false
  editingCategory.value = null
  resetCategoryForm()
}

async function handleCategorySubmit() {
  categoryFormError.value = ''
  categorySubmitting.value = true

  try {
    const payload = {
      name: (categoryForm.name || '').trim(),
      description: (categoryForm.description || '').trim(),
    }
    if (!payload.name) {
      categoryFormError.value = '分类名称不能为空'
      return
    }

    if (editingCategory.value) {
      await patch(`/api/categories/${editingCategory.value.id}`, payload)
      success('分类已更新')
    } else {
      await post('/api/categories', payload)
      success('分类已创建')
    }

    await loadCategories()
    closeCategoryForm()
  } catch (e) {
    categoryFormError.value = e.message || '操作失败'
  } finally {
    categorySubmitting.value = false
  }
}

function confirmCategoryDelete(category) {
  deletingCategory.value = category
  showCategoryDeleteModal.value = true
}

async function handleCategoryDelete() {
  if (!deletingCategory.value) return

  categoryDeleting.value = true
  try {
    const deletedId = deletingCategory.value.id
    await del(`/api/categories/${deletedId}`)
    success('分类已删除')
    showCategoryDeleteModal.value = false
    deletingCategory.value = null
    if (form.category_id === deletedId) form.category_id = null
    await loadCategories()
  } catch (e) {
    showError(e.message || '删除失败')
  } finally {
    categoryDeleting.value = false
  }
}

function editBook(book) {
  editingBook.value = book
  if (categories.value.length === 0) loadCategories()
  Object.assign(form, {
    isbn: book.isbn || '',
    title: book.title || '',
    author: book.author || '',
    publisher: book.publisher || '',
    publish_date: book.publish_date || '',
    category_id: book.category?.id ?? null,
    total_copies: book.total_copies || 1,
    location: book.location || '',
    description: book.description || '',
  })
  resetCover(book.cover_url || '')
  showAddModal.value = true
}

async function handleSubmit() {
  formError.value = ''
  submitting.value = true

  try {
    const payload = { ...form }
    if (!payload.publish_date) delete payload.publish_date
    if (!payload.category_id && payload.category_id !== 0) {
      payload.category_id = null
    }

    let savedBookId = editingBook.value?.id
    const isEditing = !!editingBook.value
    if (editingBook.value) {
      const result = await patch(`/api/books/${editingBook.value.id}`, payload)
      savedBookId = result.book?.id ?? savedBookId
    } else {
      const result = await post('/api/books', payload)
      savedBookId = result.book?.id
    }

    let coverUploadFailed = false
    if (coverFile.value && savedBookId != null) {
      try {
        const formData = new FormData()
        formData.append('cover', coverFile.value)
        await upload(`/api/books/${savedBookId}/cover`, formData)
      } catch (e) {
        showError(e.message || '封面上传失败')
        coverUploadFailed = true
      }
    }

    if (coverUploadFailed) {
      success(isEditing ? '更新成功（封面未更新）' : '添加成功（封面未上传）')
    } else {
      success(isEditing ? '更新成功' : '添加成功')
    }
    closeFormModal()
    await loadBooks({ keepPage: true })
  } catch (e) {
    formError.value = e.message || '操作失败'
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(book) {
  try {
    const newStatus = book.status === 'on_shelf' ? 'off_shelf' : 'on_shelf'
    await patch(`/api/books/${book.id}`, { status: newStatus })
    success(newStatus === 'on_shelf' ? '已上架' : '已下架')
    await loadBooks({ keepPage: true })
  } catch (e) {
    showError(e.message || '操作失败')
  }
}

function confirmDelete(book) {
  deletingBook.value = book
  showDeleteModal.value = true
}

async function handleDelete() {
  deleting.value = true
  try {
    await del(`/api/books/${deletingBook.value.id}`)
    success('删除成功')
    showDeleteModal.value = false
    deletingBook.value = null
    await loadBooks({ keepPage: true })
  } catch (e) {
    showError(e.message || '删除失败')
  } finally {
    deleting.value = false
  }
}
</script>
