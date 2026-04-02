<script setup>
const props = defineProps({
  matchId: { type: String, required: true },
})
</script>

<template>
  <div class="chat">
    <h2>Chat #{{ matchId }}</h2>
    <p class="placeholder">Chat interface will appear here (Step 5)</p>
  </div>
</template>

<style scoped>
.chat {
  padding: 16px;
}

.placeholder {
  text-align: center;
  color: #999;
  margin-top: 120px;
}
</style>
