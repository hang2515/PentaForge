<template>
  <div class="clip-editor">
    <div class="clip-header">
      <span class="section-title" style="margin:0;padding:0;border:0">高光片段</span>
      <span class="clip-count">{{ clips.length }} 个</span>
    </div>
    <div class="clip-list">
      <div v-for="(clip, i) in clips" :key="`${clip.sourceIndex}-${i}`" class="clip-card">
        <div class="clip-source" v-if="sources.length > 1">
          <span class="source-tag">{{ sources[clip.sourceIndex]?.name || `源 ${clip.sourceIndex + 1}` }}</span>
        </div>
        <div class="clip-top">
          <div class="clip-color" :style="{ background: colors[i % colors.length] }" />
          <input
            class="clip-label-input"
            :value="clip.label"
            @input="emitUpdate(clip.sourceIndex, getLocalIndex(clip.sourceIndex, i), 'label', $event.target.value)"
            :placeholder="`片段 ${i + 1}`"
          />
        </div>
        <div class="clip-times">
          <label>开始
            <input type="number" step="0.1" :value="clip.start" @input="emitUpdate(clip.sourceIndex, getLocalIndex(clip.sourceIndex, i), 'start', parseFloat($event.target.value) || 0)" />
          </label>
          <label>结束
            <input type="number" step="0.1" :value="clip.end" @input="emitUpdate(clip.sourceIndex, getLocalIndex(clip.sourceIndex, i), 'end', parseFloat($event.target.value) || 0)" />
          </label>
          <label>时长
            <span class="dur">{{ ((clip.end - clip.start)).toFixed(1) }}s</span>
          </label>
        </div>
        <div class="clip-extra">
          <label>类型
            <select :value="clip.kill_type" @change="emitUpdate(clip.sourceIndex, getLocalIndex(clip.sourceIndex, i), 'kill_type', $event.target.value)">
              <option value="">-- 无 --</option>
              <option value="double_kill">双杀</option>
              <option value="triple_kill">三杀</option>
              <option value="quadra_kill">四杀</option>
              <option value="penta_kill">五杀</option>
            </select>
          </label>
          <label>特效偏移
            <input type="number" step="0.1" :value="clip.sfx_offset ?? ''" @input="emitUpdate(clip.sourceIndex, getLocalIndex(clip.sourceIndex, i), 'sfx_offset', $event.target.value ? parseFloat($event.target.value) : null)" placeholder="自动" />
          </label>
        </div>
      </div>
      <div v-if="i < clips.length - 1" class="transition-row">
        <div class="transition-title">到下一段的转场</div>
        <div class="clip-row">
          <label>类型
            <select :value="transitionFor(clip).type" @change="setTransitionField(clip, 'type', $event.target.value)">
              <option value="fade">淡入淡出</option>
              <option value="fadeblack">淡黑</option>
              <option value="fadewhite">淡白</option>
              <option value="dissolve">溶解</option>
              <option value="wipeleft">向左擦除</option>
              <option value="wiperight">向右擦除</option>
              <option value="wipeup">向上擦除</option>
              <option value="wipedown">向下擦除</option>
              <option value="slideleft">向左滑动</option>
              <option value="slideright">向右滑动</option>
              <option value="circleopen">圆形打开</option>
              <option value="circleclose">圆形关闭</option>
            </select>
          </label>
          <label>持续时间 (秒)
            <input type="number" step="0.1" min="0" :value="transitionFor(clip).duration" @input="setTransitionField(clip, 'duration', parseFloat($event.target.value) || 0)" />
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
  sources: { type: Array, default: () => [] },
  colors: { type: Array, default: () => [] },
})
const emit = defineEmits(['updateClip', 'addClip', 'removeClip'])

// Get local clip index within a source, given the global flat index
function getLocalIndex(sourceIndex, globalIndex) {
  let count = 0
  for (let i = 0; i < globalIndex; i++) {
    if (props.clips[i].sourceIndex === sourceIndex) count++
  }
  return count
}

function emitUpdate(sourceIndex, clipIndex, field, value) {
  emit('updateClip', sourceIndex, clipIndex, { [field]: value })
}

function transitionFor(clip) {
  return clip.transition_after || { type: 'fade', duration: 0.3 }
}

function setTransitionField(clip, field, value) {
  const current = transitionFor(clip)
  const localIdx = getLocalIndex(clip.sourceIndex, props.clips.indexOf(clip))
  emit('updateClip', clip.sourceIndex, localIdx, {
    transition_after: { ...current, [field]: value },
  })
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

.clip-source {
  margin-bottom: 4px;
}
.source-tag {
  font-size: 10px;
  color: var(--gold-dim);
  background: var(--gold-glow);
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 500;
}

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
}
.transition-row {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}
.transition-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.btn-icon {
  background: none;
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
