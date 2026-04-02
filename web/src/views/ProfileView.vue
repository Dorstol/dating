<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

onMounted(async () => {
  if (!auth.user) {
    await auth.fetchUser()
  }
})

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}
</script>

<template>
  <div class="profile">
    <h2>Profile</h2>

    <div v-if="auth.user" class="profile-card">
      <p class="name">{{ auth.user.first_name }} {{ auth.user.last_name }}</p>
      <p class="info" v-if="auth.user.age">Age: {{ auth.user.age }}</p>
      <p class="info" v-if="auth.user.location">Location: {{ auth.user.location }}</p>
      <p class="info" v-if="auth.user.bio">{{ auth.user.bio }}</p>
    </div>
    <p v-else class="placeholder">Loading profile...</p>

    <button @click="handleLogout" class="logout-btn">Log out</button>

    <nav class="bottom-nav">
      <router-link to="/" class="nav-item">Discover</router-link>
      <router-link to="/matches" class="nav-item">Matches</router-link>
      <router-link to="/profile" class="nav-item active">Profile</router-link>
    </nav>
  </div>
</template>

<style scoped>
.profile {
  padding: 16px;
  padding-bottom: 72px;
}

.profile-card {
  background: #f9f9f9;
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
}

.name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.info {
  color: #666;
  margin: 4px 0;
}

.logout-btn {
  width: 100%;
  padding: 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 16px;
}

.placeholder {
  text-align: center;
  color: #999;
  margin-top: 40px;
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  background: white;
  border-top: 1px solid #eee;
  padding: 12px 0;
}

.nav-item {
  flex: 1;
  text-align: center;
  text-decoration: none;
  color: #999;
  font-size: 14px;
}

.nav-item.active,
.nav-item.router-link-active {
  color: #7c3aed;
  font-weight: 600;
}
</style>
