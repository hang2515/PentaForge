<template>
  <div class="clip-editor">
    <h3>剪辑片段</h3>
    <div v-for="(clip, i) in clips" :key="i" class="clip-card">
      <div class="clip-header">
        <span class="clip-label">{{ clip.label || clip.kill_type || `片段 ${i + 1}` }}</span>
        <button v-if="clips.length > 1" class="btn-icon" @click="remove(i)" title="删除片段">x</button>
      </div>
      <div class="clip-row">
        <label>开始 (秒)<input type="number" step="0.1" :value="clip.start" @input="setTime(i, 'start', $event)" /></label>
        <label>结束 (秒)<input type="number" step="0.1" :value="clip.end" @input="setTime(i, 'end', $event)" /></label>
        <label>时长<div class="dur">{{ (clip.end - clip.start).toFixed(1) }}s</div></label>
      </div>
      <div class="clip-row">
        <label>击杀类型
          <select :value="clip.kill_type" @change="setField(i, 'kill_type', $event.target.value)">
            <option value="">无</option>
            <option value="double_kill">双杀</option>
            <option value="triple_kill">三杀</option>
            <option value="quadra_kill">四杀</option>
            <option value="penta_kill">五杀</option>
          </select>
        </label>
        <label>标签<input :value="clip.label" @input="setField(i, 'label', $event.target.value)" placeholder="可选" /></label>
      </div>
      <div class="clip-row">
        <label>SFX 偏移 (秒)<input type="number" step="0.1" :value="clip.sfx_offset ?? ''" @input="setField(i, 'sfx_offset', $event.target.value ? parseFloat($event.target.value) : null)" placeholder="自动" /></label>
        <label>独立 BGM<input :value="clip.bgm" @input="setField(i, 'bgm', $event.target.value)" placeholder="使用全局BGM" /></label>
      </div>
    </div>
    <button class="btn" @click="add">+ 添加片段</button>
  </div>
</template>

<script setup>
const props = defineProps({ clips: Array })
const emit = defineEmits(['update:clips'])

function updateClips(clips) { emit('update:clips', clips) }

function add() {
  const clips = [...props.clips, { start: 0, end: 5, kill_type: '', label: '', sfx_offset: null, bgm: '' }]
  updateClips(clips)
}

function remove(i) {
  const clips = props.clips.filter((_, j) => j !== i)
  updateClips(clips)
}

function setTime(i, side, e) {
  const v = parseFloat(e.target.value) || 0
  const clips = props.clips.map((c, j) => j === i ? { ...c, [side]: v } : c)
  updateClips(clips)
}

function setField(i, field, value) {
  const clips = props.clips.map((c, j) => j === i ? { ...c, [field]: value } : c)
  updateClips(clips)
}
</script>

<style scoped>
.clip-card {
  background: #fff;
  border: 1px solid #e8d5c4;
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}
.clip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.clip-label { font-weight: 600; font-size: 13px; color: #5c3d2e; }
.clip-row {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}
.clip-row label {
  flex: 1;
  font-size: 11px;
  color: #8d6e63;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.clip-row input, .clip-row select {
  background: #fef9f4;
  border: 1px solid #d4b896;
  color: #4a3728;
  padding: 4px 6px;
  border-radius: 3px;
  font-size: 12px;
  width: 100%;
  box-sizing: border-box;
}
.dur { color: #d4742b; font-size: 12px; margin-top: auto; }
.btn { margin-top: 6px; }
.btn-icon {
  background: none;
  border: none;
  color: #c0392b;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
</style>
