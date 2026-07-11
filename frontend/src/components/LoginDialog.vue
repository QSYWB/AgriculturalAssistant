<template>
  <Teleport to="body">
    <Transition name="ld-bg" appear>
      <div v-if="visible" class="ld-overlay" @click.self="$emit('close')">
        <Transition name="ld-box" appear>
          <div v-if="visible" class="ld-card">
            <!-- 关闭按钮 -->
            <button class="ld-close" @click="$emit('close')" aria-label="关闭">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>

            <!-- Logo -->
            <div class="ld-logo">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <h2 class="ld-title">农智助手</h2>
            <p class="ld-sub">农业知识问答智能平台</p>

            <!-- 模式切换 -->
            <div class="ld-tabs">
              <button :class="['ld-tab', { active: mode === 'login' }]" @click="switchMode('login')">登录</button>
              <button :class="['ld-tab', { active: mode === 'register' }]" @click="switchMode('register')">注册</button>
            </div>

            <!-- 表单 -->
            <div class="ld-form">
              <Transition name="ld-shake" mode="out-in">
                <p v-if="error" class="ld-err" :key="error">{{ error }}</p>
              </Transition>

              <!-- Avatar selection (register only) -->
              <div v-if="mode === 'register'" class="ld-field">
                <label>选择头像</label>
                <div class="ld-avatar-grid">
                  <button v-for="c in avatarColors" :key="c" type="button" class="ld-avatar-opt" :class="{ active: selectedAvatar === c }" :style="{ background: c }" @click="selectedAvatar = c">
                    <svg v-if="selectedAvatar === c" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  </button>
                  <!-- Upload custom image -->
                  <button type="button" class="ld-avatar-upload" :class="{ active: isUploadAvatar }" :style="isUploadAvatar ? { background: 'url(' + selectedAvatar + ') center/cover no-repeat' } : {}" @click="fileInput?.click()">
                    <svg v-if="!isUploadAvatar" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  </button>
                  <input ref="fileInput" type="file" accept="image/*" class="ld-file-input" @change="handleFileUpload" />
                </div>
              </div>

              <!-- Nickname (register only) -->
              <div v-if="mode === 'register'" class="ld-field">
                <label>昵称</label>
                <div class="ld-input-wrap" :class="{ focus: focusNname }">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                  <input v-model="nickname" type="text" placeholder="设置昵称（选填）" maxlength="50" @focus="focusNname = true" @blur="focusNname = false" />
                </div>
              </div>

              <div class="ld-field">
                <label>用户名</label>
                <div class="ld-input-wrap" :class="{ focus: focusUser }">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  <input v-model="username" type="text" placeholder="输入用户名" minlength="2" @focus="focusUser = true" @blur="focusUser = false" @keydown.enter="submit" />
                </div>
              </div>

              <div class="ld-field">
                <label>密码</label>
                <div class="ld-input-wrap" :class="{ focus: focusPass }">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  <input v-model="password" type="password" placeholder="输入密码（至少6位）" minlength="6" @focus="focusPass = true" @blur="focusPass = false" @keydown.enter="submit" />
                </div>
              </div>

              <button class="ld-submit" :class="{ loading }" :disabled="loading || !username || !password" @click="submit">
                <span v-if="!loading">{{ mode === 'login' ? '登录' : '注册并登录' }}</span>
                <span v-else class="ld-spin"></span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'done'])
const { register, login } = useAuth()

const mode = ref('login')
const username = ref('')
const password = ref('')
const nickname = ref('')
const selectedAvatar = ref('')
const loading = ref(false)
const error = ref('')
const focusUser = ref(false)
const focusPass = ref(false)
const focusNname = ref(false)
const avatarColors = ['#16a34a','#2563eb','#d97706','#dc2626','#7c3aed','#0891b2','#db2777','#ca8a04']
const fileInput = ref(null)
const isUploadAvatar = ref(false)

watch(() => props.visible, (val) => {
  if (val) {
    mode.value = 'login'
    username.value = ''
    password.value = ''
    nickname.value = ''
    selectedAvatar.value = ''
    isUploadAvatar.value = false
    error.value = ''
  }
})

function switchMode(m) {
  mode.value = m
  nickname.value = ''
  selectedAvatar.value = ''
  isUploadAvatar.value = false
  error.value = ''
}

function handleFileUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) return
  if (file.size > 500 * 1024) { error.value = '图片不能超过 500KB'; return }
  const reader = new FileReader()
  reader.onload = (ev) => {
    selectedAvatar.value = ev.target.result
    isUploadAvatar.value = true
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}

