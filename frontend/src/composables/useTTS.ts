import { ref } from 'vue'

/** 文本转语音 composable — 封装浏览器 SpeechSynthesis API */
export function useTTS() {
    const speaking = ref(false)

    /** 检查是否支持 */
    const isSupported = (): boolean => {
        return typeof window !== 'undefined' && 'speechSynthesis' in window
    }

    /** 获取中文语音 */
    function getVoice(): SpeechSynthesisVoice | null {
        if (!isSupported()) return null
        const voices = window.speechSynthesis.getVoices()
        // 优先选中文女声
        let v = voices.find((v) => v.lang.startsWith('zh') && v.name.includes('Female'))
        if (!v) v = voices.find((v) => v.lang.startsWith('zh'))
        if (!v) v = voices.find((v) => v.lang === 'zh-CN')
        return v || null
    }

    /**
     * 朗读文本
     * @param text 要朗读的文本
     * @param rate 语速，默认 0.9
     * @returns Promise，朗读完成后 resolve
     */
    function speak(text: string, rate: number = 0.9): Promise<void> {
        return new Promise((resolve) => {
            if (!isSupported() || !text) {
                resolve()
                return
            }

            // 取消当前正在朗读的内容
            window.speechSynthesis.cancel()

            const utterance = new SpeechSynthesisUtterance(text)
            const voice = getVoice()
            if (voice) utterance.voice = voice
            utterance.rate = rate
            utterance.pitch = 1.0
            utterance.volume = 1.0

            utterance.onstart = () => {
                speaking.value = true
            }

            utterance.onend = () => {
                speaking.value = false
                resolve()
            }

            utterance.onerror = () => {
                speaking.value = false
                resolve()
            }

            window.speechSynthesis.speak(utterance)
        })
    }

    /** 停止朗读 */
    function stop() {
        if (isSupported()) {
            window.speechSynthesis.cancel()
            speaking.value = false
        }
    }

    return { speaking, isSupported, speak, stop }
}
