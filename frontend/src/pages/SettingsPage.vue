<template>
  <div class="sp-root">
    <div class="sp-card">
      <div class="sp-header">
        <button class="sp-back" @click="$router.push('/')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          返回
        </button>
        <h3>设置</h3>
      </div>

      <div class="sp-items">
        <!-- 编辑个人资料 -->
        <button class="sp-item" @click="showEditProfile = true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          <span class="sp-item-label">编辑个人资料</span>
          <svg class="sp-item-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>

        <!-- 帮助与反馈 -->
        <button class="sp-item" @click="showFeedback = true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
          <span class="sp-item-label">帮助与反馈</span>
          <svg class="sp-item-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>

        <!-- 退出登录 -->
        <button class="sp-item sp-logout" @click="doLogout">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span class="sp-item-label">退出登录</span>
        </button>
      </div>
    </div>
    <EditProfileDialog :visible="showEditProfile" @close="showEditProfile = false" />
    <FeedbackDialog :visible="showFeedback" @close="showFeedback = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import EditProfileDialog from '../components/EditProfileDialog.vue'
import FeedbackDialog from '../components/FeedbackDialog.vue'

const router = useRouter()
const { logout } = useAuth()
const showEditProfile = ref(false)
const showFeedback = ref(false)

function doLogout() {
  logout()
  router.push('/')
}
</script>

<style scoped>
.sp-root {
  height: 100%;
  display: flex; align-items: flex-start; justify-content: center;
  padding: 40px 20px;
  background: var(--bg);
}
.sp-card { width: 100%; max-width: 420px; background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); overflow: hidden; }
.sp-header { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
.sp-back { display: flex; align-items: center; gap: 4px; border: none; background: transparent; color: #16a34a; font: inherit; font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 6px; justify-self: start; }
.sp-back:hover { background: #f0fdf4; }
.sp-header h3 { font-size: 16px; font-weight: 700; color: #111827; margin: 0; text-align: center; grid-column: 2; }
.sp-items { padding: 8px 0; }
.sp-item { display: flex; align-items: center; gap: 12px; width: 100%; padding: 14px 20px; border: none; background: transparent; cursor: pointer; text-align: left; transition: background 0.1s; color: #374151; }
.sp-item:hover { background: #f9fafb; }
.sp-item svg:first-child { color: #6b7280; flex-shrink: 0; }
.sp-item-label { flex: 1; font-size: 14px; }
.sp-item-arrow { color: #d1d5db; flex-shrink: 0; }
.sp-logout { border-top: 1px solid #f3f4f6; color: #ef4444; }
.sp-logout svg:first-child { color: #ef4444; }
</style>
