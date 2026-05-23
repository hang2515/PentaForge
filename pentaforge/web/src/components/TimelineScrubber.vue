<template>
  <div class="timeline-panel">
    <div class="timeline-header">
      <span class="section-title" style="margin:0;padding:0;border:0">时间轴</span>
      <span class="timecode">{{ formatTime(currentTime) }} / {{ formatTime(videoDuration) }}</span>
    </div>
    <div class="timeline-wrapper" ref="wrapperEl">
      <canvas ref="canvasEl" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp" @wheel="onWheel" />
    </div>
    <div class="timeline-controls">
      <button class="btn btn-sm" @click="zoomOut">-</button>
      <span class="zoom-label">{{ zoomPct }}%</span>
      <button class="btn btn-sm" @click="zoomIn">+</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  videoDuration: { type: Number, default: 0 },
  clips: { type: Array, default: () => [] },
  currentTime: { type: Number, default: 0 },
  colors: { type: Array, default: () => ['#c8a84e', '#4a90d9', '#e0775c', '#5eaa8e', '#b08cd4', '#e0a040'] },
})

const emit = defineEmits(['update:clips', 'seek'])

const canvasEl = ref(null)
const wrapperEl = ref(null)
const zoom = ref(1)
const zoomPct = ref(100)

let pixelsPerSecond = 60
let rafId = null
let dragging = null
let hoveredHandle = null
let scrubTime = null  // Local playhead position during scrubbing (avoids expensive video seeks)

const BAR_H = 52
const HANDLE_W = 10
const PADDING_X = 10
const RULER_H = 18
const HANDLE_HIT_TOLERANCE = 6

function width() { return (canvasEl.value?.width || 900) }
function layoutW() { return width() - PADDING_X * 2 }

onMounted(() => {
  resizeCanvas()
  const ro = new ResizeObserver(() => resizeCanvas())
  ro.observe(wrapperEl.value)
  loop()
})

onUnmounted(() => { cancelAnimationFrame(rafId) })

watch(() => props.currentTime, () => { draw() })

// Auto-fit zoom when a new video is loaded
watch(() => props.videoDuration, (dur) => {
  if (dur <= 0) return
  // Target: show ~120s window, or full video if shorter
  const targetWindow = Math.min(dur, 120)
  const rawZoom = dur / targetWindow
  zoom.value = Math.max(1, Math.min(5, Math.round(rawZoom * 10) / 10))
  zoomPct.value = Math.round(zoom.value * 100)
  updatePPS()
  draw()
})

function resizeCanvas() {
  if (!canvasEl.value || !wrapperEl.value) return
  const rect = wrapperEl.value.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  canvasEl.value.width = rect.width * dpr
  canvasEl.value.height = (BAR_H + RULER_H + 4) * dpr
  canvasEl.value.style.width = rect.width + 'px'
  canvasEl.value.style.height = (BAR_H + RULER_H + 4) + 'px'
  const ctx = canvasEl.value.getContext('2d')
  ctx.scale(dpr, dpr)
  updatePPS()
}

function updatePPS() {
  pixelsPerSecond = (layoutW() / (Math.max(props.videoDuration, 1))) * zoom.value
}

function px(t) { return PADDING_X + t * pixelsPerSecond }
function time(x) { return (x - PADDING_X) / pixelsPerSecond }

function formatTime(sec) {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  const ms = Math.floor((sec % 1) * 10)
  return `${m}:${String(s).padStart(2, '0')}.${ms}`
}

function loop() {
  draw()
  rafId = requestAnimationFrame(loop)
}

