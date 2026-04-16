<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()
const matches = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/matches')
    matches.value = data.items
  } catch (e) {
    console.error('Failed to load matches', e)
  } finally {
    loading.value = false
  }
})

function openChat(match) {
  router.push({ name: 'Chat', params: { matchId: match.id } })
}
</script>

<template>
  <div class="matches">
    <h2>Matches</h2>

    <div v-if="loading" class="status">Loading...</div>

    <div v-else-if="!matches.length" class="status">
      <p>No matches yet</p>
      <p class="hint">Start swiping to find someone!</p>
    </div>

    <div v-else class="match-list">
      <div
        v-for="match in matches"
        :key="match.id"
        class="match-item"
        @click="openChat(match)"
      >
        <div class="avatar">
          <img
            v-if="match.matched_user?.photo"
            :src="`/static/photos/${match.matched_user.photo}`"
            :alt="match.matched_user.first_name"
          />
          <span v-else>{{ match.matched_user?.first_name?.[0] || '?' }}</span>
        </div>
        <div class="match-info">
          <p class="match-name">
            {{ match.matched_user?.first_name }}
            {{ match.matched_user?.last_name }}
          </p>
          <p class="match-status" :class="{ mutual: match.is_mutual }">
            {{ match.is_mutual ? 'Mutual match' : 'Liked' }}
          </p>
        </div>
      </div>
    </div>

    <nav class="bottom-nav">
      <div class="nav-item" @click="router.push('/')">Discover</div>
      <div class="nav-item active" @click="router.push('/matches')">Matches</div>
      <div class="nav-item" @click="router.push('/profile')">Profile</div>
    </nav>
  </div>
</template>

<style scoped>
.matches {
  padding: 16px;
  padding-bottom: 72px;
}

.status {
  text-align: center;
  color: #999;
  margin-top: 80px;
}

.hint {
  font-size: 14px;
  margin-top: 8px;
}

.match-list {
  margin-top: 12px;
}

.match-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.match-item:hover {
  background: #f9f9f9;
}

.avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #f0e6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  font-size: 20px;
  color: #7c3aed;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.match-name {
  font-weight: 600;
}

.match-status {
  font-size: 13px;
  color: #999;
}

.match-status.mutual {
  color: #7c3aed;
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
