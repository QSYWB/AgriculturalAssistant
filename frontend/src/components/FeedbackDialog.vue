<template>
  <Teleport to="body">
    <Transition name="fd-bg">
      <div v-if="visible" class="fd-overlay" @click.self="$emit('close')">
        <Transition name="fd-box">
          <div v-if="visible" class="fd-card">
            <button class="fd-close" @click="$emit('close')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
            <h3 class="fd-title">帮助与反馈</h3>

            <div class="fd-tabs">
              <button :class="['fd-tab', { active: tab === 'submit' }]" @click="tab = 'submit'">提交反馈</button>
              <button :class="['fd-tab', { active: tab === 'history' }]" @click="tab = 'history'">反馈历史</button>
            </div>

            <!-- 提交反馈 -->
            <div v-if="tab === 'submit'" class="fd-body">
              <div class="fd-field">
                <label>反馈内容</label>
                <textarea v-model="content" class="fd-textarea" placeholder="请描述您遇到的问题或建议…" rows="4"></textarea>
              </div>

              <div class="fd-img-section">
                <label>截图（可选）</label>
                <div class="fd-img-list">
                  <div v-for="(img, i) in imagePreviews" :key="i" class="fd-img-item">
                    <img :src="img" />
                    <button class="fd-img-del" @click="removeImage(i)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                  </div>
                  <button class="fd-img-add" @click="triggerImgUpload" v-if="imagePreviews.length < 3">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                  </button>
                </div>
                <input ref="imgInput" type="file" accept="image/jpeg,image/png" hidden @change="onImgChange" />
              </div>

              <div v-if="fbMsg" class="fd-msg" :class="{ err: fbErr }">{{ fbMsg }}</div>

              <button class="fd-submit" :disabled="!content.trim() || submitting" @click="submitFeedback">
                <span v-if="!submitting">提交反馈</span>
                <span v-else class="fd-spin"></span>
              </button>
            </div>

            <!-- 反馈历史 -->
            <div v-else class="fd-body">
              <div v-if="loadingHistory" class="fd-loading">加载中…</div>
              <div v-else-if="!historyItems.length" class="fd-empty">暂无反馈记录</div>
              <div v-else class="fd-history">
                <div v-for="item in historyItems" :key="item.id" class="fd-history-item">
                  <p class="fd-history-text">{{ item.content }}</p>
                  <div v-if="item.images?.length" class="fd-history-imgs">
                    <img v-for="(u, i) in item.images" :key="i" :src="u" class="fd-history-img" />
                  </div>
                  <span class="fd-history-date">{{ formatDate(item.created_at) }}</span>
                </div>
              </div>
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
const emit = defineEmits(['close'])
const { authHeader } = useAuth()

const tab = ref('submit')
const content = ref('')
const imageFiles = ref([])
const imagePreviews = ref([])
const imgInput = ref(null)
const submitting = ref(false)
const fbMsg = ref('')
const fbErr = ref(false)
const loadingHistory = ref(false)
const historyItems = ref([])

function triggerImgUpload() { imgInput.value?.click() }
function onImgChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  imageFiles.value.push(f)
  imagePreviews.value.push(URL.createObjectURL(f))
}
function removeImage(i) {
  imageFiles.value.splice(i, 1)
  imagePreviews.value.splice(i, 1)
}

async function submitFeedback() {
  if (!content.value.trim()) return
  submitting.value = true; fbMsg.value = ''
  try {
    // Upload images first
    const imgUrls = []
    for (const f of imageFiles.value) {
      const fd = new FormData()
      fd.append('file', f)
      const r = await fetch('/api/user/feedback/image', { method: 'POST', headers: authHeader(), body: fd })
      if (r.ok) {
        const d = await r.json()
        imgUrls.push(d.url)
      }
    }
    // Submit feedback
    const r = await fetch('/api/user/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify({ content: content.value, images: imgUrls }),
    })
    if (!r.ok) throw new Error((await r.json()).detail || '提交失败')
    fbMsg.value = '反馈已提交，感谢您的意见！'
    fbErr.value = false
    content.value = ''
    imageFiles.value = []
    imagePreviews.value = []
  } catch (e) {
    fbMsg.value = e.message
    fbErr.value = true
  } finally { submitting.value = false }
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const r = await fetch('/api/user/feedback', { headers: authHeader() })
    if (r.ok) {
      const d = await r.json()
      historyItems.value = d.items || []
    }
  } catch {} finally { loadingHistory.value = false }
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

