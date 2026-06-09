<template>
  <div class="chat-view">
    <!-- 主聊天区域（垂直布局：消息区 + 输入区） -->
    <div class="chat-main">
      <!-- 消息区域 -->
      <div class="messages-area" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h2>开始智能对话</h2>
          <p class="welcome-subtitle">告诉我关于您的学习情况，AI 将为您构建个性化学习画像</p>
          <div class="suggestion-chips">
            <button
              v-for="suggestion in suggestions"
              :key="suggestion.text"
              class="chip"
              @click="quickSend(suggestion.text)"
            >
              <span class="chip-icon">{{ suggestion.icon }}</span>
              <span class="chip-text">{{ suggestion.text }}</span>
            </button>
          </div>
        </div>

        <div
          v-for="(message, index) in messages"
          :key="message.id"
          class="message"
          :class="[message.role, { 'streaming': streaming && index === messages.length - 1 && message.role === 'assistant' }]"
          :style="{ animationDelay: index * 0.05 + 's' }"
        >
          <div class="message-avatar-wrapper">
            <div class="message-avatar" :class="message.role">
              {{ message.role === 'user' ? '👤' : '🤖' }}
            </div>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(message.content)"></div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>

        <div v-if="loading && !streaming" class="message assistant">
          <div class="message-avatar-wrapper">
            <div class="message-avatar assistant">🤖</div>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span class="typing-dots">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区（固定在底部） -->
      <div class="input-area">
        <div class="input-container">
          <textarea
            v-model="inputMessage"
            @keydown.enter.exact="sendMessage"
            placeholder="输入您的消息..."
            rows="1"
            ref="inputRef"
            @input="autoResize"
          ></textarea>
          <button
            class="send-btn"
            @click="sendMessage"
            :disabled="!inputMessage.trim() || loading"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 画像面板 -->
    <div class="profile-panel" :class="{ collapsed: profileCollapsed }">
      <button class="profile-toggle" @click="profileCollapsed = !profileCollapsed">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        <span v-if="profileCollapsed">画像</span>
      </button>

      <div v-if="!profileCollapsed" class="profile-body">
        <div class="profile-header">
          <h3>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            学习画像
          </h3>
          <span class="profile-version" v-if="profileVersion">v{{ profileVersion }}</span>
        </div>

        <!-- 仪表盘：综合评分 -->
        <div class="gauge-wrapper">
          <ProfileGauge :dimensions="profileDimensions" />
        </div>

        <!-- 雷达图 -->
        <div class="radar-wrapper">
          <div class="section-label">维度分析</div>
          <ProfileRadar :dimensions="profileDimensions" />
        </div>

        <!-- 维度卡片 -->
        <div class="dim-cards">
          <div
            v-for="(dim, key) in profileDimensions"
            :key="key"
            class="dim-card"
          >
            <div class="dim-card-header">
              <span class="dim-card-label">{{ dimensionLabels[key] }}</span>
              <span class="dim-card-value">{{ dim?.value || '-' }}</span>
            </div>
            <div class="dim-card-bar">
              <div class="dim-card-fill" :style="{ width: ((dim?.confidence || 0) * 100) + '%' }"></div>
            </div>
            <div class="dim-card-conf">
              置信度 {{ Math.round((dim?.confidence || 0) * 100) }}%
            </div>
          </div>
        </div>

        <button class="edit-profile-btn" @click="showEditModal = true">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
          手动修正维度
        </button>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
          <div class="modal">
            <div class="modal-header">
              <h3>手动修正画像</h3>
              <button class="modal-close" @click="showEditModal = false">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label>维度</label>
                <select v-model="editDimension">
                  <option v-for="(label, key) in dimensionLabels" :key="key" :value="key">
                    {{ label }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>值</label>
                <input v-model="editValue" type="text" placeholder="输入新的维度值" />
              </div>
            </div>
            <div class="modal-footer">
              <button class="modal-cancel" @click="showEditModal = false">取消</button>
              <button class="modal-confirm" @click="updateProfile">确认更新</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '../stores/chat'
import { useProfileStore } from '../stores/profile'
import MarkdownIt from 'markdown-it'
import ProfileRadar from '../components/profile/ProfileRadar.vue'
import ProfileGauge from '../components/profile/ProfileGauge.vue'

const chatStore = useChatStore()
const profileStore = useProfileStore()

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const streaming = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)

const profileDimensions = ref({})
const profileVersion = ref(0)
const profileCollapsed = ref(false)

