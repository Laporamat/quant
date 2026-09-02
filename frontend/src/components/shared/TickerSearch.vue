<template>
  <div class="relative" ref="wrapperRef">
    <div class="flex flex-wrap items-center gap-1.5 px-2.5 py-1.5 bg-surface-800 border border-surface-700 rounded-lg focus-within:border-primary-500 transition-colors min-h-[38px]">
      <!-- Selected chips (multi mode) -->
      <span
        v-for="t in selected"
        :key="t"
        class="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-600/20 text-primary-300 text-xs rounded-full"
      >
        {{ t }}
        <button @click="remove(t)" class="hover:text-white">×</button>
      </span>

      <input
        ref="inputRef"
        v-model="query"
        @focus="open = true"
        @input="open = true"
        @keydown.backspace="onBackspace"
        @keydown.escape="open = false"
        @keydown.down.prevent="highlight = Math.min(highlight + 1, filtered.length - 1)"
        @keydown.up.prevent="highlight = Math.max(highlight - 1, 0)"
        @keydown.enter.prevent="selectHighlighted"
        :placeholder="selected.length ? '' : placeholder"
        class="flex-1 min-w-[80px] bg-transparent text-sm text-surface-100 placeholder-surface-500 outline-none"
      />
    </div>

    <!-- Dropdown -->
    <Transition name="dropdown">
      <div
        v-if="open && filtered.length"
        class="absolute top-full mt-1 w-full z-50 bg-surface-800 border border-surface-700 rounded-lg shadow-card-lg max-h-52 overflow-y-auto scrollbar-thin"
      >
        <button
          v-for="(t, i) in filtered"
          :key="t"
          @mousedown.prevent="select(t)"
          class="w-full text-left px-3 py-2 text-sm text-surface-200 hover:bg-surface-700/50 transition-colors"
          :class="{ 'bg-surface-700/50 text-white': i === highlight }"
        >
          {{ t }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useMarketStore } from '@/stores/marketStore'

const props = withDefaults(defineProps<{
  modelValue:  string[]
  multi?:      boolean
  placeholder?: string
  universe?:   string
}>(), {
  multi:       true,
  placeholder: 'Search ticker…',
  universe:    'sp100',
})

const emit = defineEmits<{
  'update:modelValue': [val: string[]]
}>()

const marketStore = useMarketStore()
const query       = ref('')
const open        = ref(false)
const highlight   = ref(0)
const wrapperRef  = ref<HTMLElement>()
const inputRef    = ref<HTMLInputElement>()

const selected = computed(() => props.modelValue)

const allTickers = computed(
  () => marketStore.universeTickerMap[props.universe] ?? []
)

const filtered = computed(() => {
  const q = query.value.toUpperCase()
  return allTickers.value
    .filter((t) => t.includes(q) && !selected.value.includes(t))
    .slice(0, 20)
})

function select(ticker: string) {
  if (props.multi) {
    emit('update:modelValue', [...selected.value, ticker])
  } else {
    emit('update:modelValue', [ticker])
  }
  query.value = ''
  open.value = false
  highlight.value = 0
}

function remove(ticker: string) {
  emit('update:modelValue', selected.value.filter((t) => t !== ticker))
}

function onBackspace() {
  if (!query.value && selected.value.length) {
    remove(selected.value[selected.value.length - 1])
  }
}

function selectHighlighted() {
  if (filtered.value[highlight.value]) select(filtered.value[highlight.value])
}

function onClickOutside(e: MouseEvent) {
  if (!wrapperRef.value?.contains(e.target as Node)) open.value = false
}

onMounted(() => {
  document.addEventListener('mousedown', onClickOutside)
  marketStore.loadUniverse(props.universe)
})
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))
</script>

<style scoped>
.dropdown-enter-active, .dropdown-leave-active { transition: opacity .15s ease, transform .15s ease; }
.dropdown-enter-from { opacity: 0; transform: translateY(-4px); }
.dropdown-leave-to   { opacity: 0; transform: translateY(-4px); }
</style>
