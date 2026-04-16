<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api/client'

const auth = useAuthStore()
const router = useRouter()
const editing = ref(false)
const saving = ref(false)

const form = ref({
  bio: '',
  age: null,
  gender: '',
})

onMounted(async () => {
  if (!auth.user) {
    await auth.fetchUser()
  }
  if (auth.user) {
    form.value.bio = auth.user.bio || ''
    form.value.age = auth.user.age
    form.value.gender = auth.user.gender || ''
  }
})

async function saveProfile() {
  saving.value = true
  try {
    await api.patch('/users/me', {
      bio: form.value.bio || null,
      age: form.value.age ? Number(form.value.age) : null,
      gender: form.value.gender || null,
    })
    await auth.fetchUser()
    editing.value = false
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
}

</script>

<template>
  <div class="profile">
    <h2>Profile</h2>

    <div v-if="auth.user" class="profile-card">
      <div class="photo-section">
        <div class="photo">
          <img
            v-if="auth.user.photo"
            :src="`/static/photos/${auth.user.photo}`"
            alt="Profile photo"
          />
          <span v-else class="initials">
            {{ auth.user.first_name[0] }}
          </span>
        </div>
        <label class="upload-btn">
          Change photo
          <input type="file" accept="image/*" @change="uploadPhoto" hidden />
        </label>
      </div>

      <div v-if="!editing" class="info">
        <p class="name">{{ auth.user.first_name }} {{ auth.user.last_name }}</p>
        <p v-if="auth.user.age" class="detail">Age: {{ auth.user.age }}</p>
        <p v-if="auth.user.gender" class="detail">Gender: {{ auth.user.gender }}</p>
        <p v-if="auth.user.location" class="detail">Location: {{ auth.user.location }}</p>
        <p v-if="auth.user.bio" class="bio">{{ auth.user.bio }}</p>

        <div v-if="auth.user.interests?.length" class="interests">
          <span v-for="i in auth.user.interests" :key="i.id" class="tag">
            {{ i.name }}
          </span>
        </div>

        <button @click="editing = true" class="btn edit">Edit profile</button>
      </div>

      <form v-else @submit.prevent="saveProfile" class="edit-form">
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
        <div class="form-actions">
          <button type="button" @click="editing = false" class="btn cancel">Cancel</button>
          <button type="submit" :disabled="saving" class="btn save">Save</button>
        </div>
      </form>
    </div>
    <p v-else class="status">Loading...</p>

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

.profile-card {
  margin: 16px 0;
}

.photo-section {
  text-align: center;
  margin-bottom: 16px;
}

.photo {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  margin: 0 auto 12px;
  overflow: hidden;
  background: #f0e6ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.initials {
  font-size: 36px;
  color: #7c3aed;
}

.upload-btn {
  color: #7c3aed;
  font-size: 14px;
  cursor: pointer;
}

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

.btn {
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  width: 100%;
}

.btn.edit {
  margin-top: 16px;
  background: #7c3aed;
  color: white;
}

.btn.save {
  background: #7c3aed;
  color: white;
  flex: 1;
}

.btn.cancel {
  background: #f3f3f3;
  color: #666;
  flex: 1;
}

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
  text-decoration: none;
  color: #999;
  font-size: 14px;
}

.nav-item.active {
  color: #7c3aed;
  font-weight: 600;
}
</style>
