import { createApp } from 'vue'
import { createPinia } from 'pinia'

// ── ECharts — register SYNCHRONOUSLY before app mounts ───────────────────────
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import {
  LineChart, BarChart, CandlestickChart, HeatmapChart,
  ScatterChart, GaugeChart, RadarChart,
} from 'echarts/charts'
import {
  TitleComponent, TooltipComponent, GridComponent,
  LegendComponent, DataZoomComponent, MarkLineComponent,
  VisualMapComponent, AxisPointerComponent,
} from 'echarts/components'
import VueECharts from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart, BarChart, CandlestickChart, HeatmapChart,
  ScatterChart, GaugeChart, RadarChart,
  TitleComponent, TooltipComponent, GridComponent,
  LegendComponent, DataZoomComponent, MarkLineComponent,
  VisualMapComponent, AxisPointerComponent,
])

import App    from './App.vue'
import router from './router'
import { useThemeStore } from './stores/appStore'
import { http } from './api/client'
import './styles/main.css'

const app   = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.component('VChart', VueECharts)

// ── Theme ──────────────────────────────────────────────────────────────────────
const themeStore = useThemeStore()
themeStore.init()

// ── Auth: re-inject token from localStorage on hard refresh ───────────────────
// client.ts already does this on import, but doing it here ensures
// pinia is initialised before authStore reads it.
const stored = localStorage.getItem('qd_access')
if (stored) {
  http.defaults.headers.common['Authorization'] = `Bearer ${stored}`
}

app.mount('#app')
