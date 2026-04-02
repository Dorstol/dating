<script setup>
</script>

<template>
  <div class="matches">
    <h2>Matches</h2>
    <p class="placeholder">Match list will appear here (Step 5)</p>

    <nav class="bottom-nav">
      <router-link to="/" class="nav-item">Discover</router-link>
      <router-link to="/matches" class="nav-item active">Matches</router-link>
      <router-link to="/profile" class="nav-item">Profile</router-link>
    </nav>
  </div>
</template>

<style scoped>
.matches {
  padding: 16px;
  padding-bottom: 72px;
}

.placeholder {
  text-align: center;
  color: #999;
  margin-top: 120px;
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
