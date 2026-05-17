<template>
  <div class="export-settings">
    <h3>导出设置</h3>
    <div class="row">
      <label>分辨率<input :value="exp.resolution" @input="set('resolution', $event.target.value)" placeholder="1920x1080" /></label>
      <label>帧率<input type="number" :value="exp.fps" @input="set('fps', parseInt($event.target.value) || 60)" /></label>
    </div>
    <div class="row">
      <label>编码器
        <select :value="exp.codec" @change="set('codec', $event.target.value)">
          <option value="libx264">H.264</option>
          <option value="libx265">H.265</option>
        </select>
      </label>
      <label>码率<input :value="exp.bitrate" @input="set('bitrate', $event.target.value)" placeholder="12M" /></label>
    </div>
    <label>编码预设
      <select :value="exp.preset" @change="set('preset', $event.target.value)">
        <option value="ultrafast">ultrafast</option>
        <option value="superfast">superfast</option>
        <option value="veryfast">veryfast</option>
        <option value="faster">faster</option>
        <option value="fast">fast</option>
        <option value="medium">medium</option>
        <option value="slow">slow</option>
      </select>
    </label>
    <label>输出文件<input :value="output" @input="$emit('update:output', $event.target.value)" placeholder="highlight_output.mp4" /></label>
  </div>
</template>

<script setup>
const props = defineProps({ exp: Object, output: String })
const emit = defineEmits(['update:exp', 'update:output'])

function set(key, val) {
  emit('update:exp', { ...props.exp, [key]: val })
}
</script>

<style scoped>
h3 { margin: 0 0 8px; font-size: 14px; color: #5c3d2e; }
.row { display: flex; gap: 8px; }
.row label { flex: 1; }
label { display: flex; flex-direction: column; gap: 2px; font-size: 12px; color: #8d6e63; margin-bottom: 6px; }
input, select { background: #fef9f4; border: 1px solid #d4b896; color: #4a3728; padding: 4px 6px; border-radius: 3px; font-size: 12px; }
</style>
