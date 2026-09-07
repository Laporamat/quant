import { http } from './client'

export interface AuthUser {
  id: string; email: string; username: string; display_name: string
  role: string; is_active: boolean; is_verified: boolean
  last_login_at: string | null; created_at: string
}
export interface TokenResponse { access_token: string; token_type: string; expires_in: number; user: AuthUser }
export interface Session { id: string; device_info: string; ip_address: string; expires_at: string; last_used_at: string }

export const authApi = {
  providers: () => http.get<{ providers: { id:string;name:string;enabled:boolean;icon:string }[] }>('/auth/providers'),
  register:  (email: string, username: string, password: string, display_name?: string) =>
    http.post<TokenResponse>('/auth/register', { email, username, password, display_name }),
  login:     (login: string, password: string) => http.post<TokenResponse>('/auth/login', { login, password }),
  logout:    () => http.post('/auth/logout', {}).catch(() => {}),
  refresh:   () => http.post<TokenResponse>('/auth/refresh', {}),
  me:        () => http.get<AuthUser>('/auth/me'),
  updateProfile: (display_name: string) => http.put<AuthUser>('/auth/me', { display_name }),
  changePassword: (current_password: string, new_password: string) =>
    http.post('/auth/change-password', { current_password, new_password }),
  sessions: () => http.get<{ sessions: Session[] }>('/auth/sessions'),
  revokeSession: (id: string) => http.delete(`/auth/sessions/${id}`),
  revokeAll: () => http.delete('/auth/sessions'),
  auditLog:  (limit = 20) => http.get<{ logs: Record<string, unknown>[] }>(`/auth/audit?limit=${limit}`),
}
