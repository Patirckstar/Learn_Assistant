import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'voice_settings'

export interface VoiceSettings {
  ttsEnabled: boolean   // 语音播报开关
  sttEnabled: boolean   // 语音输入开关
}

function loadSettings(): VoiceSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return { ttsEnabled: true, sttEnabled: true } // 默认开启
}

function saveSettings(s: VoiceSettings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
}

export const useVoiceStore = defineStore('voice', () => {
  const settings = ref<VoiceSettings>(loadSettings())

  const ttsEnabled = computed(() => settings.value.ttsEnabled)
  const sttEnabled = computed(() => settings.value.sttEnabled)

  function toggleTTS() {
    settings.value.ttsEnabled = !settings.value.ttsEnabled
    saveSettings(settings.value)
  }

  function toggleSTT() {
    settings.value.sttEnabled = !settings.value.sttEnabled
    saveSettings(settings.value)
  }

  return { settings, ttsEnabled, sttEnabled, toggleTTS, toggleSTT }
})
