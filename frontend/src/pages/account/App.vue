<template>
  <div>
    <h1 class="text-xl md:text-2xl font-semibold text-text-primary mb-4 md:mb-8">账号设置</h1>

    <div class="bg-white rounded-2xl border border-border p-4 md:p-8 max-w-xl">
      <h2 class="text-lg font-medium text-text-primary mb-6">修改密码</h2>

      <form @submit.prevent="handleSubmit" class="space-y-5">
        <div>
          <label class="label">旧密码</label>
          <input
            v-model="form.oldPassword"
            type="password"
            required
            class="input"
            placeholder="请输入旧密码"
          />
        </div>

        <div>
          <label class="label">新密码</label>
          <input
            v-model="form.newPassword"
            type="password"
            required
            minlength="6"
            class="input"
            placeholder="请输入新密码（至少6位）"
          />
        </div>

        <div>
          <label class="label">确认新密码</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            required
            class="input"
            placeholder="请再次输入新密码"
          />
        </div>

        <div v-if="error" class="p-3 bg-red-50 text-red-600 text-sm rounded-xl">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full btn-primary py-3 text-base font-medium"
        >
          {{ loading ? '保存中...' : '保存修改' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { changePassword } from '@utils/auth'
import { success } from '@utils/toast'

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  error.value = ''

  if (form.newPassword !== form.confirmPassword) {
    error.value = '两次输入的新密码不一致'
    return
  }

  if (form.newPassword.length < 6) {
    error.value = '新密码长度至少为6位'
    return
  }

  if (form.oldPassword === form.newPassword) {
    error.value = '新密码不能与旧密码相同'
    return
  }

  loading.value = true
  try {
    await changePassword(form.oldPassword, form.newPassword, form.confirmPassword)
    success('密码修改成功')
    form.oldPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
  } catch (e) {
    error.value = e.message || '修改失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

