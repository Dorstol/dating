<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api/client'

const auth = useAuthStore()
const router = useRouter()

// ── views: 'profile' | 'edit' | 'interests' | 'blocked'
const view = ref('profile')
const saving = ref(false)

const form = ref({ bio: '', age: null, gender: '', location: '' })

// interests: track selected by name (API accepts names)
const myInterestNames = ref(new Set())
const interestNameMap = ref({}) // id -> name
const popularInterests = ref([])
const interestSearch = ref('')
const searchResults = ref([])
let searchTimer = null

// blocked
const blockedUsers = ref([])

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  if (auth.user) syncForm()
})

function syncForm() {
  form.value.bio = auth.user.bio || ''
  form.value.age = auth.user.age
  form.value.gender = auth.user.gender || ''
  form.value.location = auth.user.location || ''
}

async function saveProfile() {
  saving.value = true
  try {
    await api.patch('/users/me', {
      bio: form.value.bio || null,
      age: form.value.age ? Number(form.value.age) : null,
      gender: form.value.gender || null,
      location: form.value.location || null,
    })
    await auth.fetchUser()
    view.value = 'profile'
  } catch (e) {
    console.error('Failed to save profile', e)
  } finally {
    saving.value = false
  }
}

async function uploadPhoto(event) {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    await api.post('/users/me/upload_photo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    await auth.fetchUser()
  } catch (e) {
    console.error('Upload failed', e)
  }
  event.target.value = ''
}

async function deletePhoto(photoId) {
  try {
    await api.delete(`/users/me/photos/${photoId}`)
    await auth.fetchUser()
  } catch (e) {
    console.error('Delete photo failed', e)
  }
}

// ── Interests ──────────────────────────────────────────────

async function openInterests() {
  myInterestNames.value = new Set(auth.user.interests.map(i => i.name))
  const { data } = await api.get('/interests/popular?limit=30')
  popularInterests.value = data.items
  data.items.forEach(i => { interestNameMap.value[i.id] = i.name })
  interestSearch.value = ''
  searchResults.value = []
  view.value = 'interests'
}

function onSearchInput() {
  clearTimeout(searchTimer)
  const q = interestSearch.value.trim()
  if (!q) { searchResults.value = []; return }
  searchTimer = setTimeout(async () => {
    const { data } = await api.get(`/interests/search?q=${encodeURIComponent(q)}&limit=20`)
    searchResults.value = data.items
    data.items.forEach(i => { interestNameMap.value[i.id] = i.name })
  }, 300)
}

function toggleInterest(interest) {
  const s = new Set(myInterestNames.value)
  s.has(interest.name) ? s.delete(interest.name) : s.add(interest.name)
  myInterestNames.value = s
}

async function saveInterests() {
  saving.value = true
  try {
    await api.put('/interests/my', { interests: [...myInterestNames.value] })
    await auth.fetchUser()
    view.value = 'profile'
  } catch (e) {
    console.error('Failed to save interests', e)
  } finally {
    saving.value = false
  }
}

// ── Blocked users ──────────────────────────────────────────

async function openBlocked() {
  const { data } = await api.get('/users/blocked')
  blockedUsers.value = data
  view.value = 'blocked'
}

async function unblock(userId) {
  try {
    await api.delete(`/users/${userId}/block`)
    blockedUsers.value = blockedUsers.value.filter(b => b.blocked_user_id !== userId)
  } catch (e) {
    console.error('Unblock failed', e)
  }
}
</script>