// 同步 store 画像变化
watch(() => profileStore.dimensions, (val) => {
  profileDimensions.value = { ...val }
}, { deep: true })

const showEditModal = ref(false)
const editDimension = ref('knowledge_base')
const editValue = ref('')

const dimensionLabels = {
  knowledge_base: '知识基础',
  cognitive_style: '认知风格',
  error_patterns: '易错点偏好',
  learning_preference: '学习偏好',
  learning_pace: '学习节奏',
  goal_orientation: '目标导向'
}

const suggestions = [
  { text: '我是计算机专业大二学生', icon: '🎓' },
  { text: '我想学习数据结构', icon: '📚' },
  { text: '帮我规划学习路线', icon: '🗺️' },
  { text: '我编程基础比较薄弱', icon: '💪' }
]

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
})

const renderMarkdown = (text) => {
  return md.render(text || '')
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const autoResize = () => {
  const el = inputRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }
}

const quickSend = (text) => {
  inputMessage.value = text
  sendMessage()
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const content = inputMessage.value
  const userMessage = {
    id: 'msg-' + Date.now(),
    role: 'user',
    content: content,
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMessage)
  inputMessage.value = ''
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  loading.value = true
  streaming.value = false

  await scrollToBottom()

  let assistantMessage = null
  const ensureAssistantMessage = () => {
    if (!assistantMessage) {
      assistantMessage = reactive({
        id: 'msg-' + (Date.now() + 1),
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      })
      messages.value.push(assistantMessage)
      loading.value = false
      streaming.value = true
    }
    return assistantMessage
  }

  try {
    const response = await chatStore.sendMessage(content, (token, full) => {
      ensureAssistantMessage().content = full
    })

    const final = ensureAssistantMessage()
    final.content = response.content || final.content

    if (response.profile_update) {
      profileDimensions.value = { ...profileDimensions.value, ...response.profile_update }
    }
  } catch (error) {
    console.error('Failed to send message:', error)
    ensureAssistantMessage().content = '抱歉，发送消息时出现错误，请稍后重试。'
  } finally {
    loading.value = false
    streaming.value = false
    await scrollToBottom()
  }
}

const updateProfile = async () => {
  try {
    await profileStore.updateDimension(editDimension.value, editValue.value)
    profileDimensions.value = { ...profileStore.dimensions }
    showEditModal.value = false
  } catch (error) {
    console.error('Failed to update profile:', error)
  }
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

onMounted(async () => {
  await profileStore.fetchProfile()
  profileDimensions.value = { ...profileStore.dimensions }
  profileVersion.value = profileStore.version || 0

  if (!chatStore.currentSession) {
    await chatStore.createSession('新对话')
  }
})
</script>

<style scoped>
/* ===== 布局 ===== */
.chat-view {
  display: flex;
  height: 100%;
  background: #f5f6f8;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ===== 消息区域 ===== */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ===== 欢迎屏 ===== */
.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
}

.welcome-icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  background: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  margin-bottom: 24px;
}

.welcome-screen h2 {
  font-size: 22px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 8px;
}

.welcome-subtitle {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 32px;
  max-width: 400px;
}

.suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  max-width: 500px;
}

.chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 9999px;
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.chip:hover {
  border-color: #2563eb;
  color: #2563eb;
  background: #f5f8ff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
  transform: translateY(-1px);
}

.chip-icon {
  font-size: 15px;
}

/* ===== 消息 ===== */
.message {
  display: flex;
  gap: 10px;
  padding: 6px 40px;
  max-width: 100%;
  animation: messageIn 0.25s ease-out;
  animation-fill-mode: both;
}

.message.user {
  flex-direction: row-reverse;
}

@keyframes messageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar-wrapper {
  flex-shrink: 0;
  margin-top: 4px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}

.message-avatar.user {
  background: #2563eb;
}

.message-avatar.assistant {
  background: #ffffff;
  border: 1px solid #e5e7eb;
}

.message-content {
  max-width: 640px;
  display: flex;
  flex-direction: column;
}

.message-text {
  padding: 10px 16px;
  line-height: 1.7;
  font-size: 14px;
  color: #111827;
}

.message.user .message-text {
  background: #2563eb;
  color: #ffffff;
  border-radius: 18px 18px 4px 18px;
  font-size: 14px;
}

.message.assistant .message-text {
  background: transparent;
  border-radius: 4px 18px 18px 18px;
}

.message.streaming .message-text {
  border-left: 2px solid #2563eb;
}

.message-time {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
  padding: 0 12px;
}