function draw() {
  const c = canvasEl.value
  if (!c) return
  const ctx = c.getContext('2d')
  const w = width()
  ctx.clearRect(0, 0, w * 2, (BAR_H + RULER_H + 4) * 2)

  const dur = Math.max(props.videoDuration, 1)
  // Calculate visible time range
  const visStart = time(0)
  const visEnd = time(layoutW() + PADDING_X)

  // Ruler
  ctx.fillStyle = '#9ca3af'
  ctx.font = '10px "JetBrains Mono", monospace'
  ctx.textBaseline = 'top'

  let tickStep = 1
  if (zoom.value < 0.3) tickStep = 60
  else if (zoom.value < 0.6) tickStep = 30
  else if (zoom.value < 1) tickStep = 10
  else if (zoom.value < 2) tickStep = 5
  else tickStep = 1

  for (let t = Math.floor(visStart / tickStep) * tickStep; t <= visEnd; t += tickStep) {
    if (t < 0 || t > dur) continue
    const x = px(t)
    if (x < PADDING_X || x > layoutW() + PADDING_X) continue

    // Major tick
    ctx.strokeStyle = '#c8cdd5'
    ctx.lineWidth = 0.5
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, RULER_H)
    ctx.stroke()

    const m = Math.floor(t / 60)
    const s = Math.floor(t % 60)
    ctx.fillStyle = '#6b7280'
    ctx.fillText(`${m}:${String(s).padStart(2, '0')}`, x + 3, 2)
  }

  // Minor ticks
  if (tickStep > 1) {
    const minorStep = tickStep / 5
    for (let t = Math.floor(visStart / minorStep) * minorStep; t <= visEnd; t += minorStep) {
      if (t < 0 || t > dur) continue
      const x = px(t)
      if (x < PADDING_X || x > layoutW() + PADDING_X) continue
      ctx.fillStyle = '#dde1e6'
      ctx.fillRect(x, RULER_H - 6, 1, 6)
    }
  }

  const barY = RULER_H + 4

  // Background track
  ctx.fillStyle = '#e8eaef'
  ctx.strokeStyle = '#dde1e6'
  ctx.lineWidth = 1
  const bgX = px(0)
  const bgW = px(dur) - bgX
  ctx.beginPath()
  ctx.roundRect(Math.max(PADDING_X, bgX), barY, Math.min(bgW, layoutW()), BAR_H, 4)
  ctx.fill()
  ctx.stroke()

  // Clip regions
  props.clips.forEach((clip, i) => {
    const x1 = Math.max(PADDING_X, px(clip.start))
    const x2 = Math.min(PADDING_X + layoutW(), px(clip.end))
    if (x2 <= x1) return

    const color = props.colors[i % props.colors.length]

    // Clip fill
    const grad = ctx.createLinearGradient(0, barY, 0, barY + BAR_H)
    grad.addColorStop(0, color + '30')
    grad.addColorStop(1, color + '10')
    ctx.fillStyle = grad
    ctx.beginPath()
    ctx.roundRect(x1, barY + 2, x2 - x1, BAR_H - 4, 3)
    ctx.fill()

    // Clip border
    ctx.strokeStyle = color + '80'
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.roundRect(x1, barY + 2, x2 - x1, BAR_H - 4, 3)
    ctx.stroke()

    // Glow line at top edge
    ctx.strokeStyle = color
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(x1 + 4, barY + 3)
    ctx.lineTo(x2 - 4, barY + 3)
    ctx.stroke()

    // Handles — clamp to visible area so both sides are always draggable
    const visLeft = PADDING_X
    const visRight = PADDING_X + layoutW()
    const handleClamp = (hx) => Math.max(visLeft, Math.min(visRight, hx))

    const drawHandle = (hx, side) => {
      const cx = handleClamp(hx)
      const isHovered = hoveredHandle && hoveredHandle.clipIndex === i && hoveredHandle.side === side
      const hglow = ctx.createLinearGradient(0, barY, 0, barY + BAR_H)
      hglow.addColorStop(0, color)
      hglow.addColorStop(1, isHovered ? (color + '60') : (color + '40'))
      ctx.fillStyle = hglow
      ctx.beginPath()
      const r = side === 'start' ? [3, 0, 0, 3] : [0, 3, 3, 0]
      ctx.roundRect(cx - HANDLE_W / 2, barY, HANDLE_W, BAR_H, r)
      ctx.fill()
      if (isHovered) {
        ctx.strokeStyle = color
        ctx.lineWidth = 1.5
        ctx.stroke()
      }
    }

    drawHandle(x1, 'start')
    drawHandle(x2, 'end')

    // Label
    const label = clip.label || clip.kill_type || `${i + 1}`
    if (x2 - x1 > 30) {
      ctx.fillStyle = '#1a1d2e'
      ctx.font = '11px "Noto Sans SC", sans-serif'
      ctx.textBaseline = 'middle'
      ctx.save()
      ctx.beginPath()
      ctx.rect(x1 + 6, barY, x2 - x1 - 12, BAR_H)
      ctx.clip()
      ctx.fillText(label, x1 + 8, barY + BAR_H / 3)
      // Time range
      const dur = (clip.end - clip.start).toFixed(1)
      ctx.fillStyle = '#6b7280'
      ctx.font = '9px "JetBrains Mono", monospace'
      ctx.fillText(`${dur}s`, x1 + 8, barY + BAR_H * 2 / 3)
      ctx.restore()
    }
  })

  // Playhead — use local scrubTime during drag for smooth rendering
  const displayTime = scrubTime != null ? scrubTime : props.currentTime
  const pxHead = px(displayTime)
  if (pxHead >= PADDING_X && pxHead <= PADDING_X + layoutW()) {
    // Glow
    const glow = ctx.createLinearGradient(pxHead, barY, pxHead, barY + BAR_H)
    glow.addColorStop(0, 'rgba(224,96,80,0.2)')
    glow.addColorStop(1, 'rgba(224,96,80,0)')
    ctx.fillStyle = glow
    ctx.fillRect(pxHead - 8, barY, 16, BAR_H)

    // Line
    ctx.strokeStyle = '#e06050'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.moveTo(pxHead, barY - 2)
    ctx.lineTo(pxHead, barY + BAR_H + 2)
    ctx.stroke()

    // Triangle on top
    ctx.fillStyle = '#e06050'
    ctx.beginPath()
    ctx.moveTo(pxHead - 5, barY - 6)
    ctx.lineTo(pxHead + 5, barY - 6)
    ctx.lineTo(pxHead, barY)
    ctx.fill()
  }
}

