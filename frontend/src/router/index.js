import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    // 触摸终端：全屏独立布局，供不会使用键盘的现场操作员使用
    path: '/touch',
    name: 'touch',
    component: () => import('../views/TouchWorkbench.vue'),
    meta: { title: '过磅工作台-触摸', icon: 'Pointer', perm: 'weigh:create' }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '运营看板', icon: 'DataAnalysis', perm: 'report:view' }
      },
      {
        path: 'workbench',
        name: 'workbench',
        component: () => import('../views/WeighWorkbench.vue'),
        meta: { title: '过磅工作台', icon: 'ScaleToOriginal', perm: 'weigh:create' }
      },
      {
        path: 'pricing',
        name: 'pricing',
        component: () => import('../views/Pricing.vue'),
        meta: { title: '质检核价', icon: 'PriceTag', perm: 'weigh:item' }
      },
      {
        path: 'settlement',
        name: 'settlement',
        component: () => import('../views/Settlement.vue'),
        meta: { title: '结算管理', icon: 'Wallet', perm: 'settle:view' }
      },
      {
        path: 'trips',
        name: 'trips',
        component: () => import('../views/Trips.vue'),
        meta: { title: '磅单记录', icon: 'Tickets', perm: 'weigh:view' }
      },
      {
        path: 'reports',
        name: 'reports',
        component: () => import('../views/Reports.vue'),
        meta: { title: '报表中心', icon: 'TrendCharts', perm: 'report:view' }
      },
      {
        path: 'basic',
        name: 'basic',
        component: () => import('../views/BasicData.vue'),
        meta: { title: '基础数据', icon: 'Box', perm: 'weigh:view' }
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('../views/Users.vue'),
        meta: { title: '用户与权限', icon: 'UserFilled', perm: 'user:manage' }
      }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    const ok = await auth.restore()
    if (!ok) return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isLoggedIn) return { path: '/dashboard' }
  if (to.meta.perm && !auth.hasPerm(to.meta.perm)) {
    return { path: '/dashboard' }
  }
  document.title = to.meta.title ? `${to.meta.title} · 再生资源回收管理系统` : '再生资源回收管理系统'
  return true
})

export default router
