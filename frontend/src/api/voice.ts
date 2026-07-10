import request from '@/api/request'

export interface VoiceResponse {
  action: 'navigate' | 'chat' | 'unknown'
  target: string
  target_name: string
  reply: string
}

export function sendVoiceCommand(text: string) {
  return request.post<VoiceResponse>('/api/voice/command', { text })
}
