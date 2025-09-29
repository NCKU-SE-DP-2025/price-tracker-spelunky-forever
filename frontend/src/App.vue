<template>
  <NavBar class="navbar" />
  <RouterView class="render" />
</template>

<script setup>
import NavBar from './components/NavBar.vue';
/*
  註：RouterView 是由 vue-router 全域註冊的組件（通常不需在這裡顯式註冊）。
  如果你的 linter 或環境要求，你也可以加：
  import { RouterView } from 'vue-router';
  但大多數專案不需要。
*/
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
.navbar{
  z-index: 1000;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
}
.render{
  margin-top: 4.5em;
}
</style>
