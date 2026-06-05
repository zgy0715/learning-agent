<template>
  <div class="mindmap-view" ref="containerRef"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
})

const containerRef = ref(null)
let markmap = null

const renderMarkmap = () => {
  if (!containerRef.value || !props.content) return

  const transformer = new Transformer()
  const { root } = transformer.transform(props.content)

  if (markmap) {
    markmap.setData(root)
  } else {
    markmap = Markmap.create(containerRef.value, {
      autoFit: true,
      duration: 300
    }, root)
  }
}

watch(() => props.content, () => {
  renderMarkmap()
})

onMounted(() => {
  renderMarkmap()
})
</script>

<style scoped>
.mindmap-view {
  width: 100%;
  min-height: 300px;
}
</style>
