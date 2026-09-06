import { createApp } from 'vue'
import { createPinia } from 'pinia'

// ── ECharts — register SYNCHRONOUSLY before app mounts ───────────────────────
// Lazy loading caused VChart to be unresolved during first render → blank pages
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
import './styles/main.css'

const app   = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.component('VChart', VueECharts)  // global — available in every view

// Apply saved theme before first render
const themeStore = useThemeStore()
themeStore.init()

app.mount('#app')
