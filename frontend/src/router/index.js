import { createRouter, createWebHistory } from 'vue-router'
import { currentUser, isAdmin } from '@utils/auth'

// 布局组件
import MainLayout from '@/layouts/MainLayout.vue'

// 懒加载页面组件
const Books = () => import('@/pages/books/App.vue')
const BookDetail = () => import('@/pages/book-detail/App.vue')
const Login = () => import('@/pages/login/App.vue')
const Register = () => import('@/pages/register/App.vue')
const MyBorrows = () => import('@/pages/my-borrows/App.vue')
const AdminBooks = () => import('@/pages/admin-books/App.vue')
const AdminBorrows = () => import('@/pages/admin-borrows/App.vue')
const AdminImport = () => import('@/pages/admin-import/App.vue')
const AdminOverdue = () => import('@/pages/admin-overdue/App.vue')

const routes = [
  {
    path: '/',
    redirect: '/books/'
  },
  // 登录/注册页面 - 不使用 MainLayout
  {
    path: '/login/',
    name: 'login',
    component: Login,
    meta: { guest: true }
  },
  {
    path: '/register/',
    name: 'register',
    component: Register,
    meta: { guest: true }
  },
  // 主布局页面 - 共享 MainLayout
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: 'books/',
        name: 'books',
        component: Books
      },
      {
        path: 'books/:id/',
        name: 'book-detail',
        component: BookDetail
      },
      {
        path: 'my/borrows/',
        name: 'my-borrows',
        component: MyBorrows,
        meta: { requiresAuth: true }
      },
      {
        path: 'manage/books/',
        name: 'admin-books',
        component: AdminBooks,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'manage/borrows/',
        name: 'admin-borrows',
        component: AdminBorrows,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'manage/import-export/',
        name: 'admin-import',
        component: AdminImport,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'manage/overdue/',
        name: 'admin-overdue',
        component: AdminOverdue,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
    ]
  },
  // 捕获所有未匹配路由，重定向到图书页
  {
    path: '/:pathMatch(.*)*',
    redirect: '/books/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const user = currentUser.value

  // 需要登录的页面
  if (to.meta.requiresAuth && !user) {
    next('/login/')
    return
  }

  // 需要管理员权限的页面
  if (to.meta.requiresAdmin && !isAdmin()) {
    next('/books/')
    return
  }

  // 已登录用户访问登录/注册页，重定向到图书页
  if (to.meta.guest && user) {
    next('/books/')
    return
  }

  next()
})

export default router
