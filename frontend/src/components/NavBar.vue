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

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'NavBar',
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        },
    },
    methods: {
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
            this.close();
        },
        toggle() {
            this.isOpen = !this.isOpen
        },
        close() {
        this.isOpen = false
        },
        onClickOutside(e) {
            const navEl = this.$refs.nav
            if (!navEl) return
            const clickedInsideNav = navEl.contains(e.target)
            const clickedBurger = e.target.closest && e.target.closest('.burger')
            if (this.isOpen && !clickedInsideNav && !clickedBurger) {
            this.isOpen = false
            }
        }
    },
    data() {
        return {
        isOpen: false
        }
    },
    mounted() {
        document.addEventListener('click', this.onClickOutside)
    },
    beforeUnmount() {
        document.removeEventListener('click', this.onClickOutside)
    },
};
</script>

<style scoped>

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
        position: absolute;    /* 從文檔 flow 拿掉，避免覆蓋整頁內容 */
        top: 100%;             /* 放在 navbar 底下 */
        left: 0;
        right: 0;
        background-color: #f3f3f3;   /* 給背景，避免內容透過看見下層 */
        box-shadow: 0 6px 18px rgba(0,0,0,0.06);
        pointer-events: none;  /* 預設不接收指標事件（closed 狀態）*/
        z-index: 9;            /* 在 navbar 下，但可視需要調整 */
    }

    .navbar ul.open {
        max-height: 500px; /* 根據選單長度調整 */
        pointer-events: auto;  /* 開啟時才可以點擊 ul 內的項目 */
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
        /*position: relative; 
        z-index: 10;*/
    }

    .strip{
        display: flex;
        height:1.5px ;
        background-color:#ddd;
        width: calc(100% + 40px);
    }

}

</style>