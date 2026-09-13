import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/square',
    name: 'square',
    component: () => import('../views/SquareView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue') },
      { path: 'knowledge', name: 'knowledge', component: () => import('../views/KnowledgeView.vue') },
      { path: 'bots', name: 'bots', component: () => import('../views/BotListView.vue') },
      { path: 'bots/:id/edit', name: 'bot-edit', component: () => import('../views/BotEditView.vue') },
      { path: 'audit', name: 'audit', component: () => import('../views/AuditView.vue') },
    ],
  },
  {
    path: '/chat/:token',
    name: 'public-chat',
    component: () => import('../views/PublicChatView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  if (to.meta.public) return true
  const token = localStorage.getItem('token')
  if (!token && to.name !== 'login') {
    return { name: 'login' }
  }
  return true
})

export default router
