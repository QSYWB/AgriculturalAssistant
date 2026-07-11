<template>
  <aside class="sidebar-root">
    <!-- 搜索框 -->
    <div class="s-area">
      <div class="s-box">
        <svg class="s-ico" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="q" class="s-inp" placeholder="搜索…" />

      </div>
    </div>

    <!-- 新对话按钮 -->
    <div class="btn-area">
      <button class="new-btn" @click="$emit('new')">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        <span>新对话</span>

      </button>
    </div>

    <!-- 分隔线 -->
    <div class="sep"></div>

    <!-- 历史对话 -->
    <div class="h-area">
      <div class="h-title">历史对话</div>
      <div class="h-list">
        <div v-for="s in list" :key="s.session_id" class="h-row" :class="{ on: s.session_id === currentId }" @click="$emit('switch', s.session_id)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="h-txt" :title="s.title">{{ s.title }}</span>
        </div>
        <div v-if="!list.length && q" class="h-empty">无匹配结果</div>
        <div v-if="!list.length && !sessions.length && !q && isAuthenticated" class="h-empty">暂无历史对话</div>
        <div v-if="!list.length && !sessions.length && !q && !isAuthenticated" class="h-empty">登录后查看历史会话</div>
      </div>
    </div>

    <!-- 登录/用户区 -->
    <div class="b-area" :class="{ haspop: isAuthenticated }">
      <template v-if="isAuthenticated">
        <div class="b-card" @click.stop="toggleMenu">
          <div class="b-av" :style="{ background: avatarBg }">{{ showInitial ? name.charAt(0).toUpperCase() : '' }}</div>
          <span class="b-nm">{{ name }}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="['b-chev', { up: showMenu }]"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
        <Transition name="b-up">
          <div v-if="showMenu" class="b-popup" @click.stop>
            <button class="b-popup-item" @click="goSettings">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <span>设置</span>
            </button>
            <button class="b-popup-item b-popup-logout" @click="doLogout">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              <span>退出登录</span>
            </button>
          </div>
        </Transition>
      </template>
      <button v-else class="b-login" @click.stop="openLogin">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
        登录
      </button>
    </div>

    <!-- 折叠按钮 -->
    <button class="collapse-btn" :title="pinned ? '收起侧边栏' : '展开侧边栏'" @click="$emit('toggle-pin')">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline :points="pinned ? '15 18 9 12 15 6' : '9 18 15 12 9 6'" />
      </svg>
    </button>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
const { openLogin } = useAuth()
 
const props = defineProps({
  sessions: { type: Array, default: () => [] },
  currentId: { type: String, default: '' },
  isAuthenticated: { type: Boolean, default: false },
  user: { type: Object, default: null },
  pinned: { type: Boolean, default: true },
})

defineEmits(['new', 'switch', 'toggle-pin'])
const q = ref('')
const showMenu = ref(false)
const router = useRouter()

const name = computed(() => {
  if (props.isAuthenticated && props.user) return props.user.nickname || props.user.username
  return '游客'
})
const showInitial = computed(() => {
  const av = props.user?.avatar
  if (!av) return true
  if (av.startsWith('data:') || av.startsWith('http://') || av.startsWith('https://')) return false
  return true
})
const avatarBg = computed(() => {
  const av = props.user?.avatar
  if (!av) return 'linear-gradient(135deg,#16a34a,#15803d)'
  if (av.startsWith('data:') || av.startsWith('http://') || av.startsWith('https://')) return 'url(' + av + ') center/cover no-repeat'
  return av
})

const list = computed(() => {
  if (!q.value) return props.sessions
  const kw = q.value.toLowerCase()
  return props.sessions.filter(s => s.title.toLowerCase().includes(kw))
})

function toggleMenu() { showMenu.value = !showMenu.value }

function goSettings() {
  showMenu.value = false
  router.push('/settings')
}

function doLogout() {
  showMenu.value = false
  localStorage.removeItem('agri_assistant_token')
  localStorage.removeItem('agri_assistant_user')
  location.reload()
}

function closeMenu(e) { showMenu.value = false }

onMounted(() => document.addEventListener('click', closeMenu))
onUnmounted(() => document.removeEventListener('click', closeMenu))
</script>