.message.user .message-time {
  text-align: right;
}

/* Markdown */
.message-text :deep(p) {
  margin-bottom: 6px;
}
.message-text :deep(p:last-child) {
  margin-bottom: 0;
}
.message-text :deep(code) {
  background: rgba(0,0,0,0.06);
  padding: 1px 5px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
}
.message.user .message-text :deep(code) {
  background: rgba(255,255,255,0.2);
  color: #fff;
}
.message-text :deep(pre) {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px;
  overflow-x: auto;
  margin: 10px 0;
}
.message.user .message-text :deep(pre) {
  background: rgba(255,255,255,0.1);
  border-color: transparent;
}
.message-text :deep(pre code) {
  background: none;
  padding: 0;
}
.message-text :deep(strong) {
  font-weight: 600;
}
.message-text :deep(ul),
.message-text :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}
.message-text :deep(li) {
  margin-bottom: 3px;
}

/* 打字指示 */
.typing-indicator {
  padding: 12px 16px;
}

.typing-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.typing-dots span {
  width: 7px;
  height: 7px;
  background: #d1d5db;
  border-radius: 50%;
  animation: typing 1.4s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; background: #2563eb; }
}

/* ===== 输入区 ===== */
.input-area {
  padding: 16px 40px 24px;
  flex-shrink: 0;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 4px 4px 4px 16px;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.input-container:focus-within {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input-container textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  max-height: 120px;
  background: transparent;
  color: #111827;
  padding: 8px 0;
}

.input-container textarea::placeholder {
  color: #9ca3af;
}

.send-btn {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: #2563eb;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.send-btn:hover:not(:disabled) {
  background: #1d4ed8;
  transform: scale(1.05);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  transform: none;
}

/* ===== 画像面板 ===== */
.profile-panel {
  width: 280px;
  background: #ffffff;
  border-left: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
  transition: width 0.25s ease;
}

.profile-panel.collapsed {
  width: 44px;
}

.profile-toggle {
  position: absolute;
  top: 12px;
  left: 8px;
  z-index: 2;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}

.profile-panel.collapsed .profile-toggle {
  width: 30px;
  height: 30px;
  left: 7px;
  font-size: 11px;
  flex-direction: column;
}

.profile-toggle:hover {
  background: #eff6ff;
  color: #2563eb;
  border-color: #2563eb;
}

.profile-body {
  padding: 14px 16px 20px;
  overflow-y: auto;
  height: 100%;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  padding-top: 6px;
}

.profile-header h3 {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #111827;
}

.profile-header h3 svg {
  color: #2563eb;
}

.profile-version {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 9999px;
  background: #eff6ff;
  color: #2563eb;
  font-weight: 500;
}

.gauge-wrapper {
  background: #f9fafb;
  border-radius: 10px;
  margin-bottom: 10px;
  border: 1px solid #f3f4f6;
  overflow: hidden;
}

.radar-wrapper {
  background: #f9fafb;
  border-radius: 10px;
  padding: 8px;
  border: 1px solid #f3f4f6;
  margin-bottom: 10px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 2px 4px 0;
}

.dim-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.dim-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid #f3f4f6;
}

.dim-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.dim-card-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
}

.dim-card-value {
  font-size: 12px;
  font-weight: 700;
  color: #111827;
  background: #ffffff;
  padding: 1px 8px;
  border-radius: 9999px;
  border: 1px solid #e5e7eb;
}

.dim-card-bar {
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}

.dim-card-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #60a5fa);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.dim-card-conf {
  font-size: 10px;
  color: #9ca3af;
  text-align: right;
}

.edit-profile-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  background: transparent;
  color: #9ca3af;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-profile-btn:hover {
  background: #eff6ff;
  border-color: #2563eb;
  color: #2563eb;
}

/* ===== 弹窗 ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #ffffff;
  border-radius: 12px;
  width: 400px;
  max-width: 92%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.12);
  border: 1px solid #e5e7eb;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}

.modal-close:hover {
  background: #fee2e2;
  color: #ef4444;
}

.modal-body {
  padding: 20px 24px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 6px;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 9px 12px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  background: #ffffff;
  color: #111827;
  outline: none;
  transition: border-color 0.15s;
}

.form-group select:focus,
.form-group input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 24px 20px;
}

.modal-cancel {
  padding: 8px 18px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.modal-cancel:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.modal-confirm {
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.modal-confirm:hover {
  background: #1d4ed8;
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s;
}
.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: all 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: translateY(16px) scale(0.97);
  opacity: 0;
}
</style>
