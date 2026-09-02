<template>
  <div class="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-5 animate-fade-in">
    <div class="relative">
      <span class="text-[120px] font-black text-surface-800 select-none leading-none">404</span>
      <div class="absolute inset-0 flex items-center justify-center">
        <svg class="w-16 h-16 text-primary-500 opacity-60" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      </div>
    </div>
    <div class="space-y-2">
      <h1 class="text-2xl font-bold text-surface-200">Page Not Found</h1>
      <p class="text-surface-400 text-sm max-w-sm">The page you're looking for doesn't exist. It may have been moved or the URL is incorrect.</p>
    </div>
    <RouterLink to="/dashboard" class="btn-primary px-6 py-2.5">
      ← Back to Dashboard
    </RouterLink>
  </div>
</template>
