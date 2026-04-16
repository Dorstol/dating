<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import api from '../api/client'

const props = defineProps({
  matchId: { type: String, required: true },
})

const auth = useAuthStore()
const messages = ref([])
const newMessage = ref('')
const loading = ref(true)
const messagesContainer = ref(null)
const menuOpen = ref(false)
const reportModal = ref(false)
const reportReasons = ['Spam', 'Fake', 'Harassment', 'Inappropriate Content']
const partnerId = ref(null)

let ws = null

onMounted(async () => {
  if (!auth.user) await auth.fetchUser()
  await loadHistory()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})

async function loadHistory() {
  try {
    const { data } = await api.get(`/chat/${props.matchId}/history`)
    messages.value = data.messages.reverse()
    // infer partner id from history
    const other = messages.value.find(m => m.sender_id !== auth.user?.id)
    if (other) partnerId.value = other.sender_id

    // Mark as read
    await api.post(`/chat/${props.matchId}/read`)
  } catch (e) {
    console.error('Failed to load history', e)
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function connectWebSocket() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${location.host}/api/v1/chat/ws/${props.matchId}?token=${auth.token}`

  ws = new WebSocket(wsUrl)

  ws.onmessage = async (event) => {
    const msg = JSON.parse(event.data)
    messages.value.push(msg)
    await nextTick()
    scrollToBottom()
  }

  ws.onclose = () => {
    console.log('WebSocket closed')
  }
}

function sendMessage() {
  const text = newMessage.value.trim()
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return

  ws.send(JSON.stringify({ text }))
  newMessage.value = ''
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

function isOwn(msg) {
  return msg.sender_id === auth.user?.id
}

function formatTime(dateStr) {
  const d = new Date(dateStr)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

async function blockUser() {
  if (!partnerId.value) return
  menuOpen.value = false
  try {
    await api.post(`/users/${partnerId.value}/block`)
    router.push('/matches')
  } catch (e) {
    console.error('Block failed', e)
  }
}

async function reportUser(reason) {
  if (!partnerId.value) return
  reportModal.value = false
  try {
    await api.post(`/users/${partnerId.value}/report`, { reason })
  } catch (e) {
    console.error('Report failed', e)
  }
}
</script>

<template>
  <div class="chat">
    <header class="chat-header">
      <router-link to="/matches" class="back">&#8592;</router-link>
      <h3>Chat</h3>
      <button class="menu-btn" @click="menuOpen = true">⋯</button>
    </header>

    <!-- Overlay menu -->
    <div v-if="menuOpen" class="overlay" @click="menuOpen = false">
      <div class="menu-sheet" @click.stop>
        <button class="menu-item danger" @click="blockUser">Block user</button>
        <button class="menu-item danger" @click="menuOpen = false; reportModal = true">Report user</button>
        <button class="menu-item" @click="menuOpen = false">Cancel</button>
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

    <div v-if="loading" class="status">Loading...</div>

    <div v-else ref="messagesContainer" class="messages">
      <div v-if="!messages.length" class="status">
        No messages yet. Say hi!
      </div>
      <div
        v-for="msg in messages"
        :key="msg.id"
        class="message"
        :class="{ own: isOwn(msg) }"
      >
        <p class="text">{{ msg.text }}</p>
        <span class="time">{{ formatTime(msg.created_at) }}</span>
      </div>
    </div>

    <form @submit.prevent="sendMessage" class="input-bar">
      <input
        v-model="newMessage"
        placeholder="Type a message..."
        autocomplete="off"
      />
      <button type="submit">Send</button>
    </form>
  </div>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.chat-header h3 {
  flex: 1;
}

.menu-btn {
  background: none;
  border: none;
  font-size: 22px;
  color: #999;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
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

.back {
  text-decoration: none;
  font-size: 22px;
  color: #333;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status {
  text-align: center;
  color: #999;
  margin: auto;
}

.message {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 16px;
  background: #f0f0f0;
  color: #1a1a1a;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.message.own {
  background: #7c3aed;
  color: white;
  align-self: flex-end;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 4px;
}

.text {
  word-wrap: break-word;
}

.time {
  display: block;
  font-size: 11px;
  opacity: 0.6;
  margin-top: 4px;
  text-align: right;
}

.input-bar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #eee;
  background: white;
}

.input-bar input {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 16px;
  outline: none;
}

.input-bar button {
  padding: 12px 20px;
  background: #7c3aed;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  cursor: pointer;
}
</style>
