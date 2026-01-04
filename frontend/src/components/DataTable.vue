<template>
  <div class="bg-white rounded-2xl border border-border overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full">
        <colgroup>
          <col
            v-for="col in columns"
            :key="col.key"
            :style="col.width ? { width: col.width } : undefined"
          />
        </colgroup>
        <thead class="bg-sidebar border-b border-border">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              class="px-5 py-4 text-left text-sm font-medium text-text-secondary whitespace-nowrap"
            >
              {{ col.title }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-border">
          <tr v-if="loading">
            <td :colspan="columns.length" class="px-5 py-12 text-center text-text-muted">
              <div class="flex items-center justify-center gap-2">
                <Loader2 class="animate-spin h-5 w-5 text-claude-500" :stroke-width="2" />
                加载中...
              </div>
            </td>
          </tr>
          <tr v-else-if="data.length === 0">
            <td :colspan="columns.length" class="px-5 py-12 text-center text-text-muted">
              {{ emptyText }}
            </td>
          </tr>
          <template v-else>
            <tr
              v-for="(row, index) in data"
              :key="rowKey ? row[rowKey] : index"
              class="hover:bg-sidebar transition-colors"
            >
              <td
                v-for="col in columns"
                :key="col.key"
                class="px-5 py-4 text-sm text-text-primary"
              >
                <slot :name="col.key" :row="row" :value="row[col.key]">
                  {{ row[col.key] }}
                </slot>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { Loader2 } from 'lucide-vue-next'

defineProps({
  columns: {
    type: Array,
    required: true
  },
  data: {
    type: Array,
    default: () => []
  },
  rowKey: String,
  loading: Boolean,
  emptyText: {
    type: String,
    default: '暂无数据'
  }
})
</script>
