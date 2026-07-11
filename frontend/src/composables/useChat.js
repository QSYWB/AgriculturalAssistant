import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import { useAuth } from './useAuth.js'

const API = '/api/chat'

export function useChat() {
  const sessions = ref([])
  const currentSessionId = ref('')
  const messages = ref([])
  const inputText = ref('')
  const isStreaming = ref(false)
  const isConnecting = ref(false)

  function getHeaders(extra = {}) {
    const auth = useAuth()
    return { 'Content-Type': 'application/json', ...auth.authHeader(), ...extra }
  }

  async function handleResponse(r) {
    if (r.status === 401) {
      useAuth().logout()
      window.location.reload()
      throw new Error('Session expired')
    }
    return r
  }

  async function loadSessions() {
    if (!useAuth().isAuthenticated.value) {
      sessions.value = []
      return
    }
    try {
      const r = await handleResponse(await fetch(API + '/sessions', { headers: getHeaders() }))
      sessions.value = (await r.json()).sessions || []
    } catch {}
  }

  async function switchSession(id) {
    if (isStreaming.value) return
    currentSessionId.value = id
    messages.value = []
    try {
      const r = await handleResponse(await fetch(API + '/sessions/' + id + '/messages', { headers: getHeaders() }))
      if (r.ok) {
        const data = await r.json()
        messages.value = data.messages || []
      }
    } catch {}
  }

  async function newSession() {
    if (isStreaming.value) return
    currentSessionId.value = ''
    messages.value = []
    inputText.value = ''
    await loadSessions()
  }

  async function deleteSession(id) {
    if (isStreaming.value) return
    await handleResponse(await fetch(API + '/sessions/' + id, {
      method: 'DELETE', headers: getHeaders(),
    }))
    if (currentSessionId.value === id) {
      currentSessionId.value = ''
      messages.value = []
    }
    await loadSessions()
  }

  async function sendMessage(text) {
    const query = text?.trim?.() || inputText.value.trim()
    if (!query || isStreaming.value) return

    messages.value.push({ role: 'user', content: query })
    inputText.value = ''
    const msgIdx = messages.value.length
    messages.value.push({ role: 'assistant', content: '' })
    isStreaming.value = true
    isConnecting.value = true
    scrollToBottom()

    try {
      const response = await fetch(API + '/supervisor/stream', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          query,
          session_id: currentSessionId.value || undefined
        })
      })
      await handleResponse(response)
      if (!response.ok) throw new Error('HTTP ' + response.status)
      isConnecting.value = false

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        buffer = buffer.replace(/\r\n/g, '\n')

        let idx
        while ((idx = buffer.indexOf('\n\n')) !== -1) {
          const block = buffer.slice(0, idx)
          buffer = buffer.slice(idx + 2)
          const lines = block.split('\n')
          let eventType = '', eventData = ''
          for (const l of lines) {
            if (l.startsWith('event: ')) eventType = l.slice(7)
            else if (l.startsWith('data: ')) eventData = l.slice(6)
          }
          if (eventType === 'token') {
            messages.value[msgIdx].content += eventData
            messages.value = [...messages.value]
            scrollToBottom()
          } else if (eventType === 'done') {
            currentSessionId.value = eventData
            isStreaming.value = false
            messages.value = [...messages.value]
            await loadSessions()
            scrollToBottom()
          } else if (eventType === 'error') {
            messages.value[msgIdx].content = eventData || '服务异常'
            isStreaming.value = false
            messages.value = [...messages.value]
          }
        }
      }
    } catch (e) {
      if (e.message === 'Session expired') return
      const errText = isConnecting.value ? '连接超时，请检查网络后重试' : '网络异常，请检查连接后重试'
      messages.value[msgIdx].content = errText
      isStreaming.value = false
      isConnecting.value = false
      messages.value = [...messages.value]
    }
  }

  function scrollToBottom() {
    nextTick(() => {
      const el = document.querySelector('.chat-messages')
      if (el) el.scrollTop = el.scrollHeight
    })
  }

  function renderContent(text) {
    if (!text) return ''
    try {
      return marked.parse(text, { breaks: true })
    } catch {
      return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
    }
  }

  return {
    sessions, currentSessionId, messages, inputText, isStreaming, isConnecting,
    loadSessions, switchSession, newSession, deleteSession,
    sendMessage, renderContent
  }
}