async function submit() {
  error.value = ''
  if (!username.value || !password.value) return
  loading.value = true
  try {
    if (mode.value === 'login') {
      await login(username.value, password.value)
    } else {
      await register(username.value, password.value, nickname.value, selectedAvatar.value)
    }
    emit('done')
    emit('close')
  } catch (e) {
    error.value = e.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 背景遮罩 */
.ld-overlay {
  position: fixed; inset: 0;
  z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

/* 卡片 */
.ld-card {
  position: relative;
  width: 92%; max-width: 380px;
  background: #fff;
  border-radius: 20px;
  padding: 36px 32px 32px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.04);
  text-align: center;
}

.ld-close {
  position: absolute; top: 14px; right: 14px;
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border: none; border-radius: 8px;
  background: transparent; color: #9ca3af;
  cursor: pointer; transition: all 0.15s;
}
.ld-close:hover { background: #f3f4f6; color: #374151; }

.ld-logo { color: #16a34a; margin-bottom: 10px; }
.ld-title { font-size: 20px; font-weight: 700; color: #111827; margin: 0 0 4px; }
.ld-sub { font-size: 12px; color: #9ca3af; margin: 0 0 20px; }

/* 切换标签 */
.ld-tabs {
  display: flex; gap: 2px;
  background: #f3f4f6; border-radius: 10px; padding: 3px;
  margin-bottom: 20px;
}
.ld-tab {
  flex: 1; padding: 8px 0; border: none; border-radius: 8px;
  background: transparent; color: #6b7280;
  font: inherit; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.ld-tab.active { background: #fff; color: #16a34a; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }

/* 表单 */
.ld-form { display: flex; flex-direction: column; gap: 14px; }
.ld-field { text-align: left; }
.ld-field label { display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 5px; }
.ld-input-wrap {
  display: flex; align-items: center; gap: 8px;
  padding: 0 12px; height: 42px;
  border: 1.5px solid #e5e7eb; border-radius: 10px;
  background: #fafafa;
  transition: all 0.2s;
}
.ld-input-wrap.focus { border-color: #16a34a; background: #fff; box-shadow: 0 0 0 3px rgba(22,163,74,0.08); }
.ld-input-wrap svg { color: #9ca3af; flex-shrink: 0; transition: color 0.2s; }
.ld-input-wrap.focus svg { color: #16a34a; }
.ld-input-wrap input {
  flex: 1; border: none; background: none; outline: none;
  font: inherit; font-size: 14px; color: #111827;
}
.ld-input-wrap input::placeholder { color: #c4c7cc; }

.ld-err {
  margin: 0; padding: 8px 12px;
  background: #fef2f2; border-radius: 8px;
  font-size: 12px; color: #ef4444;
  text-align: center;
}

/* Avatar grid */
.ld-avatar-grid {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: 4px 0;
}
.ld-avatar-opt {
  width: 36px; height: 36px; border-radius: 50%;
  border: 3px solid transparent; cursor: pointer;
  transition: all 0.15s; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.ld-avatar-opt:hover { transform: scale(1.1); }
.ld-avatar-opt.active { border-color: #111827; transform: scale(1.1); box-shadow: 0 0 0 2px #fff, 0 0 0 4px #111827; }

.ld-avatar-upload {
  width: 36px; height: 36px; border-radius: 50%;
  border: 2px dashed #d1d5db; cursor: pointer;
  transition: all 0.15s; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: #fafafa;
}
.ld-avatar-upload:hover { border-color: #16a34a; background: #f0fdf4; }
.ld-avatar-upload:hover svg { stroke: #16a34a; }
.ld-avatar-upload.active {
  border-color: #111827; border-style: solid;
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px #111827;
  background: transparent;
}
.ld-file-input { display: none; }

.ld-submit {
  position: relative;
  width: 100%; height: 42px; padding: 0;
  border: none; border-radius: 10px;
  background: linear-gradient(135deg, #16a34a, #15803d);
  color: #fff; font: inherit; font-size: 14px; font-weight: 600;
  cursor: pointer; overflow: hidden;
  transition: all 0.2s;
}
.ld-submit:hover:not(:disabled) { box-shadow: 0 4px 12px rgba(22,163,74,0.3); transform: translateY(-1px); }
.ld-submit:active:not(:disabled) { transform: translateY(0); }
.ld-submit:disabled { opacity: 0.5; cursor: default; }

.ld-spin {
  display: inline-block; width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff;
  border-radius: 50%; animation: ld-spin 0.6s linear infinite;
}
@keyframes ld-spin { to { transform: rotate(360deg); } }

/* ===== Vue Transitions ===== */
.ld-bg-enter-active, .ld-bg-leave-active { transition: opacity 0.25s ease; }
.ld-bg-enter-from, .ld-bg-leave-to { opacity: 0; }

.ld-box-enter-active { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.ld-box-leave-active { transition: all 0.2s ease; }
.ld-box-enter-from { opacity: 0; transform: scale(0.9) translateY(16px); }
.ld-box-leave-to { opacity: 0; transform: scale(0.95) translateY(8px); }

.ld-shake-enter-active { animation: ld-shake 0.3s ease; }
.ld-shake-leave-active { transition: opacity 0.15s; }
.ld-shake-enter-from, .ld-shake-leave-to { opacity: 0; }
@keyframes ld-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}
</style>
