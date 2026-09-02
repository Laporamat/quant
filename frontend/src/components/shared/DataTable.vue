<template>
  <div class="flex flex-col gap-3">
    <!-- Search + controls -->
    <div v-if="searchable || $slots.controls" class="flex items-center gap-2">
      <div v-if="searchable" class="relative flex-1 max-w-xs">
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input v-model="search" type="text" placeholder="Search…"
          class="w-full pl-8 pr-3 py-1.5 bg-surface-800 border border-surface-700 rounded-lg text-sm text-surface-100 placeholder-surface-500 focus:outline-none focus:border-primary-500" />
      </div>
      <slot name="controls" />
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-lg border border-surface-700/50">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-800/50">
            <th
              v-for="col in columns"
              :key="col.key"
              @click="col.sortable !== false ? toggleSort(col.key) : null"
              class="px-3 py-2.5 text-left text-xs font-semibold text-surface-400 uppercase tracking-wider select-none"
              :class="col.sortable !== false ? 'cursor-pointer hover:text-surface-200' : ''"
              :style="col.width ? { width: col.width } : {}"
            >
              <span class="flex items-center gap-1">
                {{ col.label }}
                <span v-if="col.sortable !== false" class="text-surface-600">
                  <span v-if="sortKey === col.key">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
                  <span v-else class="opacity-0">↕</span>
                </span>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- Loading -->
          <template v-if="loading">
            <tr v-for="i in 8" :key="i" class="border-t border-surface-700/30">
              <td v-for="col in columns" :key="col.key" class="px-3 py-2.5">
                <div class="h-3 bg-surface-700 rounded animate-skeleton" :style="{ width: `${40 + Math.random()*40}%` }" />
              </td>
            </tr>
          </template>

          <!-- Empty -->
          <tr v-else-if="!paginatedRows.length">
            <td :colspan="columns.length" class="px-3 py-8 text-center text-surface-500">
              No data
            </td>
          </tr>

          <!-- Rows -->
          <tr
            v-else
            v-for="(row, i) in paginatedRows"
            :key="i"
            class="border-t border-surface-700/30 hover:bg-surface-700/20 transition-colors duration-100"
            :class="rowClass?.(row)"
            @click="$emit('row-click', row)"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              class="px-3 py-2.5 text-surface-200 tabular-nums"
              :class="col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                <span :class="col.colorize ? colorClass(row[col.key]) : ''">
                  {{ col.format ? col.format(row[col.key], row) : row[col.key] ?? '—' }}
                </span>
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="pageSize && filteredRows.length > pageSize" class="flex items-center justify-between text-xs text-surface-400">
      <span>{{ filteredRows.length }} rows</span>
      <div class="flex items-center gap-1">
        <button @click="page--" :disabled="page === 1" class="btn-ghost px-2 py-1 disabled:opacity-30">←</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button @click="page++" :disabled="page === totalPages" class="btn-ghost px-2 py-1 disabled:opacity-30">→</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

export interface TableColumn {
  key:      string
  label:    string
  sortable?: boolean
  align?:   'left' | 'right' | 'center'
  width?:   string
  format?:  (v: unknown, row: Record<string, unknown>) => string
  colorize?: boolean
}

const props = withDefaults(defineProps<{
  columns:    TableColumn[]
  rows:       Record<string, unknown>[]
  loading?:   boolean
  searchable?: boolean
  pageSize?:  number
  rowClass?:  (row: Record<string, unknown>) => string
}>(), {
  loading:    false,
  searchable: false,
})

defineEmits<{ 'row-click': [row: Record<string, unknown>] }>()

const search  = ref('')
const sortKey = ref('')
const sortDir = ref<'asc' | 'desc'>('desc')
const page    = ref(1)

function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
  page.value = 1
}

const filteredRows = computed(() => {
  let rows = props.rows
  if (search.value) {
    const q = search.value.toLowerCase()
    rows = rows.filter((r) =>
      Object.values(r).some((v) => String(v).toLowerCase().includes(q))
    )
  }
  if (sortKey.value) {
    const k = sortKey.value
    const dir = sortDir.value === 'asc' ? 1 : -1
    rows = [...rows].sort((a, b) => {
      const av = a[k] as number
      const bv = b[k] as number
      if (av === null || av === undefined) return 1
      if (bv === null || bv === undefined) return -1
      return (av > bv ? 1 : av < bv ? -1 : 0) * dir
    })
  }
  return rows
})

const totalPages = computed(() =>
  props.pageSize ? Math.ceil(filteredRows.value.length / props.pageSize) : 1
)

const paginatedRows = computed(() => {
  if (!props.pageSize) return filteredRows.value
  const start = (page.value - 1) * props.pageSize
  return filteredRows.value.slice(start, start + props.pageSize)
})

function colorClass(v: unknown) {
  const n = Number(v)
  if (isNaN(n)) return ''
  return n >= 0 ? 'text-bull' : 'text-bear'
}
</script>
