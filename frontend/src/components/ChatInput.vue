<template>
  <div class="input-area">
    <div class="input-wrapper">
      <el-button class="tool-btn" @click="$emit('upload')" :icon="null" circle title="上传图片">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
      </el-button>
      <el-input
        v-model="text"
        type="textarea"
        placeholder=" 输入问题…"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :disabled="isStreaming"
        class="chat-textarea"
        @keydown.enter.exact.prevent="$emit('send')"
        :resize="'none'"
      />
      <el-button
        class="send-btn"
        :type="text.trim() ? 'primary' : 'default'"
        :disabled="!text.trim() || isStreaming"
        @click="$emit('send')"
        circle
        title="发送"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ modelValue: String, isStreaming: Boolean })
const emit = defineEmits(['update:modelValue', 'send', 'upload'])
const text = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v)
})
</script>

<style scoped>
.chat-textarea :deep(.el-textarea__inner) {
  padding-left: 14px !important;
}
</style>
