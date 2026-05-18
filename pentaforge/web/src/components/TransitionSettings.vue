<template>
  <div class="transition-settings">
    <h3>默认转场设置</h3>
    <label>转场类型
      <select :value="type" @change="$emit('update:type', $event.target.value)">
        <option value="fade">淡入淡出</option>
        <option value="fadeblack">淡黑</option>
        <option value="fadewhite">淡白</option>
        <option value="dissolve">溶解</option>
        <option value="wipeleft">向左擦除</option>
        <option value="wiperight">向右擦除</option>
        <option value="wipeup">向上擦除</option>
        <option value="wipedown">向下擦除</option>
      </select>
    </label>
    <label>持续时间 (秒)<input type="number" step="0.1" min="0" :value="duration" @input="$emit('update:duration', parseFloat($event.target.value) || 0)" /></label>
  </div>
</template>

<script setup>
defineProps({ type: String, duration: Number })
defineEmits(['update:type', 'update:duration'])
</script>

<style scoped>
h3 { margin: 0 0 8px; font-size: 14px; color: #5c3d2e; }
label { display: flex; flex-direction: column; gap: 2px; font-size: 12px; color: #8d6e63; margin-bottom: 6px; }
input, select { background: #fef9f4; border: 1px solid #d4b896; color: #4a3728; padding: 4px 6px; border-radius: 3px; font-size: 12px; }
</style>
