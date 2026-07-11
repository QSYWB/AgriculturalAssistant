import { ref, computed } from 'vue'

const STORAGE_KEY = 'agri_assistant_token'
const USER_KEY = 'agri_assistant_user'

const token = ref(localStorage.getItem(STORAGE_KEY) || '')
const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
const showLogin = ref(false)

export function useAuth() {
  function setAuth(t, u) {
    token.value = t
    user.value = u
    localStorage.setItem(STORAGE_KEY, t)
    localStorage.setItem(USER_KEY, JSON.stringify(u))
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function register(username, password, nickname = '', avatar = '') {
    const r = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, nickname, avatar }),
    })
    if (!r.ok) throw new Error((await r.json()).detail || 'Registration failed')
    const data = await r.json()
    setAuth(data.access_token, { user_id: data.user_id, username: data.username, nickname: data.nickname || nickname, avatar: data.avatar || avatar, role: data.role })
    return data
  }

  async function login(username, password) {
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!r.ok) throw new Error((await r.json()).detail || 'Login failed')
    const data = await r.json()
    setAuth(data.access_token, { user_id: data.user_id, username: data.username, nickname: data.nickname || username, avatar: data.avatar || '', role: data.role })
    return data
  }

  function logout() {
    clearAuth()
    location.reload()
  }

  const isAuthenticated = computed(() => !!token.value)

  function openLogin() { showLogin.value = true }
  function closeLogin() { showLogin.value = false }

  function authHeader() {
    return token.value ? { 'Authorization': `Bearer ${token.value}` } : {}
  }

  return {
    token, user,
    showLogin, openLogin, closeLogin,
    isAuthenticated,
    register, login, logout,
    authHeader,
  }
}