<style scoped>
.sidebar-root {
  width: 260px; height: 100%; min-height: 0;
  background: #fff; border-right: 1px solid #e5e7eb;
  display: flex; flex-direction: column;
  overflow: hidden;
  font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.s-area { flex-shrink: 0; padding: 14px 12px 12px; }
.s-box {
  display: flex; align-items: center; gap: 8px;
  background: #f3f4f6; border-radius: 10px;
  padding: 0 10px; height: 38px;
}
.s-ico { color: #9ca3af; flex-shrink: 0; }
.s-inp { flex: 1; border: none; background: none; outline: none; font: inherit; font-size: 13px; color: #111827; min-width: 0; }
.s-inp::placeholder { color: #9ca3af; }
.s-kbd { flex-shrink: 0; font-size: 11px; color: #9ca3af; background: #e5e7eb; padding: 2px 7px; border-radius: 5px; line-height: 1.4; }
.s-kbd.gray { background: #f3f4f6; border: 1px solid #e5e7eb; }

.btn-area { flex-shrink: 0; padding: 0 12px 12px; }
.new-btn {
  display: flex; align-items: center; gap: 8px;
  width: 100%; padding: 0 9px; height: 38px;
  border: 1px solid #e5e7eb; border-radius: 10px;
  background: #fff; color: #111827;
  cursor: pointer; font: inherit; font-size: 13px;
}
.new-btn:hover { background: #f3f4f6; }
.new-btn span:first-of-type { flex: 1; text-align: left; }

.sep { height: 1px; background: #e5e7eb; margin: 0 12px; flex-shrink: 0; }

.h-area {
  flex: 1; min-height: 0;
  display: flex; flex-direction: column; overflow: hidden;
  padding: 8px 12px 0;
}
.h-title { flex-shrink: 0; font-size: 11px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 10px 8px; }
.h-list { flex: 1; overflow-y: auto; min-height: 0; padding-bottom: 4px; }
.h-list::-webkit-scrollbar { width: 4px; }
.h-list::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }
.h-row { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 8px; cursor: pointer; color: #374151; margin-bottom: 1px; }
.h-row:hover { background: #f3f4f6; }
.h-row.on { background: #f0fdf4; }
.h-row.on .h-txt { color: #15803d; font-weight: 500; }
.h-row.on svg { color: #22c55e; }
.h-row svg { color: #9ca3af; flex-shrink: 0; }
.h-txt { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.h-empty { padding: 16px 10px; text-align: center; font-size: 12px; color: #9ca3af; }

.b-area { flex-shrink: 0; border-top: 1px solid #e5e7eb; padding: 10px 12px; }
.b-card { display: flex; align-items: center; gap: 9px; padding: 6px; border-radius: 8px; cursor: pointer; }
.b-card:hover { background: #f3f4f6; }
.b-av { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.b-nm { flex: 1; font-size: 13px; font-weight: 500; color: #111827; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.b-card svg:last-child { flex-shrink: 0; color: #9ca3af; }
.b-login { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; padding: 9px 0; height: 38px; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; color: #374151; cursor: pointer; font: inherit; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.b-login:hover { background: #f3f4f6; border-color: #16a34a; color: #16a34a; }
.b-area.haspop { position: relative; }
.b-popup { position: absolute; bottom: calc(100% + 6px); left: 12px; right: 12px; background: #fff; border-radius: 12px; box-shadow: 0 -2px 16px rgba(0,0,0,0.08), 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e5e7eb; overflow: hidden; z-index: 50; }
.b-popup-item { display: flex; align-items: center; gap: 10px; width: 100%; padding: 12px 16px; border: none; background: transparent; cursor: pointer; font: inherit; font-size: 13px; color: #374151; transition: background 0.1s; }
.b-popup-item:hover { background: #f3f4f6; }
.b-popup-item svg { flex-shrink: 0; color: #6b7280; }
.b-popup-logout { color: #ef4444; border-top: 1px solid #f3f4f6; }
.b-popup-logout svg { color: #ef4444; }
.b-chev { transition: transform 0.2s; }
.b-chev.up { transform: rotate(180deg); }
.b-up-enter-active { transition: all 0.18s ease-out; }
.b-up-leave-active { transition: all 0.12s ease-in; }
.b-up-enter-from { opacity: 0; transform: translateY(8px) scale(0.96); }
.b-up-leave-to { opacity: 0; transform: translateY(4px) scale(0.97); }

/* 折叠按钮 */
.collapse-btn { flex-shrink: 0; width: 100%; height: 18px; display: flex; align-items: center; justify-content: center; border: none; background: transparent; color: #9ca3af; cursor: pointer; transition: color 0.15s; }
.collapse-btn:hover { background: #f3f4f6; color: #374151; }

@media (max-width: 768px) { .sidebar-root { position: fixed; left: 0; top: 0; z-index: 30; } }
</style>
