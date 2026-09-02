import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App    from './App.vue'
import router from './router'
import { useThemeStore } from './stores/appStore'
import './styles/main.css'

const app   = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Apply saved theme immediately (before any render)
const themeStore = useThemeStore()
themeStore.init()

app.mount('#app')

// ── Lazy-register VChart + ECharts AFTER first paint ─────────────────────────
// ECharts is ~500 KB — defer it so the shell renders instantly.
// VChart is registered globally once the idle callback fires.
const registerECharts = async () => {
  const [
    { default: VueECharts },
    { use },
    { CanvasRenderer },
    { LineChart, BarChart, CandlestickChart, HeatmapChart, ScatterChart, GaugeChart, RadarChart },
    {
      TitleComponent, TooltipComponent, GridComponent,
      LegendComponent, DataZoomComponent, MarkLineComponent,
      VisualMapComponent, AxisPointerComponent,
    },
  ] = await Promise.all([
    import('vue-echarts'),
    import('echarts/core'),
    import('echarts/renderers'),
    import('echarts/charts'),
    import('echarts/components'),
  ])

  use([
    CanvasRenderer,
    LineChart, BarChart, CandlestickChart, HeatmapChart,
    ScatterChart, GaugeChart, RadarChart,
    TitleComponent, TooltipComponent, GridComponent,
    LegendComponent, DataZoomComponent, MarkLineComponent,
    VisualMapComponent, AxisPointerComponent,
  ])

  // Register globally so every chart view can use <VChart />
  app.component('VChart', VueECharts)
}

if ('requestIdleCallback' in window) {
  requestIdleCallback(registerECharts, { timeout: 2000 })
} else {
  // Safari fallback
  setTimeout(registerECharts, 200)
}
