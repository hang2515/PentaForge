export async function getVideoInfo(path) {
  const res = await fetch(`/api/video/info?path=${encodeURIComponent(path)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to get video info')
  }
  return res.json()
}

export async function parseYaml(yamlText) {
  const res = await fetch('/api/config/parse', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ yaml_text: yamlText }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to parse YAML')
  }
  return res.json()
}

export async function saveConfig(config, outputPath) {
  const res = await fetch('/api/config/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config, output_path: outputPath }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to save config')
  }
  return res.json()
}

export async function saveConfigYaml(yamlText, outputPath) {
  const res = await fetch('/api/config/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ yaml_text: yamlText, output_path: outputPath }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to save config')
  }
  return res.json()
}

export async function loadConfig(path) {
  const res = await fetch(`/api/config/load?path=${encodeURIComponent(path)}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to load config')
  }
  return res.json()
}

export async function runPipeline(config) {
  const res = await fetch('/api/pipeline/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to start pipeline')
  }
  return res.json()
}

export async function detectCandidateClips(payload) {
  const res = await fetch('/api/detector/candidates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to generate detector candidates')
  }
  return res.json()
}

export async function detectVideoClips(payload) {
  const res = await fetch('/api/detector/video', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to run video OCR detection')
  }
  return res.json()
}

export async function exportPentaKill(payload) {
  const res = await fetch('/api/detector/penta-export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Failed to export penta-kill clips')
  }
  return res.json()
}

export async function openFileDialog(title, filetypes, initialdir) {
  const res = await fetch('/api/file-dialog', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, filetypes, initialdir }),
  })
  if (!res.ok) {
    throw new Error('Failed to open file dialog')
  }
  return res.json()
}

export async function saveFileDialog(title, filename, initialdir, filetypes, defaultextension) {
  const res = await fetch('/api/save-dialog', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, filename, initialdir, filetypes, defaultextension }),
  })
  if (!res.ok) {
    throw new Error('Failed to open save dialog')
  }
  return res.json()
}

export async function getWorkspace() {
  const res = await fetch('/api/workspace')
  if (!res.ok) {
    throw new Error('Failed to get workspace info')
  }
  return res.json()
}

export function connectProgress(jobId, onMessage, onClose, onError) {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${location.host}/ws/progress/${jobId}`)
  ws.onmessage = (e) => onMessage(JSON.parse(e.data))
  ws.onclose = onClose
  ws.onerror = onError
  return ws
}
