import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('../components/AppLayout.vue'),
      meta: { requiresAuth: true },
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../views/DashboardMobile.vue'),
        },
        {
          path: 'entry',
          name: 'Entry',
          component: () => import('../views/EntryView.vue'),
        },
        {
          path: 'trend',
          name: 'Trend',
          component: () => import('../views/TrendView.vue'),
        },
        {
          path: 'reports',
          name: 'Reports',
          component: () => import('../views/ReportListView.vue'),
        },
        {
          path: 'templates',
          name: 'Templates',
          component: () => import('../views/TemplateView.vue'),
        },
        {
          path: 'patients',
          name: 'Patients',
          component: () => import('../views/PatientView.vue'),
        },
        {
          path: 'medications',
          name: 'Medications',
          component: () => import('../views/MedicationView.vue'),
        },
        {
          path: 'med-timeline',
          name: 'MedTimeline',
          component: () => import('../views/MedicationTimelineView.vue'),
        },
      ],
    },
    {
      path: '/share/:token',
      name: 'Share',
      component: () => import('../views/ShareView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    return '/login'
  }
})

export default router
