<template>
  <el-dialog v-model="visible" title="作物病害图片诊断" width="520px" :close-on-click-modal="false" @close="$emit('close')" destroy-on-close>
    <div class="diag-body">
      <el-upload ref="uploadRef" drag accept="image/jpeg,image/png" :auto-upload="false" :show-file-list="false" :on-change="onFileChange" class="diag-upload">
        <template v-if="!preview">
          <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" style="color: var(--el-text-color-placeholder); margin-bottom: 8px;">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>
          </svg>
          <p style="margin: 0; font-size: 13px; color: var(--el-text-color-secondary);">点击或拖拽上传图片（JPEG/PNG）</p>
        </template>
        <img v-else :src="preview" class="preview-img" />
      </el-upload>
      <el-input v-model="desc" type="textarea" :rows="2" placeholder="补充描述（如：叶片上有黄色斑点）" style="margin-top: 12px;" />
      <el-progress v-if="uploadProgress > 0" :percentage="uploadProgress" :stroke-width="6" style="margin-top: 12px;"></el-progress>
      <el-button type="primary" :disabled="!preview || loading" :loading="loading" style="width: 100%; margin-top: 12px;" @click="diagnose">
        {{ loading ? '诊断中...' : '开始诊断' }}
      </el-button>
      <div v-if="result" class="diag-result" v-html="formatResult(result)"></div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from "vue"
import { marked } from "marked"
const emit = defineEmits(["close"])
const visible = ref(true)
const preview = ref("")
const desc = ref("")
const loading = ref(false)
const result = ref("")
const uploadProgress = ref(0)

function onFileChange(file) {
  preview.value = URL.createObjectURL(file.raw)
}

async function diagnose() {
  if (!preview.value || loading.value) return
  loading.value = true; result.value = ""; uploadProgress.value = 0
  try {
    const blob = await fetch(preview.value).then(r => r.blob())
    const fd = new FormData()
    fd.append("file", blob, "image." + blob.type.split("/")[1])
    fd.append("description", desc.value)
    const xhr = new XMLHttpRequest()
    uploadProgress.value = 10
    xhr.open("POST", "/api/diagnose")
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) uploadProgress.value = Math.round(10 + (e.loaded / e.total) * 40) }
    const r = await new Promise((resolve, reject) => {
      xhr.onload = () => {
        uploadProgress.value = 100
        resolve(new Response(xhr.responseText, { status: xhr.status, statusText: xhr.statusText }))
      }
      xhr.onerror = () => reject(new Error("Upload failed"))
      xhr.send(fd)
    })
    if (!r.ok) throw new Error()
    const data = await r.json()
    result.value = data.diagnosis + "\n\n【防治方案】\n" + data.treatment
  } catch {
    result.value = "诊断失败，请重试"
  }
  finally { loading.value = false }
}

function formatResult(t) {
  if (!t) return ""
  try {
    return marked.parse(t, { breaks: true })
  } catch {
    return t.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>")
  }
}
</script>

<style scoped>
.diag-body { padding: 4px 0; }
.diag-upload { width: 100%; }
.diag-upload :deep(.el-upload) { width: 100%; }
.preview-img { max-width: 100%; max-height: 280px; border-radius: 8px; object-fit: contain; display: block; margin: 0 auto; }
.diag-result { background: var(--green-50); border-radius: 8px; padding: 14px; margin-top: 12px; font-size: 13px; white-space: pre-wrap; word-break: break-word; line-height: 1.6; border: 1px solid var(--green-100); }
.diag-result :deep(strong) { color: var(--green-800); }
</style>