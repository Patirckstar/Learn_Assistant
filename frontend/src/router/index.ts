import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login/index.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      redirect: '/knowledge',
      meta: { requiresAuth: true },
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('../views/Knowledge/index.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/course',
      name: 'Course',
      component: () => import('../views/Course/index.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/quiz',
      name: 'Quiz',
      component: () => import('../views/Quiz/index.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard/index.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/wrongbook',
      name: 'WrongBook',
      component: () => import('../views/WrongBook/index.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile/index.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !authStore.isLoggedIn()) {
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn()) {
    next('/knowledge')
  } else {
    next()
  }
})

export default router