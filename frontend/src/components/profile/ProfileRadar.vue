<template>
  <div class="profile-radar" ref="chartRef"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  dimensions: {
    type: Object,
    default: () => ({})
  }
})

const chartRef = ref(null)
let chart = null

const dimensionLabels = {
  knowledge_base: '知识基础',
  cognitive_style: '认知风格',
  error_patterns: '易错点偏好',
  learning_preference: '学习偏好',
  learning_pace: '学习节奏',
  goal_orientation: '目标导向'
}

const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })
  updateChart()
}

const updateChart = () => {
  if (!chart) return

  const indicators = Object.keys(dimensionLabels).map(key => ({
    name: dimensionLabels[key],
    max: 1
  }))

  const values = Object.keys(dimensionLabels).map(key => {
    const dim = props.dimensions[key]
    return dim ? (dim.confidence || 0) : 0
  })

  const labels = Object.keys(dimensionLabels).map(key => {
    const dim = props.dimensions[key]
    return dim?.value || '-'
  })

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#111827', fontSize: 12 },
      formatter: (params) => {
        const idx = params.dataIndex
        const key = Object.keys(dimensionLabels)[idx]
        const dim = props.dimensions[key]
        const conf = Math.round((dim?.confidence || 0) * 100)
        const bar = '█'.repeat(Math.floor(conf / 10)) + '░'.repeat(10 - Math.floor(conf / 10))
        return `<div style="font-size:13px;font-weight:600;margin-bottom:4px">${dimensionLabels[key]}</div>
                <div style="color:#6b7280;font-size:12px">值: <strong>${dim?.value || '-'}</strong></div>
                <div style="color:#6b7280;font-size:12px">置信度: ${conf}%</div>
                <div style="font-size:11px;color:#2563eb;letter-spacing:1px">${bar}</div>`
      }
    },
    radar: {
      indicator: indicators,
      shape: 'circle',
      radius: '62%',
      splitNumber: 4,
      center: ['50%', '52%'],
      axisName: {
        color: '#6b7280',
        fontSize: 10,
        fontWeight: 600,
        borderRadius: 4,
        padding: [2, 6],
      },
      splitLine: {
        lineStyle: { color: '#f3f4f6', width: 1 }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(37, 99, 235, 0.03)', 'transparent']
        }
      },
      axisLine: {
        lineStyle: { color: '#e5e7eb', width: 1 }
      }
    },
    series: [{
      type: 'radar',
      animationDuration: 1200,
      animationEasing: 'elasticOut',
      data: [{
        value: values,
        name: '学习画像',
        areaStyle: {
          color: {
            type: 'radial',
            x: 0.5,
            y: 0.5,
            r: 0.8,
            colorStops: [
              { offset: 0, color: 'rgba(37, 99, 235, 0.45)' },
              { offset: 0.5, color: 'rgba(37, 99, 235, 0.2)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0.06)' }
            ]
          }
        },
        lineStyle: {
          color: '#2563eb',
          width: 2,
          shadowBlur: 10,
          shadowColor: 'rgba(37, 99, 235, 0.3)'
        },
        itemStyle: {
          color: '#2563eb',
          borderColor: '#fff',
          borderWidth: 2,
          shadowBlur: 8,
          shadowColor: 'rgba(37, 99, 235, 0.4)'
        },
        label: {
          show: true,
          formatter: (p) => labels[p.dataIndex] || '',
          color: '#111827',
          fontSize: 10,
          fontWeight: 600,
          backgroundColor: 'rgba(255,255,255,0.85)',
          padding: [2, 6],
          borderRadius: 10,
          shadowBlur: 4,
          shadowColor: 'rgba(0,0,0,0.08)'
        }
      }]
    }]
  }

  chart.setOption(option, true)
}

const handleResize = () => {
  chart && chart.resize()
}

watch(() => props.dimensions, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart && chart.dispose()
})
</script>

<style scoped>
.profile-radar {
  width: 100%;
  height: 260px;
}
</style>
