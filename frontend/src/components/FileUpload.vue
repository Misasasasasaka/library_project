<template>
  <div
    :class="[
      'border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 cursor-pointer',
      isDragging ? 'border-claude-400 bg-claude-50' : 'border-border hover:border-border-dark bg-sidebar'
    ]"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
    @click="triggerSelect"
  >
    <input
      ref="inputRef"
      type="file"
      :accept="accept"
      class="hidden"
      @change="handleSelect"
    />

    <div v-if="!file">
      <CloudUpload class="w-14 h-14 mx-auto text-text-light" :stroke-width="1.5" />
      <p class="mt-4 text-text-secondary font-medium">拖拽文件到此处，或点击上传</p>
      <p class="mt-2 text-sm text-text-muted">{{ hint }}</p>
    </div>

    <div v-else class="flex items-center justify-center gap-3">
      <FileText class="w-10 h-10 text-claude-500" :stroke-width="1.5" />
      <span class="text-text-primary font-medium">{{ file.name }}</span>
      <button
        @click.stop="clearFile"
        class="text-text-muted hover:text-red-500 transition-colors"
      >
        <X class="w-5 h-5" :stroke-width="2" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CloudUpload, FileText, X } from 'lucide-vue-next'

const props = defineProps({
  accept: {
    type: String,
    default: '.csv'
  },
  hint: {
    type: String,
    default: '支持 CSV 文件'
  }
})

const emit = defineEmits(['change'])

const inputRef = ref(null)
const isDragging = ref(false)
const file = ref(null)

function triggerSelect() {
  inputRef.value?.click()
}

function handleSelect(e) {
  const selected = e.target.files?.[0]
  if (selected) {
    file.value = selected
    emit('change', selected)
  }
}

function handleDrop(e) {
  isDragging.value = false
  const dropped = e.dataTransfer.files?.[0]
  if (dropped) {
    file.value = dropped
    emit('change', dropped)
  }
}

function clearFile() {
  file.value = null
  if (inputRef.value) {
    inputRef.value.value = ''
  }
  emit('change', null)
}

defineExpose({ clearFile })
</script>
