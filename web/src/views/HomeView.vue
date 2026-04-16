<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api/client'

const router = useRouter()

const suggestions = ref([])
const currentIndex = ref(0)
const loading = ref(true)
const actionLoading = ref(false)
const swipeDir = ref(null) // 'left' | 'right' | null

const menuOpen = ref(false)
const reportModal = ref(false)
const reportReasons = ['Spam', 'Fake', 'Harassment', 'Inappropriate Content']

function openMenu() { menuOpen.value = true }
function closeMenu() { menuOpen.value = false }

async function blockUser() {
  const user = current()
  if (!user) return
  closeMenu()
  try {
    await api.post(`/users/${user.id}/block`)
    next()
  } catch (e) {
    console.error('Block failed', e)
  }
}

async function reportUser(reason) {
  const user = current()
  if (!user) return
  reportModal.value = false
  try {
    await api.post(`/users/${user.id}/report`, { reason })
    next()
  } catch (e) {
    console.error('Report failed', e)
  }
}

const photoIndex = ref(0)
let touchStartX = 0

const current = () => suggestions.value[currentIndex.value] || null

// Reset photo index when card changes
watch(currentIndex, () => { photoIndex.value = 0 })

function allPhotos(user) {
  // photos is list of {id, filename, order}
  if (user.photos && user.photos.length) return user.photos.map(p => p.filename)
  if (user.photo) return [user.photo]
  return []
}

function onTouchStart(e) {
  touchStartX = e.touches[0].clientX
}

function onTouchEnd(e) {
  const user = current()
  if (!user) return
  const photos = allPhotos(user)
  if (photos.length <= 1) return

  const dx = e.changedTouches[0].clientX - touchStartX
  if (Math.abs(dx) < 40) return // ignore tiny swipes

  if (dx < 0 && photoIndex.value < photos.length - 1) photoIndex.value++
  else if (dx > 0 && photoIndex.value > 0) photoIndex.value--
}

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
  swipeDir.value = 'right'

  try {
    const { data } = await api.post(`/matches/${user.id}`)
    await wait(350)
    if (data.is_mutual) {
      alert(`It's a match with ${user.first_name}!`)
    }
    next()
  } catch (e) {
    console.error('Like failed', e)
  } finally {
    swipeDir.value = null
    actionLoading.value = false
  }
}

async function pass() {
  if (actionLoading.value) return
  actionLoading.value = true
  swipeDir.value = 'left'
  await wait(350)
  next()
  swipeDir.value = null
  actionLoading.value = false
}

function next() {
  if (currentIndex.value < suggestions.value.length - 1) {
    currentIndex.value++
  } else {
    suggestions.value = []
  }
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
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

    <div
      v-else
      class="card"
      :class="{ 'swipe-left': swipeDir === 'left', 'swipe-right': swipeDir === 'right' }"
    >
      <div
        class="card-photo"
        @touchstart.passive="onTouchStart"
        @touchend.passive="onTouchEnd"
      >
        <template v-if="allPhotos(current()).length">
          <img
            :src="`/static/photos/${allPhotos(current())[photoIndex]}`"
            :alt="current().first_name"
          />
          <!-- tap zones for prev/next -->
          <div class="photo-prev" @click="photoIndex > 0 && photoIndex--" />
          <div class="photo-next" @click="photoIndex < allPhotos(current()).length - 1 && photoIndex++" />
          <!-- dots -->
          <div v-if="allPhotos(current()).length > 1" class="photo-dots">
            <span
              v-for="(_, i) in allPhotos(current())"
              :key="i"
              class="dot"
              :class="{ active: i === photoIndex }"
              @click.stop="photoIndex = i"
            />
          </div>
        </template>
        <div v-else class="no-photo">{{ current().first_name[0] }}</div>
      </div>

      <div class="card-info">
        <div class="card-info-top">
          <div>
            <h3>{{ current().first_name }}, {{ current().age || '?' }}</h3>
            <p v-if="current().location" class="location">{{ current().location }}</p>
          </div>
          <button class="menu-btn" @click.stop="openMenu">⋯</button>
        </div>
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

    <!-- Overlay menu -->
    <div v-if="menuOpen" class="overlay" @click="closeMenu">
      <div class="menu-sheet" @click.stop>
        <button class="menu-item danger" @click="blockUser">Block user</button>
        <button class="menu-item danger" @click="closeMenu(); reportModal = true">Report user</button>
        <button class="menu-item" @click="closeMenu">Cancel</button>
      </div>
    </div>

    <!-- Report modal -->
    <div v-if="reportModal" class="overlay" @click="reportModal = false">
      <div class="menu-sheet" @click.stop>
        <p class="sheet-title">Reason for report</p>
        <button
          v-for="reason in reportReasons"
          :key="reason"
          class="menu-item"
          @click="reportUser(reason)"
        >{{ reason }}</button>
        <button class="menu-item" @click="reportModal = false">Cancel</button>
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
  transform-origin: bottom center;
  transition: transform 0.35s ease, opacity 0.35s ease;
}

.card.swipe-left {
  transform: translateX(-130%) rotate(-20deg);
  opacity: 0;
}

.card.swipe-right {
  transform: translateX(130%) rotate(20deg);
  opacity: 0;
}

.card-photo {
  width: 100%;
  flex: 1;
  min-height: 0;
  background: #f0f0f0;
  position: relative;
  overflow: hidden;
}

.card-photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.photo-prev,
.photo-next {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 35%;
  cursor: pointer;
}

.photo-prev { left: 0; }
.photo-next { right: 0; }

.photo-dots {
  position: absolute;
  top: 10px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 5px;
  pointer-events: none;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.5);
  pointer-events: all;
  cursor: pointer;
  transition: background 0.2s;
}

.dot.active {
  background: white;
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

.card-info-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.menu-btn {
  background: none;
  border: none;
  font-size: 22px;
  color: #999;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  flex-shrink: 0;
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}

.menu-sheet {
  width: 100%;
  background: white;
  border-radius: 16px 16px 0 0;
  padding: 8px 0 24px;
  display: flex;
  flex-direction: column;
}

.sheet-title {
  text-align: center;
  color: #999;
  font-size: 13px;
  padding: 8px 16px 4px;
}

.menu-item {
  padding: 16px;
  background: none;
  border: none;
  font-size: 16px;
  text-align: left;
  cursor: pointer;
  color: #1a1a1a;
}

.menu-item:active {
  background: #f5f5f5;
}

.menu-item.danger {
  color: #ef4444;
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
