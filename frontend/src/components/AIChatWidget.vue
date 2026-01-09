<template>
  <Teleport to="body">
    <!-- 浮动按钮 -->
    <button
      v-if="!isOpen"
      @click="openChat"
      class="fixed bottom-6 right-6 w-14 h-14 bg-claude-500 text-white rounded-full shadow-lg hover:bg-claude-600 transition-all duration-200 hover:scale-105 flex items-center justify-center z-50"
      title="AI 图书推荐"
    >
      <MessageCircle class="w-6 h-6" :stroke-width="2" />
    </button>

    <!-- 聊天窗口 -->
    <Transition name="chat">
      <div
        v-if="isOpen"
        class="fixed bottom-6 right-6 w-96 h-[32rem] bg-white rounded-2xl shadow-2xl border border-border flex flex-col z-50 overflow-hidden"
      >
        <!-- 标题栏 -->
        <div class="flex items-center justify-between px-4 py-3 bg-claude-500 text-white">
          <div class="flex items-center gap-2">
            <Sparkles class="w-5 h-5" :stroke-width="2" />
            <span class="font-medium">AI 图书推荐</span>
          </div>
          <button
            @click="closeChat"
            class="hover:bg-white/20 rounded-lg p-1 transition-colors"
          >
            <X class="w-5 h-5" :stroke-width="2" />
          </button>
        </div>

        <!-- 消息列表 -->
        <div
          ref="messagesContainer"
          class="flex-1 overflow-y-auto p-4 space-y-4"
        >
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="text-center py-8">
            <div class="w-16 h-16 bg-claude-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <BookOpen class="w-8 h-8 text-claude-500" :stroke-width="1.5" />
            </div>
            <h3 class="font-medium text-text-primary mb-2">你好，我是小图!</h3>
            <p class="text-sm text-text-muted">
              告诉我你的阅读偏好，<br>我来为你推荐合适的书籍。
            </p>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="[
              'flex',
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              :class="[
                'max-w-[80%] rounded-2xl px-4 py-3',
                msg.role === 'user'
                  ? 'bg-claude-500 text-white rounded-br-md'
                  : 'bg-sidebar text-text-primary rounded-bl-md'
              ]"
            >
              <div
                v-html="formatMessage(msg.content)"
                class="text-sm leading-relaxed chat-content"
                @click="handleMessageClick"
              ></div>
            </div>
          </div>

          <!-- 加载中 -->
          <div v-if="loading" class="flex justify-start">
            <div class="bg-sidebar rounded-2xl rounded-bl-md px-4 py-3">
              <div class="flex items-center gap-2 text-text-muted">
                <Loader2 class="w-4 h-4 animate-spin" :stroke-width="2" />
                <span class="text-sm">正在思考...</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="p-4 border-t border-border">
          <div class="flex gap-2">
            <input
              v-model="inputText"
              @keyup.enter="sendMessage"
              type="text"
              placeholder="描述你的阅读偏好..."
              class="flex-1 px-4 py-2.5 bg-sidebar border border-border rounded-xl text-sm focus:outline-none focus:border-claude-400 focus:ring-2 focus:ring-claude-500/20 transition-all"
              :disabled="loading"
            />
            <button
              @click="sendMessage"
              :disabled="loading || !inputText.trim()"
              class="px-4 py-2.5 bg-claude-500 text-white rounded-xl hover:bg-claude-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send class="w-4 h-4" :stroke-width="2" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@utils/api'
import { error as showError } from '@utils/toast'
import { currentUser } from '@utils/auth'
import { renderChatMarkdown } from '@utils/markdown'
import {
  MessageCircle,
  X,
  Sparkles,
  BookOpen,
  Send,
  Loader2
} from 'lucide-vue-next'

const router = useRouter()

const isOpen = ref(false)
const inputText = ref('')
const messages = ref([])
const loading = ref(false)
const messagesContainer = ref(null)

function openChat() {
  if (!currentUser.value) {
    showError('请先登录后使用AI推荐功能')
    router.push('/login/')
    return
  }
  isOpen.value = true
}

function closeChat() {
  isOpen.value = false
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true

  await scrollToBottom()

  try {
    // 构建历史消息
    const history = messages.value.slice(0, -1).map(m => ({
      role: m.role,
      content: m.content
    }))

    const response = await api('/api/ai/chat', {
      method: 'POST',
      body: { message: text, history }
    })

    messages.value.push({ role: 'assistant', content: response.reply })
  } catch (e) {
    showError(e.message || 'AI 服务暂时不可用')
    // 移除刚才的用户消息
    messages.value.pop()
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function formatMessage(content) {
  return renderChatMarkdown(content)
}

function handleMessageClick(event) {
  const target = event?.target
  const link = target?.closest?.('a[data-book-id]')
  if (!link) return

  const bookId = link.getAttribute('data-book-id')
  if (!bookId) return

  event.preventDefault()
  router.push(`/books/${bookId}/`)
  closeChat()
}

async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(messages, () => scrollToBottom(), { deep: true })
</script>

<style scoped>
.chat-enter-active,
.chat-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-enter-from,
.chat-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 链接样式 */
:deep(.chat-content a) {
  color: #DA7756;
  text-decoration: underline;
  font-weight: 500;
}

:deep(.chat-content a:hover) {
  color: #c56a4c;
}

:deep(.chat-content p) {
  margin: 0.25rem 0;
}

:deep(.chat-content ul),
:deep(.chat-content ol) {
  padding-left: 1.25rem;
  margin: 0.25rem 0;
}

:deep(.chat-content li) {
  margin: 0.15rem 0;
}

:deep(.chat-content pre) {
  margin: 0.5rem 0;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 0.75rem;
  overflow-x: auto;
}

:deep(.chat-content code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.85em;
  background: rgba(0, 0, 0, 0.06);
  padding: 0.1rem 0.3rem;
  border-radius: 0.35rem;
}

:deep(.chat-content pre code) {
  background: transparent;
  padding: 0;
  border-radius: 0;
}

:deep(.chat-content blockquote) {
  margin: 0.5rem 0;
  padding: 0.25rem 0.75rem;
  border-left: 3px solid rgba(218, 119, 86, 0.6);
  color: rgba(0, 0, 0, 0.7);
}

:deep(.chat-content hr) {
  margin: 0.75rem 0;
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

:deep(.chat-content h1),
:deep(.chat-content h2),
:deep(.chat-content h3),
:deep(.chat-content h4),
:deep(.chat-content h5),
:deep(.chat-content h6) {
  margin: 0.5rem 0 0.25rem;
  font-weight: 600;
}
</style>
