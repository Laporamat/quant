<template>
  <div class="max-w-2xl mx-auto space-y-5 animate-fade-in">
    <SectionHeader title="โปรไฟล์ของฉัน" description="จัดการข้อมูลบัญชีและความปลอดภัย" />

    <!-- Profile card -->
    <div class="glass p-6 space-y-4">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 rounded-2xl bg-primary-600/20 border border-primary-600/30 flex items-center justify-center text-2xl font-bold text-primary-300">
          {{ (authStore.displayName)[0]?.toUpperCase() }}
        </div>
        <div>
          <p class="font-semibold text-surface-100">{{ authStore.displayName }}</p>
          <p class="text-sm text-surface-400">{{ user?.email }}</p>
          <span class="badge badge-blue text-xs mt-1">{{ user?.role }}</span>
        </div>
      </div>

      <!-- Edit display name -->
      <div class="space-y-2 pt-2 border-t border-surface-700/50">
        <label class="text-xs font-medium text-surface-300">ชื่อที่แสดง</label>
        <div class="flex gap-2">
          <input v-model="displayName" type="text" maxlength="64"
            class="flex-1 bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-xl px-3 py-2 outline-none focus:border-primary-500 transition-colors" />
          <button @click="saveName" :disabled="savingName" class="btn-primary text-sm px-4">
            {{ savingName ? '…' : 'บันทึก' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Change password -->
    <div class="glass p-6 space-y-4">
      <h3 class="text-sm font-semibold text-surface-200">เปลี่ยนรหัสผ่าน</h3>
      <div v-if="pwdMsg" class="text-sm px-3 py-2 rounded-lg"
        :class="pwdMsg.ok ? 'bg-bull/10 text-bull' : 'bg-bear/10 text-bear'">
        {{ pwdMsg.text }}
      </div>
      <div class="space-y-3">
        <div class="space-y-1">
          <label class="text-xs text-surface-400">รหัสผ่านปัจจุบัน</label>
          <input v-model="pwd.current" type="password"
            class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-xl px-3 py-2 outline-none focus:border-primary-500 transition-colors" />
        </div>
        <div class="space-y-1">
          <label class="text-xs text-surface-400">รหัสผ่านใหม่</label>
          <input v-model="pwd.new" type="password"
            class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-xl px-3 py-2 outline-none focus:border-primary-500 transition-colors" />
        </div>
        <div class="space-y-1">
          <label class="text-xs text-surface-400">ยืนยันรหัสผ่านใหม่</label>
          <input v-model="pwd.confirm" type="password"
            class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-xl px-3 py-2 outline-none focus:border-primary-500 transition-colors" />
        </div>
        <button @click="changePwd" :disabled="savingPwd" class="btn-primary w-full">
          {{ savingPwd ? 'กำลังเปลี่ยน…' : 'เปลี่ยนรหัสผ่าน' }}
        </button>
      </div>
    </div>

    <!-- Sessions -->
    <div class="glass p-6 space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-surface-200">Sessions ที่ใช้งานอยู่</h3>
        <button @click="revokeAll" class="text-xs text-bear hover:text-bear/80 transition-colors">
          ยกเลิกทั้งหมด
        </button>
      </div>
      <div v-for="s in sessions" :key="s.id"
        class="flex items-start justify-between py-2.5 border-b border-surface-700/30 last:border-0">
        <div>
          <p class="text-xs text-surface-200">{{ s.device_info || 'Unknown device' }}</p>
          <p class="text-xs text-surface-500 mt-0.5">
            IP: {{ s.ip_address }} · ใช้ล่าสุด {{ formatDate(s.last_used_at) }}
          </p>
        </div>
        <button @click="revokeOne(s.id)"
          class="text-xs text-bear/70 hover:text-bear transition-colors shrink-0 ml-4">
          ยกเลิก
        </button>
      </div>
      <div v-if="!sessions.length" class="text-xs text-surface-500 text-center py-3">
        ไม่พบ session ที่ใช้งาน
      </div>
    </div>

    <!-- Audit log -->
    <div class="glass p-6 space-y-3">
      <h3 class="text-sm font-semibold text-surface-200">ประวัติการเข้าสู่ระบบ</h3>
      <DataTable :columns="auditCols" :rows="auditLogs" :page-size="10" />
    </div>

    <!-- Logout -->
    <button @click="logout" class="w-full py-2.5 rounded-xl border border-bear/30 text-bear hover:bg-bear/10 transition-all text-sm font-medium">
      ออกจากระบบ
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import SectionHeader from '@/components/shared/SectionHeader.vue'
import DataTable     from '@/components/shared/DataTable.vue'
import { useAuthStore } from '@/stores/authStore'
import { authApi, type Session } from '@/api/authApi'
import { useToastStore } from '@/stores/appStore'

const authStore = useAuthStore()
const toast     = useToastStore()
const router    = useRouter()

const user        = computed(() => authStore.user)
const displayName = ref(authStore.displayName)
const savingName  = ref(false)
const sessions    = ref<Session[]>([])
const auditLogs   = ref<Record<string, unknown>[]>([])

const pwd     = ref({ current: '', new: '', confirm: '' })
const pwdMsg  = ref<{ ok: boolean; text: string } | null>(null)
const savingPwd = ref(false)

const auditCols = [
  { key: 'event',      label: 'Event' },
  { key: 'ip_address', label: 'IP' },
  { key: 'created_at', label: 'เวลา', format: (v: unknown) => formatDate(String(v)) },
]

function formatDate(d: string) {
  return dayjs(d).format('DD/MM/YY HH:mm')
}

async function saveName() {
  savingName.value = true
  try {
    await authStore.updateProfile(displayName.value)
  } finally {
    savingName.value = false
  }
}

async function changePwd() {
  pwdMsg.value = null
  if (pwd.value.new !== pwd.value.confirm) {
    pwdMsg.value = { ok: false, text: 'รหัสผ่านใหม่ไม่ตรงกัน' }
    return
  }
  savingPwd.value = true
  try {
    await authApi.changePassword(pwd.value.current, pwd.value.new)
    pwdMsg.value = { ok: true, text: 'เปลี่ยนรหัสผ่านสำเร็จ กรุณาเข้าสู่ระบบใหม่' }
    pwd.value = { current: '', new: '', confirm: '' }
    setTimeout(() => { authStore.logout(); router.push('/login') }, 2000)
  } catch (e: any) {
    pwdMsg.value = { ok: false, text: e.response?.data?.detail || 'เกิดข้อผิดพลาด' }
  } finally {
    savingPwd.value = false
  }
}

async function revokeOne(id: string) {
  await authApi.revokeSession(id)
  sessions.value = sessions.value.filter(s => s.id !== id)
  toast.success('ยกเลิก session แล้ว')
}

async function revokeAll() {
  await authApi.revokeAllSessions()
  sessions.value = []
  toast.success('ยกเลิก sessions ทั้งหมดแล้ว')
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(async () => {
  const [sRes, aRes] = await Promise.allSettled([
    authApi.sessions(),
    authApi.auditLog(20),
  ])
  if (sRes.status === 'fulfilled') sessions.value = sRes.value.data.sessions
  if (aRes.status === 'fulfilled') auditLogs.value = aRes.value.data.logs
})
</script>
