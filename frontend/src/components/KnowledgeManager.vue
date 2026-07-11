<template>
  <div class="knowledge-manager">
    <div class="km-header">
      <el-button text size="small" @click="$emit('close')" class="back-btn">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
        返回
      </el-button>
      <h4>知识库管理</h4>
    </div>

    <div class="km-actions">
      <el-button size="small" @click="triggerUpload">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        上传文件
      </el-button>
      <el-button size="small" :disabled="loading" @click="reloadAll">
        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        重新加载
      </el-button>
    </div>

    <el-upload
      ref="uploadRef"
      :show-file-list="false"
      :auto-upload="false"
      accept=".txt,.md,.pdf"
      :on-change="handleUpload"
      style="display: none"
    />

    <div v-if="loading" class="km-loading"><span class="spinner"></span> 处理中…</div>

    <div class="km-files">
      <div v-for="f in files" :key="f.filename" class="km-file">
        <div class="km-file-icon">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
        </div>
        <div class="km-file-info">
          <span class="km-filename" :title="f.filename">{{ f.filename }}</span>
          <span class="km-size">{{ (f.size / 1024).toFixed(1) }} KB</span>
        </div>
        <el-button text size="small" class="km-delete" @click="deleteFile(f.filename)" title="删除文件">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </el-button>
      </div>
      <el-empty v-if="!files.length && !loading" :description="'暂无知识文件'" style="padding: 32px 16px;">
        <template #image>
          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" style="color: var(--el-text-color-placeholder);">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </template>
        <p style="font-size: 12px; color: var(--el-text-color-secondary); margin: 0;">上传 .txt/.md/.pdf 文件以构建知识库</p>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
const emit = defineEmits(['close'])
const API = '/api/chat/knowledge'

const files = ref([])
const loading = ref(false)

async function loadFiles() {
  try {
    const r = await fetch(`${API}/files`, { credentials: 'include' })
    if (r.ok) files.value = (await r.json()).files || []
  } catch {}
}

function triggerUpload() {
  // Use a hidden input since el-upload with manual trigger is complex
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.txt,.md,.pdf'
  input.onchange = (e) => {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }
  input.click()
}

async function handleFile(f) {
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('file', f)
    const r = await fetch(`${API}/upload`, { method: 'POST', body: fd, credentials: 'include' })
    if (!r.ok) throw new Error((await r.json()).detail || '上传失败')
    const data = await r.json()
    ElMessage.success(`上传成功，向量库共 ${data.total_chunks} 个片段`)
    await loadFiles()
  } catch (e) {
    ElMessage.error(`上传失败: ${e.message}`)
  } finally { loading.value = false }
}

function handleUpload(file) {
  handleFile(file.raw)
}

async function deleteFile(name) {
  try {
    await ElMessageBox.confirm(`确认删除 "${name}" ？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }
  loading.value = true
  try {
    const r = await fetch(`${API}/files/${encodeURIComponent(name)}`, { method: 'DELETE', credentials: 'include' })
    if (!r.ok) throw new Error('删除失败')
    const data = await r.json()
    ElMessage.success(`已删除，向量库共 ${data.total_chunks} 个片段`)
    await loadFiles()
  } catch (e) {
    ElMessage.error(`删除失败: ${e.message}`)
  } finally { loading.value = false }
}

async function reloadAll() {
  loading.value = true
  try {
    const r = await fetch(`${API}/reload`, { method: 'POST', credentials: 'include' })
    if (!r.ok) throw new Error('重新加载失败')
    const data = await r.json()
    ElMessage.success(`重新加载完成，向量库共 ${data.total_chunks} 个片段`)
    await loadFiles()
  } catch (e) {
    ElMessage.error(`重新加载失败: ${e.message}`)
  } finally { loading.value = false }
}

onMounted(loadFiles)
</script>

<style scoped>
.knowledge-manager { display: flex; flex-direction: column; height: 100%; overflow: hidden; }
.km-header { padding: 12px 14px 8px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 6px; }
.km-header h4 { font-size: 13px; font-weight: 600; flex: 1; margin: 0; }
.back-btn { color: var(--green-700); }
.km-actions { display: flex; gap: 6px; padding: 10px 12px; flex-wrap: wrap; }
.km-files { flex: 1; overflow-y: auto; padding: 4px 8px; }
.km-file { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border-radius: var(--radius-sm); transition: background 0.1s; }
.km-file:hover { background: var(--green-50); }
.km-file-icon { color: var(--text-muted); flex-shrink: 0; display: flex; }
.km-file-info { flex: 1; min-width: 0; }
.km-filename { display: block; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text); }
.km-size { font-size: 11px; color: var(--text-muted); }
.km-delete { flex-shrink: 0; opacity: 0; transition: opacity 0.15s; }
.km-file:hover .km-delete { opacity: 1; }
.km-delete:hover { color: #ef4444; }
.km-loading { display: flex; align-items: center; gap: 6px; padding: 8px 12px; font-size: 12px; color: var(--text-secondary); }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(0,0,0,0.1); border-top-color: var(--green-600); border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
