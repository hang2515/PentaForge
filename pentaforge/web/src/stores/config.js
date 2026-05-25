import { defineStore } from 'pinia'
import yaml from 'js-yaml'

const defaultExport = {
  resolution: '1920x1080', fps: 60, codec: 'libx264',
  bitrate: '12M', preset: 'medium',
}

const defaultTransitions = { type: 'fade', duration: 0.6 }

const defaultSfx = {
  double_kill: 'assets/sfx/double_kill.mp3',
  triple_kill: 'assets/sfx/triple_kill.mp3',
  quadra_kill: 'assets/sfx/quadra_kill.mp3',
  penta_kill: 'assets/sfx/penta_kill.mp3',
}

const CLIP_COLORS = [
  '#c8a84e', '#4a90d9', '#e0775c', '#5eaa8e',
  '#b08cd4', '#e0a040', '#5c9ace', '#c4608c',
]

function emptyClip(sourceIdx = 0, videoDuration = 0) {
  const dur = Math.min(5, videoDuration > 0 ? videoDuration / 6 : 5)
  const start = videoDuration > 0 ? Math.max(0, (videoDuration - dur) / 2) : 0
  return { start, end: start + dur, kill_type: '', label: '', sfx_offset: null, bgm: '', sourceIndex: sourceIdx, transition_after: null }
}

function emptySource(path = '') {
  return { path, name: path.split(/[/\\]/).pop() || '', info: null }
}

export const useConfigStore = defineStore('config', {
  state: () => ({
    sources: [],
    activeSourceIndex: 0,
    output: 'highlight_output.mp4',
    bgm: '',
    bgm_volume: 0.3,
    sfx: { ...defaultSfx },
    sfx_volume: 0.85,
    audio_enabled: true,
    transitions: { ...defaultTransitions },
    export: { ...defaultExport },
    temp_dir: '',

    // Runtime
    activeJobId: null,
    pipelineMessages: [],
  }),

  getters: {
    activeSource(state) {
      return state.sources[state.activeSourceIndex] || emptySource()
    },
    sourcePath(state) {
      return state.sources[state.activeSourceIndex]?.path || ''
    },
    videoSrc() {
      const src = this.sourcePath
      if (!src) return ''
      return `/api/video/stream/${encodeURIComponent(src)}`
    },
    videoInfo(state) {
      return state.sources[state.activeSourceIndex]?.info || null
    },
    videoDuration() {
      return this.videoInfo?.duration || 0
    },
    activeClips() {
      const idx = this.activeSourceIndex
      return this.allClips.filter(c => (c.sourceIndex ?? 0) === idx)
    },
    allClips(state) {
      // Flatten: collect clips from source metadata
      const result = []
      for (let i = 0; i < state.sources.length; i++) {
        const src = state.sources[i]
        if (src._clips) {
          for (const c of src._clips) {
            result.push({ ...c, sourceIndex: i })
          }
        }
      }
      return result
    },
    yamlText() {
      const obj = {
        sources: this.sources.map(s => ({ path: s.path, name: s.name })),
        output: this.output,
        bgm: this.bgm || undefined,
        bgm_volume: this.bgm_volume,
        sfx: Object.keys(this.sfx).filter(k => this.sfx[k]).length > 0 ? this.sfx : undefined,
        sfx_volume: this.sfx_volume,
        audio_enabled: this.audio_enabled,
        transitions: this.transitions,
        export: this.export,
        clips: this.allClips.map(c => ({
          source_index: c.sourceIndex,
          start: c.start,
          end: c.end,
          kill_type: c.kill_type || undefined,
          label: c.label || undefined,
          sfx_offset: c.sfx_offset != null ? c.sfx_offset : undefined,
          bgm: c.bgm || undefined,
          transition_after: c.transition_after || undefined,
        })),
        temp_dir: this.temp_dir || undefined,
      }
      return yaml.dump(obj, { flowLevel: -1, lineWidth: 120 })
    },
    clipColors() { return CLIP_COLORS },
  },

  actions: {
    addSource(path) {
      const existing = this.sources.find(s => s.path === path)
      if (existing) {
        this.activeSourceIndex = this.sources.indexOf(existing)
        return
      }
      this.sources.push({ path, name: path.split(/[/\\]/).pop() || path, info: null, _clips: [emptyClip(this.sources.length)] })
      this.activeSourceIndex = this.sources.length - 1
    },

    removeSource(index) {
      if (this.sources.length <= 1) return
      this.sources.splice(index, 1)
      if (this.activeSourceIndex >= this.sources.length) {
        this.activeSourceIndex = this.sources.length - 1
      }
    },

    setActiveSource(index) {
      if (index >= 0 && index < this.sources.length) {
        this.activeSourceIndex = index
      }
    },

    setSourceInfo(path, info) {
      const src = this.sources.find(s => s.path === path)
      if (src) src.info = info
    },

    addClip(sourceIndex) {
      const idx = sourceIndex ?? this.activeSourceIndex
      const src = this.sources[idx]
      if (!src) return
      if (!src._clips) src._clips = []
      const dur = src.info?.duration || 0
      src._clips.push(emptyClip(idx, dur))
    },

    removeClip(sourceIndex, clipIndex) {
      const src = this.sources[sourceIndex ?? this.activeSourceIndex]
      if (!src || !src._clips) return
      if (src._clips.length > 1) {
        src._clips.splice(clipIndex, 1)
      }
    },

    updateClip(sourceIndex, clipIndex, updates) {
      const src = this.sources[sourceIndex ?? this.activeSourceIndex]
      if (!src || !src._clips) return
      const clip = src._clips[clipIndex]
      if (!clip) return
      Object.assign(clip, updates)
    },

    setAllClips(sourceIndex, clips) {
      const idx = sourceIndex ?? this.activeSourceIndex
      const src = this.sources[idx]
      if (!src) return
      src._clips = clips.map(c => ({ ...c, sourceIndex: idx }))
    },

    addPipelineMessage(msg) {
      this.pipelineMessages.push(msg)
    },

    loadFromYaml(yamlText) {
      const obj = yaml.load(yamlText)
      if (!obj) return

      // Sources
      if (obj.sources && Array.isArray(obj.sources)) {
        for (const s of obj.sources) {
          if (s.path) this.addSource(s.path)
        }
      } else if (obj.source) {
        this.addSource(obj.source)
      }

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
      this.temp_dir = obj.temp_dir || ''

      // Clips
      if (obj.clips && Array.isArray(obj.clips)) {
        // Group clips by source_index
        const clipsBySource = {}
        for (const c of obj.clips) {
          const si = c.source_index ?? 0
          if (!clipsBySource[si]) clipsBySource[si] = []
          clipsBySource[si].push({
            start: c.start ?? 0,
            end: c.end ?? 5,
            kill_type: c.kill_type || '',
            label: c.label || '',
            sfx_offset: c.sfx_offset ?? null,
            bgm: c.bgm || '',
            transition_after: c.transition_after ? { ...defaultTransitions, ...c.transition_after } : null,
          })
        }
        for (const [si, clips] of Object.entries(clipsBySource)) {
          const idx = parseInt(si)
          if (idx < this.sources.length) {
            this.sources[idx]._clips = clips
            this.activeSourceIndex = idx
          }
        }
      }
    },
  },
})
