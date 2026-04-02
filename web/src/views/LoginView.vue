<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useTelegram } from '../composables/useTelegram'

const auth = useAuthStore()
const router = useRouter()
const { isTelegram, getInitData, ready } = useTelegram()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  // Auto-login via Telegram WebApp
  if (isTelegram.value) {
    ready()
    const initData = getInitData()
    if (initData) {
      loading.value = true
      try {
        await auth.loginTelegram(initData)
        router.push({ name: 'Home' })
      } catch (e) {
        error.value = 'Telegram auth failed'
      } finally {
        loading.value = false
      }
    }
  }
})

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.loginEmail(email.value, password.value)
    router.push({ name: 'Home' })
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login">
    <h1>Dating App</h1>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="isTelegram" class="tg-notice">
      <p>Authenticating via Telegram...</p>
    </div>

    <form v-else @submit.prevent="handleLogin" class="login-form">
      <input
        v-model="email"
        type="email"
        placeholder="Email"
        required
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        required
      />
      <button type="submit" :disabled="loading">Log in</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
.login {
  max-width: 360px;
  margin: 80px auto;
  padding: 0 16px;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

button {
  padding: 12px;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
}

.error {
  color: #ef4444;
  font-size: 14px;
}

.loading, .tg-notice {
  margin-top: 40px;
  color: #666;
}
</style>
