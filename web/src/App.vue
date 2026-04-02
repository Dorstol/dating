<script setup>
import { onMounted } from 'vue'
import { useTelegram } from './composables/useTelegram'

const { isTelegram, ready, expand } = useTelegram()

onMounted(() => {
  if (isTelegram.value) {
    ready()
    expand()
  }
})
</script>

<template>
  <router-view />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #fff;
  color: #1a1a1a;
  -webkit-font-smoothing: antialiased;
}
</style>