watch(() => props.visible, (val) => { if (val) loadHistory() })
</script>

<style scoped>
.fd-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.3); backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); }
.fd-card { position: relative; width: 92%; max-width: 440px; max-height: 80vh; background: #fff; border-radius: 18px; padding: 28px 24px 24px; box-shadow: 0 12px 40px rgba(0,0,0,0.1); overflow-y: auto; }
.fd-close { position: absolute; top: 14px; right: 14px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 8px; background: transparent; color: #9ca3af; cursor: pointer; }
.fd-close:hover { background: #f3f4f6; color: #374151; }
.fd-title { font-size: 17px; font-weight: 700; color: #111827; margin: 0 0 16px; text-align: center; }
.fd-tabs { display: flex; gap: 2px; background: #f3f4f6; border-radius: 10px; padding: 3px; margin-bottom: 16px; }
.fd-tab { flex: 1; padding: 8px 0; border: none; border-radius: 8px; background: transparent; color: #6b7280; font: inherit; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; }
.fd-tab.active { background: #fff; color: #16a34a; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.fd-body { display: flex; flex-direction: column; gap: 12px; }
.fd-field label, .fd-img-section label { display: block; font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 5px; }
.fd-textarea { width: 100%; padding: 10px 12px; border: 1.5px solid #e5e7eb; border-radius: 10px; font: inherit; font-size: 13px; outline: none; resize: vertical; min-height: 80px; }
.fd-textarea:focus { border-color: #16a34a; }
.fd-img-list { display: flex; gap: 8px; flex-wrap: wrap; }
.fd-img-item { position: relative; width: 72px; height: 72px; border-radius: 8px; overflow: hidden; }
.fd-img-item img { width: 100%; height: 100%; object-fit: cover; }
.fd-img-del { position: absolute; top: 2px; right: 2px; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 4px; background: rgba(0,0,0,0.5); color: #fff; cursor: pointer; padding: 0; }
.fd-img-add { width: 72px; height: 72px; border: 1.5px dashed #e5e7eb; border-radius: 8px; background: transparent; color: #9ca3af; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.fd-img-add:hover { border-color: #16a34a; color: #16a34a; }

.fd-msg { padding: 8px 12px; border-radius: 8px; font-size: 12px; }
.fd-msg.err { background: #fef2f2; color: #ef4444; }
.fd-msg:not(.err) { background: #f0fdf4; color: #16a34a; }

.fd-submit { width: 100%; height: 40px; border: none; border-radius: 10px; background: linear-gradient(135deg,#16a34a,#15803d); color: #fff; font: inherit; font-size: 14px; font-weight: 600; cursor: pointer; }
.fd-submit:hover:not(:disabled) { box-shadow: 0 4px 12px rgba(22,163,74,0.3); }
.fd-submit:disabled { opacity: 0.5; }
.fd-spin { display: inline-block; width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: fds 0.6s linear infinite; }
@keyframes fds { to { transform: rotate(360deg); } }

.fd-loading, .fd-empty { padding: 24px 0; text-align: center; font-size: 13px; color: #9ca3af; }
.fd-history { display: flex; flex-direction: column; gap: 10px; max-height: 300px; overflow-y: auto; }
.fd-history-item { padding: 12px; border-radius: 10px; background: #f9fafb; }
.fd-history-text { font-size: 13px; color: #374151; margin: 0 0 8px; line-height: 1.5; }
.fd-history-imgs { display: flex; gap: 6px; margin-bottom: 6px; }
.fd-history-img { width: 56px; height: 56px; border-radius: 6px; object-fit: cover; }
.fd-history-date { font-size: 11px; color: #9ca3af; }

.fd-bg-enter-active, .fd-bg-leave-active { transition: opacity 0.2s; }
.fd-bg-enter-from, .fd-bg-leave-to { opacity: 0; }
.fd-box-enter-active { transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.fd-box-leave-active { transition: all 0.15s; }
.fd-box-enter-from { opacity: 0; transform: scale(0.92) translateY(12px); }
.fd-box-leave-to { opacity: 0; transform: scale(0.95); }
</style>
