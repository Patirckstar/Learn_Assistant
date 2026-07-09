import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/knowledge',
    },
    {
      path: '/knowledge',
      name: 'Knowledge',
      component: () => import('../views/Knowledge/index.vue'),
    },
    {
      path: '/course',
      name: 'Course',
      component: () => import('../views/Course/index.vue'),
    },
    {
      path: '/quiz',
      name: 'Quiz',
      component: () => import('../views/Quiz/index.vue'),
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard/index.vue'),
    },
    {
      path: '/wrongbook',
      name: 'WrongBook',
      component: () => import('../views/WrongBook/index.vue'),
    },
  ],
})

export default router
