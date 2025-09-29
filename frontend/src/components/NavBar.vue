<template>
    <nav class="navbar">
        <div class="bur_bp">
            <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
            <div class="burger" :class="{ open: isOpen }" @click="toggle" tabindex="0" @keydown.enter.prevent="toggle">
                <p class="line"></p>
                <p class="line"></p>
                <p class="line"></p>
            </div>
        </div>
        <ul ref="nav" :class="{ open: isOpen }">
            <li class="strip"></li>
            <li><RouterLink to="/overview" @click="close">物價概覽</RouterLink></li>
            <li class="strip"></li>
            <li><RouterLink to="/trending" @click="close">物價趨勢</RouterLink></li>
            <li class="strip"></li>
            <li><RouterLink to="/news" @click="close">相關新聞</RouterLink></li>
            <li class="strip"></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login" @click="close">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
    </nav>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'

const nav = ref(null)
const isOpen = ref(false)

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

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>

<style scoped>
/* 原本的 style 完全保留 */
.burger {
    display: none;            
}

.burger .line{
    padding: 2px 10px;
    border: none;
    background-color: black;
    margin: 1.5px
}

.strip{
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
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title > a{
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

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

@media (max-width: 768px) {
    .burger {
        display: flex;
        flex-direction: column;
    }

    .bur_bp {
        display: flex;
        align-items: center;
        flex-direction: row;
        justify-content: space-between;
    }

    .bp {
        display: flex;
        font-size: 20px;
        font-weight: bold;
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
    }

    .navbar ul.open {
        max-height: 500px;
        pointer-events: auto;
    }   

    .strip {
        display: flex;
        height:1.5px ;
        background-color:#ddd;
        width: calc(100% + 40px);
    }

    .navbar {
        flex-direction: column;
        align-items: stretch;
        box-shadow: 0 0 5px #000000;
        padding: 10px 20px;
        justify-content: center;
    }

    .strip{
        display: flex;
        height:1.5px ;
        background-color:#ddd;
        width: calc(100% + 40px);
    }

}
</style>
