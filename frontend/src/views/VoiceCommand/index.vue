<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="vc-overlay" @click.self="close">
        <div class="vc-modal">
          <!-- Header -->
          <div class="vc-header">
            <div class="vc-header-left">
              <svg class="vc-header-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
              <span>语音指令</span>
            </div>
            <button class="vc-close-btn" @click="close">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Content -->
          <div class="vc-body">
            <!-- 输入区域 -->
            <div class="vc-input-area">
              <div class="vc-text-display">
                <textarea
                  ref="textInputRef"
                  v-model="inputText"
                  class="vc-textarea"
                  :placeholder="isListening ? '正在聆听...' : '说出你的指令，或直接输入文字'"
                  rows="3"
                  @keydown.enter.exact="submitText"
                ></textarea>
              </div>

              <div class="vc-mic-row">
                <button
                  class="vc-mic-btn"
                  :class="{ listening: isListening }"
                  @mousedown.prevent="startListen"
                  @mouseup.prevent="stopListen"
                  @mouseleave.prevent="stopListen"
                  @touchstart.prevent="startListen"
                  @touchend.prevent="stopListen"
                >
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                  </svg>
                </button>
                <span class="vc-mic-hint">{{ isListening ? '松开完成录音' : '按住说话' }}</span>
              </div>

              <button
                class="vc-submit-btn"
                :disabled="!inputText.trim() || processing"
                @click="submitText"
              >
                <span v-if="processing" class="vc-spinner"></span>
                <span v-else>发送指令</span>
              </button>
            </div>

            <!-- 响应区域 -->
            <Transition name="reply-slide">
              <div v-if="reply" class="vc-reply" :class="replyClass">
                <div class="vc-reply-icon">
                  <svg v-if="replyAction === 'navigate'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="9 18 15 12 9 6"/>
                  </svg>
                  <svg v-else-if="replyAction === 'chat'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                </div>
                <span class="vc-reply-text">{{ reply }}</span>
                <button
                  v-if="voiceStore.ttsEnabled && ttsSupported && !ttsSpeaking"
                  class="vc-reply-speak-btn"
                  @click="speakReply"
                  title="朗读回复"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                  </svg>
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { sendVoiceCommand } from '@/api/voice'
import { useVoiceStore } from '@/stores/voice'
import { useTTS } from '@/composables/useTTS'
import type { VoiceResponse } from '@/api/voice'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'close'): void
}>()

const router = useRouter()
const voiceStore = useVoiceStore()
const { speaking: ttsSpeaking, isSupported: isTTSSupported, speak: ttsSpeak } = useTTS()
const ttsSupported = isTTSSupported()

const inputText = ref('')
const isListening = ref(false)
const processing = ref(false)
const reply = ref('')
const replyAction = ref('')
const textInputRef = ref<HTMLTextAreaElement>()

// 语音识别
let recognition: any = null
const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

function initRecognition() {
  if (!SpeechRecognitionAPI) return
  if (recognition) return

  recognition = new SpeechRecognitionAPI()
  recognition.lang = 'zh-CN'
  recognition.interimResults = false
  recognition.continuous = false

  recognition.onresult = (event: any) => {
    const transcript = event.results[0][0].transcript
    inputText.value = transcript
  }

  recognition.onerror = (event: any) => {
    console.error('语音识别错误:', event.error)
    isListening.value = false
    if (event.error === 'not-allowed') {
      inputText.value = ''
    }
  }

  recognition.onend = () => {
    isListening.value = false
  }
}

function startListen() {
  if (!SpeechRecognitionAPI) {
    inputText.value = ''  // 浏览器不支持，允许手动输入
    return
  }
  initRecognition()
  try {
    recognition.start()
    isListening.value = true
    reply.value = ''
  } catch (e) {
    // 可能已在运行
  }
}

function stopListen() {
  if (recognition && isListening.value) {
    try {
      recognition.stop()
    } catch (e) {
      // ignore
    }
    isListening.value = false
  }
}

async function submitText() {
  const text = inputText.value.trim()
  if (!text || processing.value) return

  processing.value = true
  reply.value = ''

  try {
    const res = await sendVoiceCommand(text)
    const data = res.data as VoiceResponse
    reply.value = data.reply
    replyAction.value = data.action

    if (data.action === 'navigate' && data.target) {
      // 延迟一下让用户看到提示，然后跳转并关闭
      setTimeout(() => {
        router.push(data.target)
        close()
      }, 1200)
    }

    // 自动朗读回复（TTS 开启时）
    if (voiceStore.ttsEnabled && ttsSupported) {
      ttsSpeak(data.reply)
    }
  } catch (e: any) {
    reply.value = e.response?.data?.detail || '请求失败，请检查网络连接。'
    replyAction.value = 'unknown'
  } finally {
    processing.value = false
  }
}

