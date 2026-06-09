<template>
  <div class="profile-gauge" ref="chartRef" v-show="hasData"></div>
  <div class="profile-gauge-empty" v-show="!hasData">
    <div class="empty-score">--</div>
    <div class="empty-label">暂无画像数据</div>
    <div class="empty-hint">发送消息后自动生成</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  dimensions: {
    type: Object,
    default: () => ({})
  }
})

const chartRef = ref(null)
let chart = null

const hasData = computed(() => {
  const dims = Object.values(props.dimensions)
  return dims.length > 0 && dims.some(d => (d?.confidence || 0) > 0)
})

const avgScore = computed(() => {
  const dims = Object.values(props.dimensions)
  if (!dims.length) return 0
  const total = dims.reduce((sum, d) => sum + (d?.confidence || 0), 0)
  return Math.round((total / dims.length) * 100)
})

const dimCount = computed(() => {
  return Object.values(props.dimensions).filter(d => d?.value && d.confidence > 0).length
})

const initChart = () => {
  if (!chartRef.value) return
  try {
    chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })
    updateChart()
  } catch (e) {
    console.error('Gauge init error:', e)
  }
}

const updateChart = () => {
  if (!chart) return
  if (!hasData.value) return

  const score = Math.max(avgScore.value, 1) // 避免 0 时 roundCap 渲染异常

  const option = {
    series: [{
      type: 'gauge',
      center: ['50%', '60%'],
      radius: '85%',
      startAngle: 210,
      endAngle: -30,
      min: 0,
      max: 100,
      splitNumber: 5,
      progress: {
        show: true,
        width: 10,
        roundCap: true,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#60a5fa' },
              { offset: 0.5, color: '#2563eb' },
              { offset: 1, color: '#1d4ed8' }
            ]
          }
        }
      },
      pointer: { show: false },
      axisLine: {
        lineStyle: {
          width: 10,
          color: [[1, '#f3f4f6']]
        }
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: { show: false },
      title: { show: false },
      data: [{ value: score }],
      animationDuration: 1500,
      animationEasing: 'elasticOut'
    }],
    graphic: {
      elements: [
        {
          type: 'text',
          left: 'center',
          top: '38%',
          style: {
            text: score + '',
            fill: '#111827',
            font: 'bold 28px -apple-system, sans-serif',
            textAlign: 'center'
          },
          z: 100
        },
        {
          type: 'text',
          left: 'center',
          top: '55%',
          style: {
            text: '综合评分',
            fill: '#9ca3af',
            font: '12px -apple-system, sans-serif',
            textAlign: 'center'
          },
          z: 100
        },
        {
          type: 'text',
          left: 'center',
          top: '65%',
          style: {
            text: `${dimCount.value}/6 维度已分析`,
            fill: '#2563eb',
            font: '11px -apple-system, sans-serif',
            textAlign: 'center'
          },
          z: 100
        }
      ]
    }
  }

  try {
    chart.setOption(option, true)
  } catch (e) {
    console.error('Gauge setOption error:', e)
  }
}

const handleResize = () => {
  chart && chart.resize()
}

watch(() => props.dimensions, async () => {
  if (hasData.value && !chart) {
    await nextTick()
    initChart()
  } else {
    updateChart()
  }
}, { deep: true })

onMounted(() => {
  if (hasData.value) {
    initChart()
  }
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart && chart.dispose()
})
</script>

<style scoped>
.profile-gauge {
  width: 100%;
  height: 160px;
}

.profile-gauge-empty {
  width: 100%;
  height: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.empty-score {
  font-size: 32px;
  font-weight: 700;
  color: #d1d5db;
  margin-bottom: 4px;
}

.empty-label {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 2px;
}

.empty-hint {
  font-size: 11px;
}
</style>
