<template>
  <div class="min-h-screen bg-surface-950 flex items-center justify-center p-4">
    <!-- Background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -left-40 w-96 h-96 rounded-full bg-primary-600/8 blur-3xl" />
      <div class="absolute -bottom-40 -right-40 w-96 h-96 rounded-full bg-accent-600/8 blur-3xl" />
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

      <div class="glass rounded-2xl p-8 shadow-card-lg border border-surface-700/50">
        <h1 class="text-xl font-bold text-surface-100 mb-1">สมัครสมาชิก</h1>
        <p class="text-sm text-surface-400 mb-6">
          มีบัญชีแล้ว?
          <RouterLink to="/login" class="text-primary-400 hover:text-primary-300 font-medium transition-colors">
            เข้าสู่ระบบ
          </RouterLink>
        </p>

        <!-- Error / server errors -->
        <Transition name="slide-alert">
          <div v-if="error"
            class="flex items-start gap-2.5 px-4 py-3 rounded-xl bg-bear/10 border border-bear/30 mb-5 text-sm text-bear">
            <svg class="w-4 h-4 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
            </svg>
            <div>
              <p>{{ error }}</p>
              <ul v-if="pwdErrors.length" class="list-disc list-inside mt-1 space-y-0.5">
                <li v-for="e in pwdErrors" :key="e" class="text-xs">{{ e }}</li>
              </ul>
            </div>
          </div>
        </Transition>

        <form @submit.prevent="handleSubmit" class="space-y-4" novalidate>
          <!-- Display Name -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-surface-300">ชื่อที่แสดง <span class="text-surface-500">(ไม่บังคับ)</span></label>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
              </svg>
              <input v-model="form.display_name" type="text" maxlength="64"
                placeholder="ชื่อ Trader ของคุณ"
                class="w-full pl-9 pr-4 py-2.5 bg-surface-800 border border-surface-700 rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none focus:border-primary-500 transition-colors" />
            </div>
          </div>

          <!-- Email -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-surface-300">อีเมล <span class="text-bear">*</span></label>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/>
              </svg>
              <input v-model="form.email" type="email" autocomplete="email" required
                placeholder="email@example.com"
                :class="inputClass(!!errors.email)"
                class="w-full pl-9 pr-4 py-2.5 bg-surface-800 border rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors" />
            </div>
            <p v-if="errors.email" class="text-xs text-bear">{{ errors.email }}</p>
          </div>

          <!-- Username -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-surface-300">ชื่อผู้ใช้ <span class="text-bear">*</span></label>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"/>
              </svg>
              <input v-model="form.username" type="text" autocomplete="username" required
                placeholder="trader_username" minlength="3" maxlength="32"
                :class="inputClass(!!errors.username)"
                class="w-full pl-9 pr-4 py-2.5 bg-surface-800 border rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors" />
            </div>
            <p v-if="errors.username" class="text-xs text-bear">{{ errors.username }}</p>
            <p class="text-xs text-surface-500">3–32 ตัวอักษร ตัวอักษรภาษาอังกฤษ ตัวเลข _ -</p>
          </div>

          <!-- Password -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-surface-300">รหัสผ่าน <span class="text-bear">*</span></label>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25-2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
              </svg>
              <input v-model="form.password" :type="showPwd ? 'text' : 'password'"
                autocomplete="new-password" required placeholder="••••••••"
                :class="inputClass(!!errors.password)"
                class="w-full pl-9 pr-10 py-2.5 bg-surface-800 border rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors" />
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

            <!-- Password strength meter -->
            <div v-if="form.password" class="space-y-1.5">
              <div class="flex gap-1">
                <div v-for="i in 4" :key="i"
                  class="flex-1 h-1 rounded-full transition-all duration-300"
                  :class="i <= pwdStrength.score
                    ? ['bg-bear', 'bg-side', 'bg-side', 'bg-bull'][pwdStrength.score - 1] ?? 'bg-bull'
                    : 'bg-surface-700'" />
              </div>
              <p class="text-xs" :class="{
                'text-bear': pwdStrength.score <= 1,
                'text-side': pwdStrength.score === 2,
                'text-bull': pwdStrength.score >= 3,
              }">{{ pwdStrength.label }}</p>
            </div>
          </div>

          <!-- Confirm Password -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-surface-300">ยืนยันรหัสผ่าน <span class="text-bear">*</span></label>
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
              </svg>
              <input v-model="form.confirm" :type="showPwd ? 'text' : 'password'"
                autocomplete="new-password" required placeholder="••••••••"
                :class="inputClass(!!errors.confirm)"
                class="w-full pl-9 pr-4 py-2.5 bg-surface-800 border rounded-xl text-sm text-surface-100 placeholder-surface-500 outline-none transition-colors" />
            </div>
            <p v-if="errors.confirm" class="text-xs text-bear">{{ errors.confirm }}</p>
          </div>

          <!-- Terms -->
          <label class="flex items-start gap-2.5 cursor-pointer group">
            <input type="checkbox" v-model="form.agree"
              class="mt-0.5 w-4 h-4 rounded accent-primary-500 shrink-0" />
            <span class="text-xs text-surface-400 leading-snug">
              ยอมรับ
              <a href="#" class="text-primary-400 hover:underline">ข้อกำหนดการใช้งาน</a>
              และ
              <a href="#" class="text-primary-400 hover:underline">นโยบายความเป็นส่วนตัว</a>
            </span>
          </label>
          <p v-if="errors.agree" class="text-xs text-bear -mt-2">{{ errors.agree }}</p>

          <!-- Submit -->
          <button type="submit" :disabled="authStore.loading"
            class="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-semibold text-sm transition-all duration-150"
            :class="authStore.loading
              ? 'bg-primary-600/50 text-white/50 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-500 active:bg-primary-700 text-white shadow-glow'">
            <svg v-if="authStore.loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ authStore.loading ? 'กำลังสมัคร…' : 'สมัครสมาชิก' }}
          </button>
        </form>
      </div>

      <p class="text-center text-xs text-surface-600 mt-5 flex items-center justify-center gap-1.5">
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
        </svg>
        รหัสผ่าน bcrypt-12 · JWT HS256 · ไม่เก็บข้อมูลดิบ
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const router    = useRouter()
const authStore = useAuthStore()

