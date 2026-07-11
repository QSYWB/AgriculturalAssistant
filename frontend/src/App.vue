<template>
  <ErrorBoundary>
    <nav class="app-nav">
      <router-link to="/" class="nav-logo">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
        </svg>
        <span class="nav-title">农智助手</span>
      </router-link>

    </nav>
    <router-view class="app-content" />
    <LoginDialog :visible="showLogin" @close="showLogin = false" @done="onLoginDone" />
  </ErrorBoundary>
</template>

<script setup>
import { useAuth } from './composables/useAuth.js'
import ErrorBoundary from './ErrorBoundary.vue'
import LoginDialog from './components/LoginDialog.vue'

const { showLogin } = useAuth()


function onLoginDone() { window.location.reload() }
</script>

<style scoped>
.app-nav {
  display: flex; align-items: center; justify-content: space-between;
  height: 48px; padding: 0 18px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid #e5e7eb;
  position: sticky; top: 0; z-index: 100;
}
.nav-logo {
  display: flex; align-items: center; gap: 8px;
  text-decoration: none; color: #15803d;
}
.nav-logo svg { flex-shrink: 0; }
.nav-title { font-weight: 700; font-size: 15px; letter-spacing: -0.01em; }
.nav-login:hover { box-shadow: 0 2px 8px rgba(22,163,74,0.3); transform: translateY(-1px); }
.nav-logout:hover { background: #fef2f2; color: #ef4444; border-color: #fecaca; }
.app-content { height: calc(100vh - 48px); }
</style>