function close() {
  inputText.value = ''
  reply.value = ''
  replyAction.value = ''
  processing.value = false
  isListening.value = false
  if (recognition) {
    try { recognition.stop() } catch (e) { /* ignore */ }
  }
  emit('update:visible', false)
  emit('close')
}

const replyClass = computed(() => {
  return `reply-${replyAction.value}`
})

function speakReply() {
  if (reply.value && voiceStore.ttsEnabled) {
    ttsSpeak(reply.value)
  }
}

// 当弹窗打开时自动聚焦
defineExpose({ focusInput: () => nextTick(() => textInputRef.value?.focus()) })
</script>

<style scoped>
/* ===== Overlay ===== */
.vc-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(2px);
}

/* ===== Modal ===== */
.vc-modal {
  background: var(--color-surface, #fff);
  border-radius: 16px;
  width: 480px;
  max-width: calc(100vw - 40px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ===== Header ===== */
.vc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.vc-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-heading, #1f2937);
}

.vc-header-icon {
  color: var(--color-primary, #3b82f6);
}

.vc-close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--color-primary-light, #eff6ff);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary, #6b7280);
  transition: all 0.15s;
}

.vc-close-btn:hover {
  background: var(--color-primary, #3b82f6);
  color: #fff;
}

/* ===== Body ===== */
.vc-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== Input ===== */
.vc-input-area {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.vc-text-display {
  position: relative;
}

.vc-textarea {
  width: 100%;
  min-height: 72px;
  padding: 12px 14px;
  border: 2px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--color-text-heading, #1f2937);
  background: var(--color-bg, #f9fafb);
  resize: none;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
  box-sizing: border-box;
}

.vc-textarea:focus {
  border-color: var(--color-primary, #3b82f6);
  background: #fff;
}

.vc-textarea::placeholder {
  color: #9ca3af;
}

/* ===== Mic ===== */
.vc-mic-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.vc-mic-btn {
  width: 64px;
  height: 64px;
  border: none;
  border-radius: 50%;
  background: var(--color-primary-light, #eff6ff);
  color: var(--color-primary, #3b82f6);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 2px 12px rgba(59, 130, 246, 0.15);
}

.vc-mic-btn:hover {
  transform: scale(1.06);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
}

.vc-mic-btn:active,
.vc-mic-btn.listening {
  background: #ef4444;
  color: #fff;
  box-shadow: 0 0 0 8px rgba(239, 68, 68, 0.2);
  animation: pulse-ring 1.2s ease-out infinite;
}

@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.35); }
  100% { box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }
}

.vc-mic-hint {
  font-size: 13px;
  color: var(--color-text-secondary, #6b7280);
  user-select: none;
}

/* ===== Submit ===== */
.vc-submit-btn {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: var(--color-primary, #3b82f6);
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.vc-submit-btn:hover:not(:disabled) {
  background: #2563eb;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.35);
}

.vc-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.vc-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== Reply ===== */
.vc-reply {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-heading, #1f2937);
}

.vc-reply.reply-navigate {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
}

.vc-reply.reply-chat {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
}

.vc-reply.reply-unknown {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.vc-reply-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.vc-reply-text {
  flex: 1;
}

.vc-reply-speak-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.6);
  color: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  opacity: 0.6;
}

.vc-reply-speak-btn:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.9);
}

.vc-reply.reply-navigate .vc-reply-icon { color: #10b981; }
.vc-reply.reply-chat .vc-reply-icon { color: #3b82f6; }
.vc-reply.reply-unknown .vc-reply-icon { color: #ef4444; }

/* ===== Transitions ===== */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.25s ease;
}

.modal-fade-enter-active .vc-modal,
.modal-fade-leave-active .vc-modal {
  transition: transform 0.25s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .vc-modal {
  transform: scale(0.92) translateY(16px);
}

.modal-fade-leave-to .vc-modal {
  transform: scale(0.92) translateY(16px);
}

.reply-slide-enter-active {
  transition: all 0.3s ease;
}

.reply-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
