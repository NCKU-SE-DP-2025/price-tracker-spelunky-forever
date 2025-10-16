<template>
  <nav class="navbar" :class="{ 'navbar-scrolled': hasScrolled }">
    <div class="bur_bp">
      <div class="title">
        <RouterLink to="/overview">價格追蹤小幫手</RouterLink>
      </div>
      <button
        class="burger"
        :class="{ open: isOpen }"
        @click="toggle"
        :aria-expanded="String(isOpen)"
        aria-controls="main-navlist"
        aria-label="Toggle navigation menu"
      >
        <span class="line" aria-hidden="true"></span>
        <span class="line" aria-hidden="true"></span>
        <span class="line" aria-hidden="true"></span>
      </button>
    </div>

    <ul id="main-navlist" ref="nav" :class="{ open: isOpen }">
      <li class="strip"></li>
      <li :class="{ active: isActive('/overview') }">
        <RouterLink to="/overview" @click="close">物價概覽</RouterLink>
      </li>
      <li class="strip"></li>
      <li :class="{ active: isActive('/trending') }">
        <RouterLink to="/trending" @click="close">物價趨勢</RouterLink>
      </li>
      <li class="strip"></li>
      <li :class="{ active: isActive('/news') }">
        <RouterLink to="/news" @click="close">相關新聞</RouterLink>
      </li>
      <li class="strip"></li>
      <li v-if="!isLoggedIn" :class="{ active: isActive('/login') }">
        <RouterLink to="/login" @click="close">登入</RouterLink>
      </li>
      <li v-else @click="logout">Hi, {{ getUserName }}! 登出</li>
    </ul>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRoute } from 'vue-router'

const nav = ref(null)
const isOpen = ref(false)
const hasScrolled = ref(false)
const route = useRoute()
const userStore = useAuthStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)
const getUserName = computed(() => userStore.getUserName)

function toggle() {
  isOpen.value = !isOpen.value
}
function close() {
  isOpen.value = false
}
function logout() {
  userStore.logout()
  close()
}
function onClickOutside(e) {
  const navEl = nav.value
  if (!navEl) return
  const clickedInsideNav = navEl.contains(e.target)
  const clickedBurger = e.target.closest && e.target.closest('.burger')
  if (isOpen.value && !clickedInsideNav && !clickedBurger) {
    isOpen.value = false
  }
}
function onKeydown(e) {
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}
function handleScroll() {
  if (window.scrollY > 10) {
    hasScrolled.value = true
    if (isOpen.value) close()
  } else {
    hasScrolled.value = false
  }
}
function isActive(path) {
  return route.path.startsWith(path)
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('click', onClickOutside)
  window.addEventListener('scroll', handleScroll)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', onClickOutside)
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.burger {
  display: none;
}
.burger .line {
  padding: 2px 10px;
  border: none;
  background-color: black;
  margin: 1.5px
}
.strip {
  display: none;
}
.navbar {
  display: flex;
  justify-content: space-between;
  background-color: #f3f3f3;
  padding: 1.5em;
  height: 4.5em;
  width: 100%;
  align-items: center;
  box-shadow: 0 0 5px #000000;
  transition: box-shadow .3s ease;
}
.navbar-scrolled {
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.navbar ul {
  list-style: none;
  display: flex;
  justify-content: space-around;
}
.title > a {
  display: flex;
  font-size: 1.4em;
  font-weight: bold;
  color: #2c3e50 !important;
}
.navbar li {
  color: #575B5D;
  margin: 0 .5em;
  font-size: 1.2em;
}
.navbar li:hover {
  cursor: pointer;
  font-weight: bold;
}
.navbar a {
  text-decoration: none;
  color: #575B5D;
}
.navbar li.active a {
  color: #0086f4;
  font-weight: bold;
  border-bottom: 2px solid #0086f4;
}

@media (max-width: 768px) {
  .burger {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 30px;                 
    height: 30px;
    padding: 4px;                
    box-sizing: border-box;      
    position: relative;          
    z-index: 1;
  }
  .bur_bp {
    display: flex;
    align-items: center;
    flex-direction: row;
    justify-content: space-between;
  }
  .navbar ul {
    flex-direction: column;
    align-items: center;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.75s ease;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: #f3f3f3;
    box-shadow: 0 6px 18px rgba(0,0,0,0.06);
    pointer-events: none;
    z-index: 9;
    gap: 10px;
  }
  .navbar ul.open {
    max-height: 500px;
    pointer-events: auto;
  }
  .strip {
    display: flex;
    height: 1.5px;
    background-color: #ddd;
    width: calc(100% + 40px);
    margin: 10px;
  }
  .navbar {
    flex-direction: column;
    align-items: stretch;
    box-shadow: 0 0 5px #000000;
    padding: 10px 20px;
    justify-content: center;
  }
  .burger::after {
    content: "";
    position: absolute;
    top: -6px;
    right: -6px;
    bottom: -6px;
    left: -6px;
    border-radius: 8px; 
    border: 1px solid rgba(0, 0, 0, 0.12);
    background: transparent;
    pointer-events: none; 
    transition: background-color 0.12s ease, box-shadow 0.12s ease;
    z-index: 0;
  }
  .burger:active::after,
  .burger.open::after {
    background-color: rgba(187, 182, 182, 0.644);
    box-shadow: 0 1px 4px rgb(255, 255, 255);
  }
  .burger:focus-visible::after {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 140, 255, 0.12);
  }
}
</style>