// ── Interaction ──

function hitTest(e) {
  const rect = canvasEl.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const barY = RULER_H + 4

  const visLeft = PADDING_X
  const visRight = PADDING_X + layoutW()

  // Check playhead for scrubbing
  const displayTime = scrubTime != null ? scrubTime : props.currentTime
  const pxHead = px(displayTime)
  if (pxHead >= visLeft && pxHead <= visRight && Math.abs(x - pxHead) < 8) {
    return { type: 'playhead', time: time(x) }
  }

  if (y < barY || y > barY + BAR_H) return { type: 'ruler', time: time(x) }
  for (let i = 0; i < props.clips.length; i++) {
    const clip = props.clips[i]
    const x1 = px(clip.start)
    const x2 = px(clip.end)
    const cx1 = Math.max(visLeft, Math.min(visRight, x1))
    const cx2 = Math.max(visLeft, Math.min(visRight, x2))
    if (Math.abs(x - cx1) < HANDLE_W + HANDLE_HIT_TOLERANCE) return { type: 'handle', clipIndex: i, side: 'start' }
    if (Math.abs(x - cx2) < HANDLE_W + HANDLE_HIT_TOLERANCE) return { type: 'handle', clipIndex: i, side: 'end' }
    if (x >= x1 && x <= x2) return { type: 'body', clipIndex: i }
  }
  return { type: 'empty', time: time(x) }
}

function onMouseDown(e) {
  const hit = hitTest(e)
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
  } else {
    // Ruler, empty area, or playhead — seek video once, then scrub locally
    scrubTime = Math.max(0, hit.time)
    emit('seek', scrubTime)
    dragging = { type: 'scrub' }
    e.preventDefault()
  }
}

function onMouseMove(e) {
  if (!canvasEl.value) return
  const rect = canvasEl.value.getBoundingClientRect()
  const x = e.clientX - rect.left

  if (dragging) {
    if (dragging.type === 'scrub') {
      // Only update local time for smooth canvas rendering — seek on mouseup
      scrubTime = Math.max(0, time(x))
    } else {
      const dx = (x - dragging.startX) / pixelsPerSecond
      const clips = props.clips.map(c => ({ ...c }))
      const clip = clips[dragging.clipIndex]

      if (dragging.type === 'handle') {
        if (dragging.side === 'start') {
          clip.start = Math.max(0, Math.min(dragging.origStart + dx, clip.end - 0.1))
        } else {
          clip.end = Math.max(clip.start + 0.1, Math.min(props.videoDuration, dragging.origEnd + dx))
        }
      } else if (dragging.type === 'body') {
        const dur = clip.end - clip.start
        clip.start = Math.max(0, Math.min(dragging.origStart + dx, (props.videoDuration || 9999) - dur))
        clip.end = clip.start + dur
      }

      emit('update:clips', clips)
    }
    e.preventDefault()
  } else {
    const hit = hitTest(e)
    if (hit.type === 'handle') {
      canvasEl.value.style.cursor = 'ew-resize'
      hoveredHandle = { clipIndex: hit.clipIndex, side: hit.side }
    } else if (hit.type === 'body') {
      canvasEl.value.style.cursor = 'grab'
      hoveredHandle = null
    } else if (hit.type === 'playhead') {
      canvasEl.value.style.cursor = 'ew-resize'
      hoveredHandle = null
    } else if (hit.type === 'empty' || hit.type === 'ruler') {
      canvasEl.value.style.cursor = 'pointer'
      hoveredHandle = null
    } else {
      canvasEl.value.style.cursor = 'default'
      hoveredHandle = null
    }
  }
}

function onMouseUp() {
  if (dragging && dragging.type === 'scrub' && scrubTime != null) {
    emit('seek', scrubTime)
  }
  dragging = null
  scrubTime = null
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.2 : 0.2
  zoom.value = Math.max(0.1, Math.min(5, zoom.value + delta))
  zoomPct.value = Math.round(zoom.value * 100)
  updatePPS()
  draw()
}

function zoomIn() {
  zoom.value = Math.min(5, zoom.value + 0.2)
  zoomPct.value = Math.round(zoom.value * 100)
  updatePPS()
  draw()
}

function zoomOut() {
  zoom.value = Math.max(0.1, zoom.value - 0.2)
  zoomPct.value = Math.round(zoom.value * 100)
  updatePPS()
  draw()
}
</script>

<style scoped>
.timeline-panel {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 12px;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.timecode {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-secondary);
}
.timeline-wrapper {
  width: 100%;
  border-radius: var(--radius);
  overflow: hidden;
}
.timeline-wrapper canvas {
  width: 100%;
  height: auto;
  display: block;
  cursor: crosshair;
}
.timeline-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 6px;
}
.btn-sm {
  padding: 2px 10px;
  font-size: 14px;
  line-height: 1;
}
.zoom-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  min-width: 36px;
  text-align: center;
}
</style>
