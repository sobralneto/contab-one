<template>
  <div class="auth-layout">
    <!-- Animated gradient background -->
    <div class="auth-bg">
      <div class="auth-bg-orb orb-1"></div>
      <div class="auth-bg-orb orb-2"></div>
      <div class="auth-bg-orb orb-3"></div>
    </div>

    <!-- Card -->
    <div class="auth-card glass animate-fade-in">
      <div class="auth-brand">
        <img class="brand-logo" :src="logoVertical" alt="Contab One" />
      </div>
      <router-view />
    </div>

    <!-- Footer -->
    <p class="auth-footer text-muted">
      &copy; {{ new Date().getFullYear() }} Contab One
    </p>
  </div>
</template>

<script setup lang="ts">
// Auth layout: full-screen gradient background with centered glass card
import logoVertical from "@/assets/contab-one-vertical.png";
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
}

/* ── Animated gradient orbs ── */
.auth-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: linear-gradient(
    135deg,
    #e6f3e5 0%,
    #f0f7ef 30%,
    #f2f2f2 70%,
    #e6f3e5 100%
  );
}

.dark .auth-bg {
  background: linear-gradient(
    135deg,
    #171717 0%,
    #1f1f1f 30%,
    #262626 70%,
    #1f1f1f 100%
  );
}

.auth-bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(
    circle,
    rgba(var(--accent-rgb), 0.30) 0%,
    transparent 70%
  );
  top: -200px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(
    circle,
    rgba(var(--accent-rgb), 0.25) 0%,
    transparent 70%
  );
  bottom: -150px;
  left: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 350px;
  height: 350px;
  background: radial-gradient(
    circle,
    rgba(var(--accent-rgb), 0.20) 0%,
    transparent 70%
  );
  top: 40%;
  right: 30%;
  animation-delay: -14s;
}

@keyframes float {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.05);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.95);
  }
}

/* ── Card ── */
.auth-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
  border-radius: var(--radius-lg);
  padding: 2.5rem 2rem;
  box-shadow: var(--shadow-lg);
}

.auth-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
}

.brand-logo {
  display: block;
  width: 220px;
  max-width: 70%;
  height: auto;
}

/* O card fica escuro no dark mode e a palavra "CONTAB" da logo é verde-escura:
   uma base clara atrás da logo mantém o contraste. */
.dark .brand-logo {
  background: #ffffff;
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
}

/* ── Footer ── */
.auth-footer {
  position: relative;
  z-index: 1;
  margin-top: 2rem;
  font-size: 12px;
}
</style>
