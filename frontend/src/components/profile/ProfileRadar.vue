<template>
  <div class="profile-radar" ref="chartRef"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
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

  chart = echarts.init(chartRef.value)
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
    return dim ? dim.confidence || 0 : 0
  })

  const option = {
    radar: {
      indicator: indicators,
      shape: 'circle',
      splitNumber: 5,
      axisName: {
        color: '#666',
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: '#e0e0e0'
        }
      },
      splitArea: {
        areaStyle: {
          color: ['#fff', '#f5f5f5']
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '学习画像',
        areaStyle: {
          color: 'rgba(64, 158, 255, 0.2)'
        },
        lineStyle: {
          color: '#409eff'
        },
        itemStyle: {
          color: '#409eff'
        }
      }]
    }]
  }

  chart.setOption(option)
}

watch(() => props.dimensions, () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => {
    chart && chart.resize()
  })
})
</script>

<style scoped>
.profile-radar {
  width: 100%;
  height: 250px;
}
</style>
