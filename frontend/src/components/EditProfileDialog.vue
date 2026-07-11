<template>
  <Teleport to="body">
    <Transition name="ep-bg">
      <div v-if="visible" class="ep-overlay" @click.self="$emit('close')">
        <Transition name="ep-box">
          <div v-if="visible" class="ep-card">
            <button class="ep-close" @click="$emit('close')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
            <h3 class="ep-title">编辑个人资料</h3>

            <div class="ep-avatar-section">
              <div class="ep-av-preview" @click="triggerAvatarUpload">
                <div v-if="!avatarPreview" class="ep-av-placeholder">{{ nickname?.charAt(0)?.toUpperCase() || '?' }}</div>
                <img v-else :src="avatarPreview" class="ep-av-img" />
                <div class="ep-av-overlay"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg></div>
              </div>
              <p class="ep-av-hint">点击更换头像</p>
            </div>
            <input ref="avatarInput" type="file" accept="image/jpeg,image/png" hidden @change="onAvatarChange" />

            <div class="ep-field">
              <label>用户名（不可修改）</label>
              <div class="ep-disabled-input">{{ username }}</div>
            </div>

            <div class="ep-field">
              <label>用户ID</label>
              <div class="ep-disabled-input mono">{{ userId }}</div>
            </div>

            <div class="ep-field">
              <label>昵称</label>
              <input v-model="nickname" class="ep-input" placeholder="输入昵称" maxlength="50" />
            </div>

            <div v-if="saveMsg" class="ep-msg" :class="{ err: saveErr }">{{ saveMsg }}</div>

            <button class="ep-save" :disabled="saving" @click="saveProfile">
              <span v-if="!saving">保存</span>
              <span v-else class="ep-spin"></span>
            </button>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'saved'])
import { useAuth } from '../composables/useAuth.js'
const { authHeader } = useAuth()

const username = ref('')
const userId = ref('')
const nickname = ref('')
const avatarPreview = ref('')
const avatarFile = ref(null)
const avatarInput = ref(null)
const saving = ref(false)
const saveMsg = ref('')
const saveErr = ref(false)

watch(() => props.visible, async (val) => {
  if (!val) return
  try {
    const headers = { 'Content-Type': 'application/json', ...authHeader(), ...authHeader() }
    const r = await fetch('/api/user/profile', { headers })
    if (r.ok) {
      const d = await r.json()
      username.value = d.username
      userId.value = d.user_id
      nickname.value = d.nickname || d.username
      if (d.avatar) avatarPreview.value = d.avatar
    }
  } catch {}
})

function triggerAvatarUpload() { avatarInput.value?.click() }

function onAvatarChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  avatarFile.value = f
  avatarPreview.value = URL.createObjectURL(f)
}

async function saveProfile() {
  saveMsg.value = ''
  saving.value = true
  try {
    const r = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify({ nickname: nickname.value }),
    })
    if (!r.ok) throw new Error((await r.json()).detail || '保存失败')

    if (avatarFile.value) {
      const fd = new FormData()
      fd.append('file', avatarFile.value)
      const ar = await fetch('/api/user/avatar', { method: 'POST', headers: authHeader(), body: fd })
      if (!ar.ok) throw new Error('头像上传失败')
    }

    saveMsg.value = '保存成功'
    saveErr.value = false
    setTimeout(() => emit('close'), 800)
  } catch (e) {
    saveMsg.value = e.message
    saveErr.value = true
  } finally { saving.value = false }
}
</script>

<style scoped>
.ep-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.3); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); }
.ep-card { position: relative; width: 92%; max-width: 400px; background: #fff; border-radius: 18px; padding: 32px 28px 28px; box-shadow: 0 12px 40px rgba(0,0,0,0.1); text-align: center; }
.ep-close { position: absolute; top: 14px; right: 14px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 8px; background: transparent; color: #9ca3af; cursor: pointer; }
.ep-close:hover { background: #f3f4f6; color: #374151; }
.ep-title { font-size: 17px; font-weight: 700; color: #111827; margin: 0 0 20px; }

.ep-avatar-section { margin-bottom: 20px; }
.ep-av-preview { width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 8px; position: relative; cursor: pointer; overflow: hidden; background: linear-gradient(135deg, #16a34a, #15803d); }
.ep-av-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 24px; font-weight: 700; }
.ep-av-img { width: 100%; height: 100%; object-fit: cover; }
.ep-av-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; color: #fff; opacity: 0; transition: opacity 0.15s; }
.ep-av-preview:hover .ep-av-overlay { opacity: 1; }
.ep-av-hint { font-size: 11px; color: #9ca3af; margin: 0; }

.ep-field { text-align: left; margin-bottom: 14px; }
.ep-field label { display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 5px; }
.ep-input, .ep-disabled-input { width: 100%; padding: 0 12px; height: 40px; border: 1.5px solid #e5e7eb; border-radius: 10px; font: inherit; font-size: 13px; outline: none; transition: border-color 0.15s; }
.ep-input:focus { border-color: #16a34a; }
.ep-disabled-input { background: #f9fafb; color: #6b7280; line-height: 40px; }
.mono { font-family: 'SF Mono', 'JetBrains Mono', monospace; font-size: 12px; }

.ep-msg { padding: 8px 12px; border-radius: 8px; font-size: 12px; margin-bottom: 12px; }
.ep-msg.err { background: #fef2f2; color: #ef4444; }
.ep-msg:not(.err) { background: #f0fdf4; color: #16a34a; }

.ep-save { width: 100%; height: 40px; border: none; border-radius: 10px; background: linear-gradient(135deg,#16a34a,#15803d); color: #fff; font: inherit; font-size: 14px; font-weight: 600; cursor: pointer; }
.ep-save:hover:not(:disabled) { box-shadow: 0 4px 12px rgba(22,163,74,0.3); }
.ep-save:disabled { opacity: 0.5; }
.ep-spin { display: inline-block; width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: lds 0.6s linear infinite; }
@keyframes lds { to { transform: rotate(360deg); } }

.ep-bg-enter-active, .ep-bg-leave-active { transition: opacity 0.2s; }
.ep-bg-enter-from, .ep-bg-leave-to { opacity: 0; }
.ep-box-enter-active { transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.ep-box-leave-active { transition: all 0.15s; }
.ep-box-enter-from { opacity: 0; transform: scale(0.92) translateY(12px); }
.ep-box-leave-to { opacity: 0; transform: scale(0.95); }
</style>
