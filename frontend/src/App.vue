<script setup>
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <Navbar />
  <main class="mx-auto max-w-7xl px-3 pb-8 sm:px-6 sm:pb-10 lg:px-8">
    <RouterView />
  </main>
</template>

<style scoped></style>
