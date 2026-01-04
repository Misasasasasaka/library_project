<template>
  <div class="min-h-screen bg-content flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <router-link to="/books/" class="block text-center mb-8 group">
        <div class="w-16 h-16 bg-claude-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg group-hover:bg-claude-600 transition-colors">
          <Library class="w-8 h-8 text-white" :stroke-width="2" />
        </div>
        <h1 class="mt-6 text-2xl font-semibold text-text-primary group-hover:text-claude-600 transition-colors">智慧图书馆</h1>
        <p class="mt-2 text-text-muted">创建账户，开启阅读之旅</p>
      </router-link>

      <!-- 注册表单 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border p-8">
        <form @submit.prevent="handleSubmit">
          <div class="space-y-5">
            <div>
              <label class="label">用户名</label>
              <input
                v-model="form.username"
                type="text"
                required
                class="input"
                placeholder="请输入用户名"
              />
            </div>

            <div>
              <label class="label">邮箱</label>
              <input
                v-model="form.mail"
                type="email"
                class="input"
                placeholder="请输入邮箱（可选，用于接收通知）"
              />
            </div>

            <div>
              <label class="label">密码</label>
              <input
                v-model="form.password"
                type="password"
                required
                minlength="6"
                class="input"
                placeholder="请输入密码（至少6位）"
              />
            </div>

            <div>
              <label class="label">确认密码</label>
              <input
                v-model="form.confirmPassword"
                type="password"
                required
                class="input"
                placeholder="请再次输入密码"
              />
            </div>
          </div>

          <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-600 text-sm rounded-xl">
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="mt-6 w-full btn-primary py-3 text-base font-medium"
          >
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-text-muted">
          已有账户？
          <router-link to="/login/" class="text-claude-600 hover:text-claude-700 font-medium">立即登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get } from '@utils/api'
import { register } from '@utils/auth'
import { Library } from 'lucide-vue-next'

const router = useRouter()

const form = reactive({
  username: '',
  mail: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    await get('/api/auth/csrf')
  } catch (e) {
    console.error('获取 CSRF Token 失败')
  }
})

async function handleSubmit() {
  error.value = ''

  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }

  if (form.password.length < 6) {
    error.value = '密码长度至少为6位'
    return
  }

  loading.value = true

  try {
    await register(form.username, form.password, form.mail || undefined)
    router.push('/books/')
  } catch (e) {
    error.value = e.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
