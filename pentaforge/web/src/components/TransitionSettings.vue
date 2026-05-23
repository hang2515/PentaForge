<template>
  <div class="transition-settings">
    <div class="row">
      <label>类型
        <select :value="store.transitions.type" @change="store.transitions.type = $event.target.value">
          <option value="fade">淡入淡出</option>
          <option value="fadeblack">淡黑</option>
          <option value="fadewhite">淡白</option>
          <option value="dissolve">溶解</option>
          <option value="wipeleft">左擦除</option>
          <option value="wiperight">右擦除</option>
          <option value="wipeup">上擦除</option>
          <option value="wipedown">下擦除</option>
        </select>
      </label>
    </div>
    <label>持续时间 <span class="val">{{ store.transitions.duration.toFixed(1) }}s</span>
      <input type="range" min="0.1" max="2" step="0.1" :value="store.transitions.duration" @input="store.transitions.duration = parseFloat($event.target.value)" />
    </label>
  </div>
</template>

<script setup>
import { useConfigStore } from '../stores/config.js'
const store = useConfigStore()
</script>

<style scoped>
.transition-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.row { display: flex; gap: 8px; }
.row label { flex: 1; }
.val {
  font-family: var(--font-mono);
  color: var(--gold);
  font-size: 10px;
}
</style>
