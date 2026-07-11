<template>
  <el-scrollbar ref="container" class="chat-messages" view-class="chat-scroll-view">
    <div v-if="!messages.length" class="welcome">
      <div class="welcome-icon">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <h2>农智助手</h2>
      <p class="welcome-sub">农业知识问答 · 作物病害诊断</p>
      <div class="welcome-hints">
        <el-tag v-for="(h, i) in hints" :key="i" class="hint-tag" effect="plain" color="#f0fdf4" @click="$emit('sendQuick', h)">{{ h }}</el-tag>
      </div>
    </div>
    <div v-if="loadingSessions" class="skeleton-area">
      <div v-for="n in 5" :key="n" class="skeleton-row" :class="n % 2 === 0 ? 'skeleton-user' : 'skeleton-assistant'">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-lines">
          <div class="skeleton-line" :style="'width:' + (50 + n * 8) + '%'"></div>
          <div class="skeleton-line" :style="'width:' + (30 + n * 10) + '%'"></div>
        </div>
      </div>
    </div>
    <div v-for="(msg, idx) in messages" :key="idx" class="message" :class="msg.role">
      <div class="avatar" :class="msg.role">
        <svg v-if="msg.role === 'assistant'" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div class="bubble" @mouseenter="hoveredIdx = idx" @mouseleave="hoveredIdx = -1">
        <div class="msg-text" v-html="renderContent(msg.content)"></div>
        <div v-if="isConnecting && idx === messages.length - 1 && msg.role === 'assistant' && !msg.content" class="connecting-dots">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
        <span v-else-if="isStreaming && idx === messages.length - 1 && msg.role === 'assistant' && msg.content" class="cursor"></span>
        <div v-if="hoveredIdx === idx && msg.content" class="msg-actions">
          <button class="msg-action-btn" title="复制" @click.stop="copyMessage(msg.content)">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
          </button>
          <button v-if="msg.role === 'assistant' && idx === messages.length - 1 && !isStreaming" class="msg-action-btn" title="重新生成" @click.stop="$emit('retry')">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
          </button>
        </div>
      </div>
    </div>
  </el-scrollbar>
</template>

<script setup>
import { ref, watch, nextTick } from "vue"

const props = defineProps({
  messages: Array,
  isStreaming: Boolean,
  isConnecting: Boolean,
  loadingSessions: Boolean,
  renderContent: Function
})
const emit = defineEmits(["sendQuick", "retry"])
const container = ref(null)
const hoveredIdx = ref(-1)
const hints = ["玉米锈病怎么防治？", "水稻什么时候施肥最好？", "大葱施肥的注意事项"]

watch(() => props.messages.length + (props.isStreaming ? 1 : 0), () => {
  nextTick(() => {
    if (container.value) {
      const wrap = container.value.wrapRef
      if (wrap) {
        const isNearBottom = wrap.scrollHeight - wrap.scrollTop - wrap.clientHeight < 150
        if (isNearBottom) wrap.scrollTop = wrap.scrollHeight
      }
    }
  })
})

function copyMessage(text) {
  navigator.clipboard.writeText(text).catch(() => {})
}
</script>

<style scoped>
.chat-messages { flex: 1; overflow-y: auto; padding: 4px 0; }
.skeleton-area { padding: 20px 24px; }
.skeleton-row { display: flex; gap: 12px; margin-bottom: 18px; max-width: 780px; margin-left: auto; margin-right: auto; }
.skeleton-row.skeleton-user { flex-direction: row-reverse; }
.skeleton-avatar { width: 34px; height: 34px; border-radius: 50%; background: #e5e7eb; flex-shrink: 0; animation: skel-pulse 1.5s ease-in-out infinite; }
.skeleton-lines { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 10px 0; }
.skeleton-line { height: 14px; border-radius: 7px; background: #e5e7eb; animation: skel-pulse 1.5s ease-in-out infinite; }
@keyframes skel-pulse { 0%, 100% { opacity: 0.6 } 50% { opacity: 1 } }
.connecting-dots { display: inline-flex; gap: 4px; padding: 8px 0; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e; animation: dot-bounce 1.4s ease-in-out infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce { 0%, 60%, 100% { transform: translateY(0); opacity: 0.4 } 30% { transform: translateY(-6px); opacity: 1 } }
.msg-actions { display: flex; gap: 2px; margin-top: 6px; padding-top: 6px; border-top: 1px solid #e5e7eb; }
.msg-action-btn { display: flex; align-items: center; justify-content: center; width: 28px; height: 28px; border: none; border-radius: 6px; background: transparent; color: #9ca3af; cursor: pointer; transition: all 0.15s; }
.msg-action-btn:hover { background: #e5e7eb; color: #374151; }
</style>