const form = reactive({
  display_name: '', email: '', username: '',
  password: '', confirm: '', agree: false,
})
const errors    = reactive({ email: '', username: '', password: '', confirm: '', agree: '' })
const error     = ref('')
const pwdErrors = ref<string[]>([])
const showPwd   = ref(false)

onMounted(() => { if (authStore.isLoggedIn) router.replace('/dashboard') })

function inputClass(hasError: boolean) {
  return hasError ? 'border-bear/60 focus:border-bear' : 'border-surface-700 focus:border-primary-500'
}

// Password strength
const pwdStrength = computed(() => {
  const p = form.password
  let score = 0
  if (p.length >= 8)  score++
  if (p.length >= 12) score++
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++
  if (/\d/.test(p))    score++
  if (/[^a-zA-Z0-9]/.test(p)) score = Math.min(4, score + 1)
  const labels = ['', 'อ่อนมาก', 'อ่อน', 'ปานกลาง', 'แข็งแกร่ง']
  return { score: Math.min(4, score), label: labels[Math.min(4, score)] }
})

function validate(): boolean {
  Object.assign(errors, { email: '', username: '', password: '', confirm: '', agree: '' })
  let ok = true
  if (!/^[^@]+@[^@]+\.[^@]+$/.test(form.email)) {
    errors.email = 'รูปแบบอีเมลไม่ถูกต้อง'; ok = false
  }
  if (form.username.length < 3) {
    errors.username = 'ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'; ok = false
  } else if (!/^[a-zA-Z0-9_\-]+$/.test(form.username)) {
    errors.username = 'ใช้ได้เฉพาะ a-z 0-9 _ -'; ok = false
  }
  if (form.password.length < 8) {
    errors.password = 'รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร'; ok = false
  }
  if (form.password !== form.confirm) {
    errors.confirm = 'รหัสผ่านไม่ตรงกัน'; ok = false
  }
  if (!form.agree) {
    errors.agree = 'กรุณายอมรับข้อกำหนด'; ok = false
  }
  return ok
}

async function handleSubmit() {
  error.value = ''; pwdErrors.value = []
  if (!validate()) return
  const result = await authStore.register(
    form.email, form.username, form.password,
    form.display_name || undefined,
  )
  if (result.ok) {
    router.push('/dashboard')
  } else {
    const detail = result.error
    if (typeof detail === 'object' && detail?.errors) {
      error.value     = detail.message || 'รหัสผ่านไม่ผ่าน'
      pwdErrors.value = detail.errors
    } else {
      error.value = String(detail)
    }
  }
}
</script>

<style scoped>
.slide-alert-enter-active { transition: all .2s ease; }
.slide-alert-leave-active { transition: all .15s ease; }
.slide-alert-enter-from   { opacity: 0; transform: translateY(-8px); }
.slide-alert-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
