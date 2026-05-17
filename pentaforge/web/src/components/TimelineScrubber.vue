<template>
  <div class="timeline-wrapper" ref="wrapperEl">
    <canvas ref="canvasEl" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp" @keydown="onKeyDown" tabindex="0" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  videoDuration: { type: Number, default: 0 },
  clips: { type: Array, default: () => [] },
  currentTime: { type: Number, default: 0 },
})

const emit = defineEmits(['update:clips', 'seek', 'addClip'])

const canvasEl = ref(null)
const wrapperEl = ref(null)
let pixelsPerSecond = 1
let rafId = null
let dragging = null

const COLORS = ['#e07b3c', '#d4a574', '#c0392b', '#f4a460', '#e8b86d', '#c49a6c', '#b5651d', '#daa520']
const BAR_H = 48
const HANDLE_W = 8
const PADDING_X = 8

function width() { return canvasEl.value?.width || 800 }
function layoutW() { return width() - PADDING_X * 2 }

onMounted(() => {
  resizeCanvas()
  const ro = new ResizeObserver(() => resizeCanvas())
  ro.observe(wrapperEl.value)
  loop()
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  window.removeEventListener('keydown', onKeyDown)
})

function resizeCanvas() {
  if (!canvasEl.value || !wrapperEl.value) return
  const rect = wrapperEl.value.getBoundingClientRect()
  canvasEl.value.width = rect.width
  canvasEl.value.height = BAR_H + 24
  pixelsPerSecond = layoutW() / (props.videoDuration || 1)
}

function px(t) { return PADDING_X + t * pixelsPerSecond }
function time(x) { return (x - PADDING_X) / pixelsPerSecond }

function loop() {
  draw()
  rafId = requestAnimationFrame(loop)
}

function draw() {
  const c = canvasEl.value
  if (!c) return
  const ctx = c.getContext('2d')
  const w = c.width
  const h = c.height
  ctx.clearRect(0, 0, w, h)

  // ruler ticks
  ctx.fillStyle = '#8d6e63'
  ctx.font = '10px monospace'
  const dur = props.videoDuration || 1
  let tickInterval = 1
  if (dur > 600) tickInterval = 60
  else if (dur > 300) tickInterval = 30
  else if (dur > 120) tickInterval = 10
  else if (dur > 30) tickInterval = 5

  for (let t = 0; t <= dur; t += tickInterval) {
    const x = px(t)
    ctx.fillRect(x, 6, 1, 6)
    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60)
    ctx.fillText(`${m}:${String(s).padStart(2, '0')}`, x + 2, 14)
  }

  const barY = 18

  // background bar
  ctx.fillStyle = '#f5ede3'
  ctx.fillRect(PADDING_X, barY, layoutW(), BAR_H)

  // clip regions
  props.clips.forEach((clip, i) => {
    const x1 = px(clip.start)
    const x2 = px(clip.end)
    const color = COLORS[i % COLORS.length]
    ctx.fillStyle = color
    ctx.globalAlpha = 0.35
    ctx.fillRect(x1, barY, x2 - x1, BAR_H)
    ctx.globalAlpha = 1
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.strokeRect(x1, barY, x2 - x1, BAR_H)

    // handles
    ctx.fillStyle = color
    ctx.fillRect(x1 - HANDLE_W / 2, barY, HANDLE_W, BAR_H)
    ctx.fillRect(x2 - HANDLE_W / 2, barY, HANDLE_W, BAR_H)

    // label
    const label = clip.label || clip.kill_type || `片段 ${i + 1}`
    ctx.fillStyle = '#4a3728'
    ctx.font = '11px sans-serif'
    const textW = ctx.measureText(label).width
    if (textW + 8 < x2 - x1) {
      ctx.fillText(label, x1 + 4, barY + BAR_H / 2 + 4)
    }
  })

  // playhead
  const pxHead = px(props.currentTime)
  ctx.strokeStyle = '#c0392b'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(pxHead, barY)
  ctx.lineTo(pxHead, barY + BAR_H)
  ctx.stroke()
}

function hitTest(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const barY = 18
  if (y < barY || y > barY + BAR_H) return { type: 'none' }
  for (let i = 0; i < props.clips.length; i++) {
    const clip = props.clips[i]
    const x1 = px(clip.start)
    const x2 = px(clip.end)
    if (Math.abs(x - x1) < HANDLE_W) return { type: 'handle', clipIndex: i, side: 'start' }
    if (Math.abs(x - x2) < HANDLE_W) return { type: 'handle', clipIndex: i, side: 'end' }
    if (x >= x1 && x <= x2) return { type: 'body', clipIndex: i }
  }
  return { type: 'empty', time: time(x) }
}

function onMouseDown(e) {
  const hit = hitTest(e)
  if (hit.type === 'none') return

  const rect = canvasEl.value.getBoundingClientRect()
  const x = e.clientX - rect.left

  if (hit.type === 'handle' || hit.type === 'body') {
    dragging = {
      type: hit.type,
      clipIndex: hit.clipIndex,
      side: hit.side,
      startX: x,
      origStart: props.clips[hit.clipIndex].start,
      origEnd: props.clips[hit.clipIndex].end,
    }
    e.preventDefault()
  } else if (hit.type === 'empty') {
    emit('seek', Math.max(0, hit.time))
  }
}

function onMouseMove(e) {
  if (!canvasEl.value) return
  const rect = canvasEl.value.getBoundingClientRect()
  const x = e.clientX - rect.left

  if (dragging) {
    const dx = (x - dragging.startX) / pixelsPerSecond
    const clips = [...props.clips]
    const clip = { ...clips[dragging.clipIndex] }

    if (dragging.type === 'handle') {
      if (dragging.side === 'start') {
        clip.start = Math.max(0, Math.min(dragging.origStart + dx, clip.end - 0.1))
      } else {
        clip.end = Math.max(clip.start + 0.1, dragging.origEnd + dx)
      }
    } else if (dragging.type === 'body') {
      const duration = clip.end - clip.start
      clip.start = Math.max(0, Math.min(dragging.origStart + dx, (props.videoDuration || 9999) - duration))
      clip.end = clip.start + duration
    }

    clips[dragging.clipIndex] = clip
    emit('update:clips', clips)
    e.preventDefault()
  } else {
    const hit = hitTest(e)
    canvasEl.value.style.cursor = hit.type === 'none' ? 'default' : hit.type === 'empty' ? 'pointer' : 'col-resize'
  }
}

function onMouseUp() {
  dragging = null
}

function onKeyDown(e) {
}
</script>

<style scoped>
.timeline-wrapper {
  width: 100%;
}
.timeline-wrapper canvas {
  width: 100%;
  height: auto;
  display: block;
  cursor: pointer;
  outline: none;
}
</style>
