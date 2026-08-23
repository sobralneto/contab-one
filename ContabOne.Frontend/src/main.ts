import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'

import App from './App.vue'
import router from './router'
import { registerGuards } from './router/guards'
import './style.css'

// ── Bootstrap ──
const app = createApp(App)

app.use(createPinia())
app.use(router)
// Unstyled mode: usamos Tailwind + nossos design tokens para todo o visual
app.use(PrimeVue, {
  unstyled: true,
})

// Register route guards (auth + page title)
registerGuards(router)

app.mount('#app')
