import { defineStore } from 'pinia'
import yaml from 'js-yaml'

const defaultExport = {
  resolution: '1920x1080',
  fps: 60,
  codec: 'libx264',
  bitrate: '12M',
  preset: 'medium',
}

const defaultTransitions = {
  type: 'fade',
  duration: 0.3,
}

const defaultSfx = {
  double_kill: 'assets/sfx/double_kill.mp3',
  triple_kill: 'assets/sfx/triple_kill.mp3',
  quadra_kill: 'assets/sfx/quadra_kill.mp3',
  penta_kill: 'assets/sfx/penta_kill.mp3',
}

function emptyClip() {
  return { start: 0, end: 5, kill_type: '', label: '', sfx_offset: null, bgm: '' }
}

export const useConfigStore = defineStore('config', {
  state: () => ({
    source: '',
    output: 'highlight_output.mp4',
    bgm: '',
    bgm_volume: 0.3,
    sfx: { ...defaultSfx },
    sfx_volume: 0.85,
    audio_enabled: true,
    transitions: { ...defaultTransitions },
    export: { ...defaultExport },
    clips: [emptyClip()],
    temp_dir: '',

    // Runtime state
    videoInfo: null,
    activeJobId: null,
    pipelineStatus: null,
    pipelineMessages: [],
  }),

  getters: {
    yamlText() {
      const obj = {
        source: this.source,
        output: this.output,
        bgm: this.bgm || undefined,
        bgm_volume: this.bgm_volume,
        sfx: Object.keys(this.sfx).filter(k => this.sfx[k]).length > 0 ? this.sfx : undefined,
        sfx_volume: this.sfx_volume,
        audio_enabled: this.audio_enabled,
        transitions: this.transitions,
        export: this.export,
        clips: this.clips.map(c => ({
          start: c.start,
          end: c.end,
          kill_type: c.kill_type || undefined,
          label: c.label || undefined,
          sfx_offset: c.sfx_offset != null ? c.sfx_offset : undefined,
          bgm: c.bgm || undefined,
        })),
        temp_dir: this.temp_dir || undefined,
      }
      return yaml.dump(obj, { flowLevel: -1, lineWidth: 120 })
    },

    videoSrc() {
      if (!this.source) return ''
      return `/api/video/stream/${encodeURIComponent(this.source)}`
    },
  },

  actions: {
    addClip() {
      this.clips.push(emptyClip())
    },

    removeClip(index) {
      if (this.clips.length > 1) {
        this.clips.splice(index, 1)
      }
    },

    setClipTime(index, side, value) {
      if (index >= 0 && index < this.clips.length) {
        const clip = this.clips[index]
        if (side === 'start') {
          clip.start = Math.max(0, Math.min(value, clip.end - 0.1))
        } else {
          clip.end = Math.max(clip.start + 0.1, value)
        }
      }
    },

    loadFromYaml(yamlText) {
      const obj = yaml.load(yamlText)
      if (!obj) return
      this.source = obj.source || ''
      this.output = obj.output || 'highlight_output.mp4'
      this.bgm = obj.bgm || ''
      this.bgm_volume = obj.bgm_volume ?? 0.3
      if (obj.sfx) {
        this.sfx = { ...defaultSfx, ...obj.sfx }
      }
      this.sfx_volume = obj.sfx_volume ?? 0.85
      this.audio_enabled = obj.audio_enabled ?? true
      if (obj.transitions) {
        this.transitions = { ...defaultTransitions, ...obj.transitions }
      }
      if (obj.export) {
        this.export = { ...defaultExport, ...obj.export }
      }
      this.clips = (obj.clips || []).map(c => ({
        start: c.start ?? 0,
        end: c.end ?? 5,
        kill_type: c.kill_type || '',
        label: c.label || '',
        sfx_offset: c.sfx_offset ?? null,
        bgm: c.bgm || '',
      }))
      if (this.clips.length === 0) {
        this.clips = [emptyClip()]
      }
      this.temp_dir = obj.temp_dir || ''
    },

    addPipelineMessage(msg) {
      this.pipelineMessages.push(msg)
    },
  },
})
