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

export async function openFileDialog(title, filetypes) {
  const res = await fetch('/api/file-dialog', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, filetypes }),
  })
  if (!res.ok) {
    throw new Error('Failed to open file dialog')
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
