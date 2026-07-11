<template>
  <div class="app-layout" @mousemove="onMouseMove" @mouseleave="stopPeek">
    

    <div class="sidebar-wrapper" :class="{ collapsed: !pinned, peeking: isPeeking }" @mouseenter="cancelRetract" @mouseleave="onSidebarLeave">
      <AiSidebar
        :pinned="pinned"
        :sessions="sessions"
        :current-id="currentSessionId"
        :is-authenticated="isAuthenticated"
        :user="user"
        @new="newSession"
        @switch="switchSession"
        @open-diagnose="showUpload = true"
        @open-knowledge="showKnowledge = true"
        @toggle-pin="togglePin"
      />
    </div>

    <div v-if="!pinned && !isPeeking" class="sidebar-peek-trigger" @mouseenter="startPeek" />

    <main class="main-area">
      <div class="conversation-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span class="conv-title-text">{{ currentTitle }}</span>
      </div>
      <ChatMessages
        :messages="messages"
        :is-streaming="isStreaming"
        :is-connecting="isConnecting"
        :loading-sessions="loadingSessions"
        :render-content="renderContent"
        @send-quick="sendQuick"
        @retry="retryLast"
      />
      <ChatInput
        v-model="inputText"
        :is-streaming="isStreaming"
        @send="sendMessage"
        @upload="showUpload = true"
      />
    </main>

    <DiagnoseModal v-if="showUpload" @close="showUpload = false" />
    <LoginDialog :visible="showLogin" @close="closeLogin" @done="closeLogin" />

    <el-dialog v-model="showKnowledge" title="知识库管理" width="460px" destroy-on-close @close="showKnowledge = false">
      <KnowledgeManager @close="showKnowledge = false" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useAuth } from '../composables/useAuth.js'
import { useChat } from '../composables/useChat.js'
import AiSidebar from '../components/AiSidebar.vue'
import ChatMessages from '../components/ChatMessages.vue'
import ChatInput from '../components/ChatInput.vue'
import DiagnoseModal from '../components/DiagnoseModal.vue'
import LoginDialog from '../components/LoginDialog.vue'
import KnowledgeManager from '../components/KnowledgeManager.vue'

const { isAuthenticated, user, showLogin, closeLogin } = useAuth()

const {
  sessions, currentSessionId, messages, inputText, isStreaming, isConnecting,
  loadSessions, switchSession, newSession,
  sendMessage, renderContent,
} = useChat()

const showUpload = ref(false)
const loadingSessions = ref(false)
const showKnowledge = ref(false)
const pinned = ref(true)
const isPeeking = ref(false)
let peekTimer = null

const currentTitle = computed(() => {
  if (!currentSessionId.value) return '新对话'
  const session = sessions.value.find(s => s.session_id === currentSessionId.value)
  return session?.title || '新对话'
})

function sendQuick(text) {
  sendMessage(text)
}

function retryLast() {
  const lastUser = [...messages.value].reverse().find(m => m.role === "user")
  if (lastUser) sendMessage(lastUser.content)
}

function togglePin() {
  pinned.value = !pinned.value
  if (pinned.value) isPeeking.value = false
}

function startPeek() {
  if (!pinned.value) {
    isPeeking.value = true
    if (peekTimer) { clearTimeout(peekTimer); peekTimer = null }
  }
}

function cancelRetract() {
  if (peekTimer) { clearTimeout(peekTimer); peekTimer = null }
}

function stopPeek() {
  if (!pinned.value) {
    if (peekTimer) clearTimeout(peekTimer)
    peekTimer = setTimeout(() => { isPeeking.value = false }, 1200)
  }
}

function onSidebarLeave() { stopPeek() }

function onMouseMove(e) {
  if (pinned.value || isPeeking.value) return
  if (e.clientX < 8) startPeek()
}

onMounted(() => {
  if (isAuthenticated.value) loadSessions()
})

watch(isAuthenticated, (val) => {
  if (val) loadSessions()
  else {
    sessions.value = []
    currentSessionId.value = ''
    messages.value = []
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: calc(100vh - 48px);
  overflow: hidden;
}

.sidebar-wrapper {
  width: 260px;
  min-width: 260px;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  border-right: 1px solid #e5e7eb;
  transition: width 0.25s ease, min-width 0.25s ease;
}
.sidebar-wrapper.collapsed:not(.peeking) {
  width: 0;
  min-width: 0;
  border-right: none;
}

.sidebar-peek-trigger {
  position: fixed;
  left: 0; top: 0;
  width: 8px; height: 100%;
  z-index: 20;
  cursor: default;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.conversation-title {
  flex-shrink: 0;
  display: flex; align-items: center; gap: 6px;
  padding: 6px 24px;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
  color: #6b7280;
  font-size: 13px; font-weight: 500;
}
.conv-title-text {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}


@media (max-width: 768px) {
  .sidebar-overlay { display: block; position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 20; }
  .sidebar-wrapper { position: fixed; left: 0; top: 0; z-index: 30; transition: transform 0.25s; }
  .sidebar-wrapper.collapsed:not(.peeking) { transform: translateX(-100%); width: 260px; min-width: 260px; }
  .sidebar-peek-trigger { display: none; }
}
</style>