<template>
  <div class="min-h-screen bg-content flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <router-link to="/books/" class="block text-center mb-8 group">
        <div class="w-16 h-16 bg-claude-500 rounded-2xl flex items-center justify-center mx-auto shadow-lg group-hover:bg-claude-600 transition-colors">
          <Library class="w-8 h-8 text-white" :stroke-width="2" />
        </div>
        <h1 class="mt-6 text-2xl font-semibold text-text-primary group-hover:text-claude-600 transition-colors">图书馆</h1>
        <p class="mt-2 text-text-muted">欢迎回来，请登录您的账户</p>
      </router-link>

      <!-- 登录表单 -->
      <div class="bg-white rounded-2xl shadow-sm border border-border p-6 md:p-8">
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
              <label class="label">密码</label>
              <input
                v-model="form.password"
                type="password"
                required
                class="input"
                placeholder="请输入密码"
              />
            </div>

            <div class="flex items-end gap-3">
              <div class="flex-1">
                <label class="label">验证码</label>
                <input
                  v-model="form.captcha"
                  type="text"
                  required
                  class="input"
                  placeholder="请输入图片验证码"
                />
              </div>
              <img
                :src="captchaUrl"
                class="h-11 w-32 rounded-xl border border-border cursor-pointer select-none"
                alt="验证码"
                title="点击刷新验证码"
                @click="refreshCaptcha"
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
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-text-muted">
          还没有账户？
          <router-link to="/register/" class="text-claude-600 hover:text-claude-700 font-medium">立即注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { get } from '@utils/api'
import { login } from '@utils/auth'
import { Library } from 'lucide-vue-next'

const router = useRouter()

const form = reactive({
  username: '',
  password: '',
  captcha: ''
})

const loading = ref(false)
const error = ref('')
const captchaUrl = ref('')

onMounted(async () => {
  try {
    await get('/api/auth/csrf')
  } catch (e) {
    console.error('获取 CSRF Token 失败')
  }

  refreshCaptcha()
})

function refreshCaptcha() {
  captchaUrl.value = `/api/auth/captcha?t=${Date.now()}`
}

async function handleSubmit() {
  error.value = ''
  loading.value = true

  try {
    await login(form.username, form.password, form.captcha)
    router.push('/books/')
  } catch (e) {
    error.value = e.message || '登录失败，请检查用户名和密码'
    form.captcha = ''
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}
</script>
