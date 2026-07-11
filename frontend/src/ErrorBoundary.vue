 <template>
   <div v-if="hasError" class="error-boundary">
     <div class="error-icon">
       <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
         <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
       </svg>
     </div>
     <h2>页面出现异常</h2>
     <p>{{ errorMessage }}</p>
     <button @click="recover">重新加载</button>
   </div>
   <slot v-else />
 </template>
 
 <script setup>
 import { ref, onErrorCaptured } from 'vue'
 
 const hasError = ref(false)
 const errorMessage = ref('')
 
 onErrorCaptured((err) => {
   hasError.value = true
   errorMessage.value = err.message || '未知错误'
   console.error('[ErrorBoundary]', err)
   return false
 })
 
 function recover() {
   hasError.value = false
   errorMessage.value = ''
   window.location.reload()
 }
 </script>
 
 <style scoped>
 .error-boundary {
   display: flex; flex-direction: column; align-items: center; justify-content: center;
   min-height: 100vh; padding: 40px; text-align: center; color: #6b7280;
 }
 .error-icon { color: #ef4444; margin-bottom: 12px; }
 h2 { font-size: 18px; color: #1a1d23; margin-bottom: 8px; }
 p { font-size: 13px; margin-bottom: 20px; }
 button {
   padding: 10px 24px; background: #2b7a4b; color: #fff; border: none;
   border-radius: 8px; font-size: 14px; cursor: pointer;
 }
 button:hover { background: #236a3f; }
 </style>
