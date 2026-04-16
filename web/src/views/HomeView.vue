<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()

const suggestions = ref([])
const currentIndex = ref(0)
const loading = ref(true)
const actionLoading = ref(false)

const current = () => suggestions.value[currentIndex.value] || null

onMounted(async () => {
  await loadSuggestions()
})

async function loadSuggestions() {
  loading.value = true
  try {
    const { data } = await api.get('/matches/suggestion')
    suggestions.value = data.items
    currentIndex.value = 0
  } catch (e) {
    console.error('Failed to load suggestions', e)
  } finally {
    loading.value = false
  }
}

async function like() {
  const user = current()
  if (!user || actionLoading.value) return

  actionLoading.value = true
  try {
    const { data } = await api.post(`/matches/${user.id}`)
    if (data.is_mutual) {
      alert(`It's a match with ${user.first_name}!`)
    }
    next()
  } catch (e) {
    console.error('Like failed', e)
  } finally {
    actionLoading.value = false
  }
}

function pass() {
  next()
}

function next() {
  if (currentIndex.value < suggestions.value.length - 1) {
    currentIndex.value++
  } else {
    suggestions.value = []
  }
}
</script>

<template>
  <div class="home">
    <h2>Discover</h2>

    <div v-if="loading" class="status">Loading...</div>

    <div v-else-if="!current()" class="status">
      <p>No more suggestions</p>
      <button @click="loadSuggestions" class="btn reload">Refresh</button>
    </div>

    <div v-else class="card">
      <div class="card-photo">
        <img
          v-if="current().photo"
          :src="`/static/photos/${current().photo}`"
          :alt="current().first_name"
        />
        <div v-else class="no-photo">{{ current().first_name[0] }}</div>
      </div>

      <div class="card-info">
        <h3>{{ current().first_name }}, {{ current().age || '?' }}</h3>
        <p v-if="current().location" class="location">{{ current().location }}</p>
        <p v-if="current().bio" class="bio">{{ current().bio }}</p>
        <div v-if="current().interests?.length" class="interests">
          <span v-for="i in current().interests" :key="i.id" class="tag">
            {{ i.name }}
          </span>
        </div>
      </div>

      <div class="actions">
        <button @click="pass" class="btn pass" :disabled="actionLoading">Pass</button>
        <button @click="like" class="btn like" :disabled="actionLoading">Like</button>
      </div>
    </div>

    <nav class="bottom-nav">
      <div class="nav-item active" @click="router.push('/')">Discover</div>
      <div class="nav-item" @click="router.push('/matches')">Matches</div>
      <div class="nav-item" @click="router.push('/profile')">Profile</div>
    </nav>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  padding: 16px 16px 72px;
  box-sizing: border-box;
}

.status {
  text-align: center;
  color: #999;
  margin-top: 80px;
}

.card {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 400px;
  width: 100%;
  margin: 8px auto 0;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  min-height: 0;
}

.card-photo {
  width: 100%;
  flex: 1;
  min-height: 0;
  background: #f0f0f0;
}

.card-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-photo {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  color: #ccc;
  background: #f5f5f5;
}

.card-info {
  padding: 16px;
}

.card-info h3 {
  font-size: 22px;
  margin-bottom: 4px;
}

.location {
  color: #888;
  font-size: 14px;
}

.bio {
  margin-top: 8px;
  color: #555;
}

.interests {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.tag {
  padding: 4px 10px;
  background: #f0e6ff;
  color: #7c3aed;
  border-radius: 12px;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 12px;
  padding: 16px;
}

.btn {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.5;
}

.btn.pass {
  background: #f3f3f3;
  color: #666;
}

.btn.like {
  background: #7c3aed;
  color: white;
}

.btn.reload {
  margin-top: 16px;
  background: #7c3aed;
  color: white;
  padding: 12px 32px;
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
  cursor: pointer;
  padding: 6px 0;
  border-radius: 8px;
  transition: background 0.15s;
  user-select: none;
}

.nav-item:active {
  background: #f0e6ff;
}

.nav-item.active {
  color: #7c3aed;
  font-weight: 600;
}
</style>
