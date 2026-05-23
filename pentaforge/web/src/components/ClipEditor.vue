<template>
  <div class="clip-editor">
    <div class="clip-header">
      <span class="section-title" style="margin:0;padding:0;border:0">高光片段</span>
      <span class="clip-count">{{ clips.length }} 个</span>
    </div>
    <div class="clip-list">
      <div v-for="(clip, i) in clips" :key="i" class="clip-card">
        <div class="clip-top">
          <div class="clip-color" :style="{ background: colors[i % colors.length] }" />
          <input
            class="clip-label-input"
            :value="clip.label"
            @input="emitUpdate(i, 'label', $event.target.value)"
            :placeholder="`片段 ${i + 1}`"
          />
          <button class="btn-icon" @click="$emit('removeClip', i)" v-if="clips.length > 1">&times;</button>
        </div>
        <div class="clip-times">
          <label>开始
            <input type="number" step="0.1" :value="clip.start" @input="emitUpdate(i, 'start', parseFloat($event.target.value) || 0)" />
          </label>
          <label>结束
            <input type="number" step="0.1" :value="clip.end" @input="emitUpdate(i, 'end', parseFloat($event.target.value) || 0)" />
          </label>
          <label>时长
            <span class="dur">{{ ((clip.end - clip.start)).toFixed(1) }}s</span>
          </label>
        </div>
        <div class="clip-extra">
          <label>类型
            <select :value="clip.kill_type" @change="emitUpdate(i, 'kill_type', $event.target.value)">
              <option value="">-- 无 --</option>
              <option value="double_kill">双杀</option>
              <option value="triple_kill">三杀</option>
              <option value="quadra_kill">四杀</option>
              <option value="penta_kill">五杀</option>
            </select>
          </label>
          <label>特效偏移
            <input type="number" step="0.1" :value="clip.sfx_offset ?? ''" @input="emitUpdate(i, 'sfx_offset', $event.target.value ? parseFloat($event.target.value) : null)" placeholder="自动" />
          </label>
        </div>
      </div>
    </div>
    <button class="btn btn-primary add-clip-btn" @click="$emit('addClip')">+ 添加片段</button>
  </div>
</template>

<script setup>
const props = defineProps({
  clips: { type: Array, default: () => [] },
  sourceIndex: { type: Number, default: 0 },
  colors: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:clips', 'addClip', 'removeClip'])

function emitUpdate(clipIndex, field, value) {
  const clips = props.clips.map((c, j) => j === clipIndex ? { ...c, [field]: value } : { ...c })
  emit('update:clips', clips)
}
</script>

<style scoped>
.clip-editor {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 12px;
}
.clip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.clip-count {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
}
.clip-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
  margin-bottom: 10px;
}
.clip-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 10px;
  transition: border-color var(--transition);
}
.clip-card:hover { border-color: var(--border-accent); }

.clip-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.clip-color {
  width: 10px; height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}
.clip-label-input {
  flex: 1;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--border);
  color: var(--text-primary);
  padding: 3px 0;
  font-size: 13px;
  font-weight: 500;
}
.clip-label-input:focus {
  border-bottom-color: var(--gold-dim);
  box-shadow: none;
}
.clip-times {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}
.clip-times label {
  flex: 1;
  font-size: 10px;
}
.clip-times input {
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 4px 8px;
}
.dur {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--gold);
  font-weight: 500;
}
.clip-extra {
  display: flex;
  gap: 8px;
}
.clip-extra label {
  flex: 1;
  font-size: 10px;
}
.clip-extra select, .clip-extra input {
  font-size: 11px;
  padding: 4px 6px;
}
.add-clip-btn {
  width: 100%;
  text-align: center;
}
</style>