<template>
  <div class="profile">

    <!-- ── Profile view ── -->
    <template v-if="view === 'profile'">
      <h2>Profile</h2>

      <div v-if="auth.user" class="profile-card">
        <div class="photo-section">
          <div class="photos-grid">
            <div v-for="p in auth.user.photos" :key="p.id" class="photo-thumb">
              <img :src="`/static/photos/${p.filename}`" alt="Photo" />
              <button class="delete-photo" @click="deletePhoto(p.id)">×</button>
            </div>
            <div v-if="!auth.user.photos.length" class="photo-thumb placeholder">
              <span class="initials">{{ auth.user.first_name[0] }}</span>
            </div>
          </div>
          <label class="upload-btn" v-if="auth.user.photos.length < 6">
            + Add photo
            <input type="file" accept="image/*" @change="uploadPhoto" hidden />
          </label>
        </div>

        <p class="name">{{ auth.user.first_name }} {{ auth.user.last_name }}</p>
        <p v-if="auth.user.age" class="detail">Age: {{ auth.user.age }}</p>
        <p v-if="auth.user.gender" class="detail">Gender: {{ auth.user.gender }}</p>
        <p v-if="auth.user.location" class="detail">Location: {{ auth.user.location }}</p>
        <p v-if="auth.user.bio" class="bio">{{ auth.user.bio }}</p>

        <div v-if="auth.user.interests?.length" class="interests">
          <span v-for="i in auth.user.interests" :key="i.id" class="tag">{{ i.name }}</span>
        </div>

        <div class="profile-actions">
          <button class="btn purple" @click="syncForm(); view = 'edit'">Edit profile</button>
          <button class="btn purple" @click="openInterests">Edit interests</button>
          <button class="btn gray" @click="openBlocked">Blocked users</button>
        </div>
      </div>
      <p v-else class="status">Loading...</p>
    </template>

    <!-- ── Edit profile ── -->
    <template v-else-if="view === 'edit'">
      <div class="subpage-header">
        <button class="back-btn" @click="view = 'profile'">&#8592;</button>
        <h2>Edit profile</h2>
      </div>
      <form @submit.prevent="saveProfile" class="edit-form">
        <label>
          Bio
          <textarea v-model="form.bio" rows="3" placeholder="About yourself..." />
        </label>
        <label>
          Age
          <input v-model="form.age" type="number" min="16" max="100" />
        </label>
        <label>
          Gender
          <select v-model="form.gender">
            <option value="">Not specified</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </label>
        <label>
          Location
          <input v-model="form.location" type="text" placeholder="City or country" />
        </label>
        <div class="form-actions">
          <button type="button" @click="view = 'profile'" class="btn gray">Cancel</button>
          <button type="submit" :disabled="saving" class="btn purple">Save</button>
        </div>
      </form>
    </template>

    <!-- ── Edit interests ── -->
    <template v-else-if="view === 'interests'">
      <div class="subpage-header">
        <button class="back-btn" @click="view = 'profile'">&#8592;</button>
        <h2>Interests</h2>
        <button class="save-inline" :disabled="saving" @click="saveInterests">Save</button>
      </div>

      <input
        v-model="interestSearch"
        @input="onSearchInput"
        class="search-input"
        placeholder="Search interests..."
      />

      <p class="section-label">
        {{ interestSearch.trim() ? 'Search results' : 'Popular' }}
      </p>
      <div class="interests-grid">
        <button
          v-for="i in (interestSearch.trim() ? searchResults : popularInterests)"
          :key="i.id"
          class="interest-chip"
          :class="{ selected: myInterestNames.has(i.name) }"
          @click="toggleInterest(i)"
        >{{ i.name }}</button>
      </div>
    </template>

    <!-- ── Blocked users ── -->
    <template v-else-if="view === 'blocked'">
      <div class="subpage-header">
        <button class="back-btn" @click="view = 'profile'">&#8592;</button>
        <h2>Blocked users</h2>
      </div>
      <div v-if="!blockedUsers.length" class="status">No blocked users</div>
      <div v-else class="blocked-list">
        <div v-for="b in blockedUsers" :key="b.id" class="blocked-item">
          <span class="blocked-name">User #{{ b.blocked_user_id }}</span>
          <button class="btn-unblock" @click="unblock(b.blocked_user_id)">Unblock</button>
        </div>
      </div>
    </template>

    <nav class="bottom-nav">
      <div class="nav-item" @click="router.push('/')">Discover</div>
      <div class="nav-item" @click="router.push('/matches')">Matches</div>
      <div class="nav-item active" @click="router.push('/profile')">Profile</div>
    </nav>
  </div>
</template>

<style scoped>
.profile {
  padding: 16px;
  padding-bottom: 72px;
}

/* ── Subpage header ── */
.subpage-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.subpage-header h2 {
  flex: 1;
  margin: 0;
}

.back-btn {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
  color: #333;
  padding: 0;
}

.save-inline {
  background: none;
  border: none;
  color: #7c3aed;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

/* ── Photo section ── */
.photo-section {
  margin-bottom: 16px;
}

.photos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}

.photo-thumb {
  position: relative;
  aspect-ratio: 3/4;
  border-radius: 10px;
  overflow: hidden;
  background: #f0e6ff;
}

.photo-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.photo-thumb.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-photo {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.initials {
  font-size: 36px;
  color: #7c3aed;
}

.upload-btn {
  display: inline-block;
  color: #7c3aed;
  font-size: 14px;
  cursor: pointer;
  padding: 8px 16px;
  border: 1px dashed #7c3aed;
  border-radius: 8px;
}

/* ── Info ── */
.name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.detail {
  color: #666;
  margin: 4px 0;
  font-size: 14px;
}

.bio {
  margin-top: 12px;
  color: #444;
}

.interests {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.tag {
  padding: 4px 10px;
  background: #f0e6ff;
  color: #7c3aed;
  border-radius: 12px;
  font-size: 13px;
}

.profile-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

/* ── Buttons ── */
.btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  width: 100%;
}

.btn.purple {
  background: #7c3aed;
  color: white;
}

.btn.gray {
  background: #f3f3f3;
  color: #666;
}

/* ── Edit form ── */
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.edit-form label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  color: #666;
}

.edit-form input,
.edit-form textarea,
.edit-form select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

.form-actions {
  display: flex;
  gap: 12px;
}

.form-actions .btn {
  flex: 1;
}

/* ── Interests ── */
.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 16px;
  box-sizing: border-box;
  outline: none;
  margin-bottom: 16px;
}

.section-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 10px;
}

.interests-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.interest-chip {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1.5px solid #ddd;
  background: white;
  font-size: 14px;
  cursor: pointer;
  color: #333;
  transition: all 0.15s;
}

.interest-chip.selected {
  background: #7c3aed;
  border-color: #7c3aed;
  color: white;
}

/* ── Blocked ── */
.blocked-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.blocked-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid #f0f0f0;
}

.blocked-name {
  font-size: 15px;
  color: #333;
}

.btn-unblock {
  background: none;
  border: 1px solid #7c3aed;
  color: #7c3aed;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  cursor: pointer;
}

/* ── Misc ── */
.status {
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
