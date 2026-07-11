import { createRouter, createWebHistory } from 'vue-router'
import ChatLayout from '../pages/ChatLayout.vue'
import SettingsPage from '../pages/SettingsPage.vue'

const routes = [
  {
    path: '/',
    name: 'chat',
    component: ChatLayout,
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsPage,
  },
]

const router = createRouter({
  history: createWebHistory('/chat/'),
  routes,
})

export default router
