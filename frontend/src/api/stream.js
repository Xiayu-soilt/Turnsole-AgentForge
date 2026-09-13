const BASE_URL = 'http://localhost:8000'

export function streamChat({ endpoint, payload, onChunk, onDone, onError, onMeta }) {
  const controller = new AbortController()

  fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(localStorage.getItem('token')
        ? { Authorization: `Bearer ${localStorage.getItem('token')}` }
        : {}),
    },
    body: JSON.stringify(payload),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        let detail = `HTTP ${response.status}`
        try {
          const data = await response.json()
          detail = data.detail || detail
        } catch {
          /* ignore */
        }
        throw new Error(detail)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const blocks = buffer.split('\n\n')
        buffer = blocks.pop() || ''

        for (const block of blocks) {
          const lines = block.split('\n')
          let event = ''
          let data = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) event = line.slice(7).trim()
            else if (line.startsWith('data: ')) data += line.slice(6)
          }
          if (!event || !data) continue
          let parsed
          try {
            parsed = JSON.parse(data)
          } catch {
            continue
          }
          if (event === 'chunk' && onChunk) onChunk(parsed)
          else if (event === 'done' && onDone) onDone(parsed)
          else if (event === 'meta' && onMeta) onMeta(parsed)
          else if (event === 'error' && onError) onError(parsed)
        }
      }
      if (buffer.trim()) {
        const lines = buffer.split('\n')
        let event = ''
        let data = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) event = line.slice(7).trim()
          else if (line.startsWith('data: ')) data += line.slice(6)
        }
        if (event && data) {
          try {
            const parsed = JSON.parse(data)
            if (event === 'done' && onDone) onDone(parsed)
            else if (event === 'chunk' && onChunk) onChunk(parsed)
          } catch {
            /* ignore */
          }
        }
      }
    })
    .catch((err) => {
      if (err.name === 'AbortError') return
      if (onError) onError({ message: err.message || '网络错误' })
    })

  return () => controller.abort()
}
