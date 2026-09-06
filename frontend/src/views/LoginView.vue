<template>
  <div class="min-h-screen bg-surface-950 flex items-center justify-center p-4">
    <!-- Background decoration -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary-600/8 blur-3xl" />
      <div class="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-accent-600/8 blur-3xl" />
    </div>

    <div class="relative w-full max-w-md animate-slide-up">
      <!-- Logo -->
      <div class="text-center mb-8">
        <RouterLink to="/" class="inline-flex items-center gap-2.5">
          <div class="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
            <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="3 17 9 11 13 15 21 7" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="text-xl font-bold text-surface-100">QuantDash</span>
        </RouterLink>
        <p class="text-surface-400 text-sm mt-2">Quantitative Trading Platform</p>
      </div>

      <!-- Card -->
      <div class="glass rounded-2xl p-8 shadow-card-lg border border-surface-700/50">
        <h1 class="text-xl font-bold text-surface-100 mb-1">เข้าสู่ระบบ</h1>
        <p class="text-sm text-surface-400 mb-6">
          ยังไม่มีบัญชี?
          <RouterLink to="/register" class="text-primary-400 hover:text-primary-300 font-medium transition-colors">
            สมัครสมาชิก
          </RouterLink>
        </p>

        <!-- Error alert -->
        <Transition name="slide-alert">
          <div v-if="error"
            class="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-bear/10 border border-bear/30 mb-5 text-sm text-bear">
            <svg class="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
            </svg>
            <span>{{ error }}</span>
          </div>
        </Transition>

        <form @submit.prevent="handleSubmit" class="space-y-4" novalidate>
          <!-- Email or Username -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-surface-300">อีเมล หรือ ชื่อผู้ใช้</label>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
              </svg>
              <input
                v-model="form.login"
                type="text"
                autocomplete="username"
                placeholder="email@example.com หรือ username"
                required
                :class="inputClass(!!errors.login)"
                class="w-full pl-9 pr-4 py-2.5 bg-surface-800 border rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors"
              />
            </div>
            <p v-if="errors.login" class="text-xs text-bear">{{ errors.login }}</p>
          </div>

          <!-- Password -->
          <div class="space-y-1.5">
            <div class="flex justify-between">
              <label class="text-xs font-medium text-surface-300">รหัสผ่าน</label>
              <button type="button" class="text-xs text-primary-400 hover:text-primary-300 transition-colors">
                ลืมรหัสผ่าน?
              </button>
            </div>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
              </svg>
              <input
                v-model="form.password"
                :type="showPwd ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                required
                :class="inputClass(!!errors.password)"
                class="w-full pl-9 pr-10 py-2.5 bg-surface-800 border rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors"
              />
              <button type="button" @click="showPwd = !showPwd"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300 transition-colors">
                <svg v-if="!showPwd" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/>
                </svg>
              </button>
            </div>
            <p v-if="errors.password" class="text-xs text-bear">{{ errors.password }}</p>
          </div>

          <!-- Submit -->
          <button type="submit" :disabled="authStore.loading"
            class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all duration-150 mt-2"
            :class="authStore.loading
              ? 'bg-primary-600/50 text-white/50 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-500 active:bg-primary-700 text-white shadow-glow hover:shadow-glow'">
            <svg v-if="authStore.loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ authStore.loading ? 'กำลังเข้าสู่ระบบ…' : 'เข้าสู่ระบบ' }}
          </button>
        </form>

        <!-- Divider -->
        <div class="flex items-center gap-3 my-5">
          <div class="flex-1 h-px bg-surface-700" />
          <span class="text-xs text-surface-500">หรือ</span>
          <div class="flex-1 h-px bg-surface-700" />
        </div>

        <!-- Social login placeholders -->
        <div class="grid grid-cols-2 gap-2">
          <button v-for="p in socialProviders" :key="p.id"
            :disabled="!p.enabled" @click="socialLogin(p.id)"
            class="flex items-center justify-center gap-2 py-2 rounded-xl border text-sm font-medium transition-all"
            :class="p.enabled
              ? 'bg-surface-800 border-surface-700 text-surface-200 hover:border-primary-600/50 hover:bg-surface-700'
              : 'bg-surface-800/30 border-surface-700/30 text-surface-600 cursor-not-allowed'">
            <span>{{ p.icon }}</span>
            <span>{{ p.name }}</span>
          </button>
        </div>
      </div>

      <!-- Security note -->
      <p class="text-center text-xs text-surface-600 mt-5 flex items-center justify-center gap-1.5">
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
        </svg>
        ป้องกันด้วย JWT + bcrypt · ข้อมูลเข้ารหัสทั้งหมด
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { authApi } from '@/api/authApi'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const form    = reactive({ login: '', password: '' })
const errors  = reactive({ login: '', password: '' })
const error   = ref('')
const showPwd = ref(false)
const socialProviders = ref<{ id:string;name:string;icon:string;enabled:boolean }[]>([])

onMounted(async () => {
  if (authStore.isLoggedIn) { router.replace('/dashboard'); return }
  try {
    const r = await authApi.providers()
    socialProviders.value = r.data.providers.filter(p => p.id !== 'local')
  } catch { /* ignore */ }
})

function inputClass(hasError: boolean) {
  return hasError ? 'border-bear/60 focus:border-bear' : 'border-surface-700 focus:border-primary-500'
}

function validate() {
  errors.login    = form.login.trim()    ? '' : 'กรุณากรอกอีเมลหรือชื่อผู้ใช้'
  errors.password = form.password.trim() ? '' : 'กรุณากรอกรหัสผ่าน'
  return !errors.login && !errors.password
}

async function handleSubmit() {
  error.value = ''
  if (!validate()) return
  const result = await authStore.login(form.login.trim(), form.password)
  if (result.ok) {
    const redirect = route.query.redirect as string | undefined
    router.push(redirect && redirect.startsWith('/') ? redirect : '/dashboard')
  } else {
    error.value = result.error
  }
}

function socialLogin(id: string) {
  // TODO: implement OAuth flow
}
</script>

<style scoped>
.slide-alert-enter-active { transition: all .2s ease; }
.slide-alert-leave-active { transition: all .15s ease; }
.slide-alert-enter-from   { opacity: 0; transform: translateY(-8px); }
.slide-alert-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
