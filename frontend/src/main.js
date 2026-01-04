import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initAuth } from '@utils/auth'
import './styles/main.css'

// 初始化认证状态后再挂载应用
initAuth().finally(() => {
  const app = createApp(App)
  app.use(router)
  app.mount('#app')
})
