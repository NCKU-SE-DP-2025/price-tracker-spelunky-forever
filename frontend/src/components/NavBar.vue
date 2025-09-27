<template>
    <nav class="navbar">
        <div class="bur_bp">
            <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
            <div class="burger">
                <p class="line"></p>
                <p class="line"></p>
                <p class="line"></p>
            </div>
        </div>
        <ul>
            <p class="strip"></p>
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <p class="strip"></p>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <p class="strip"></p>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <p class="strip"></p>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
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
        }
    },
    methods: {
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
        }
    }
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
        box-shadow: none;
    }

    .strip{
        display: flex;
        height:1.5px ;
        background-color:#ddd;
        width: calc(100% + 40px);
    }

}

</style>