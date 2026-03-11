<script setup>
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <Navbar />
  <main class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
    <RouterView />
  </main>
</template>

<style scoped></style>
