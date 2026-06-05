<template>
  <div class="chat-view">
    <div class="chat-container">
      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">💬</div>
          <h3>开始对话</h3>
          <p>告诉我关于您的学习情况，我将为您构建个性化画像</p>
        </div>
        <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
          <div class="message-avatar">
            {{ message.role === 'user' ? '👤' : '🤖' }}
          </div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(message.content)"></div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-container">
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            @keydown.enter.exact="sendMessage"
            placeholder="输入您的消息..."
            rows="1"
            ref="inputRef"
          ></textarea>
          <button class="send-btn" @click="sendMessage" :disabled="!inputMessage.trim() || loading">
            发送
          </button>
        </div>
      </div>
    </div>

    <!-- 画像面板 -->
    <div class="profile-panel">
      <h3>学习画像</h3>
      <div class="radar-chart" ref="radarChart"></div>
      <div class="profile-details">
        <div v-for="(dim, key) in profileDimensions" :key="key" class="profile-item">
          <span class="label">{{ dimensionLabels[key] }}</span>
          <span class="value">{{ dim.value }}</span>
          <div class="confidence-bar">
            <div class="confidence-fill" :style="{ width: (dim.confidence * 100) + '%' }"></div>
          </div>
        </div>
      </div>
      <button class="edit-btn" @click="showEditModal = true">手动修正</button>
    </div>

    <!-- 编辑弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click="showEditModal = false">
      <div class="modal" @click.stop>
        <h3>修正画像</h3>
        <div class="form-group">
          <label>选择维度</label>
          <select v-model="editDimension">
            <option v-for="(label, key) in dimensionLabels" :key="key" :value="key">
              {{ label }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>设置值</label>
          <input v-model="editValue" type="text" placeholder="输入维度值">
        </div>
        <div class="modal-actions">
          <button class="cancel-btn" @click="showEditModal = false">取消</button>
          <button class="confirm-btn" @click="updateProfile">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '../stores/chat'
import { useProfileStore } from '../stores/profile'
import MarkdownIt from 'markdown-it'

const chatStore = useChatStore()
const profileStore = useProfileStore()

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)

const showEditModal = ref(false)
const editDimension = ref('knowledge_base')
const editValue = ref('')

const profileDimensions = ref({})
const dimensionLabels = {
  knowledge_base: '知识基础',
  cognitive_style: '认知风格',
  error_patterns: '易错点偏好',
  learning_preference: '学习偏好',
  learning_pace: '学习节奏',
  goal_orientation: '目标导向'
}

const md = new MarkdownIt()

const renderMarkdown = (text) => {
  return md.render(text)
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const content = inputMessage.value
  const userMessage = {
    id: Date.now(),
    role: 'user',
    content: content,
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMessage)
  inputMessage.value = ''
  loading.value = true

  await scrollToBottom()

  try {
    const response = await chatStore.sendMessage(content)
    const assistantMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: response.content,
      timestamp: new Date().toISOString()
    }
    messages.value.push(assistantMessage)

    if (response.profile_update) {
      profileDimensions.value = response.profile_update
    }
  } catch (error) {
    console.error('Failed to send message:', error)
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '抱歉，发送消息时出现错误，请重试。',
      timestamp: new Date().toISOString()
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const updateProfile = async () => {
  try {
    await profileStore.updateDimension(editDimension.value, editValue.value)
    profileDimensions.value = profileStore.dimensions
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
  profileDimensions.value = profileStore.dimensions

  // 确保有一个会话
  if (!chatStore.currentSession) {
    await chatStore.createSession('新对话')
  }
})
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100%;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h3 {
  margin-bottom: 8px;
  color: var(--text-color);
}

.message {
  display: flex;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-color-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  margin: 0 12px;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  line-height: 1.6;
}

.message.user .message-text {
  background: var(--primary-color);
  color: white;
}

.message-time {
  font-size: 12px;
  color: var(--text-color-placeholder);
  margin-top: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-color-placeholder);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.input-container {
  padding: 20px;
  background: white;
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper textarea {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  max-height: 120px;
}

.input-wrapper textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.send-btn {
  padding: 12px 24px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.send-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.send-btn:disabled {
  background: var(--bg-color-dark);
  cursor: not-allowed;
}

.profile-panel {
  width: 300px;
  background: white;
  border-left: 1px solid var(--border-color);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.profile-panel h3 {
  margin-bottom: 20px;
  color: var(--text-color);
}

.radar-chart {
  width: 100%;
  height: 250px;
  margin-bottom: 20px;
}

.profile-details {
  flex: 1;
  overflow-y: auto;
}

.profile-item {
  margin-bottom: 16px;
}

.profile-item .label {
  display: block;
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-bottom: 4px;
}

.profile-item .value {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.confidence-bar {
  height: 4px;
  background: var(--bg-color-dark);
  border-radius: 2px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: var(--primary-color);
  transition: width 0.3s;
}

.edit-btn {
  width: 100%;
  padding: 10px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.edit-btn:hover {
  background: var(--bg-color-dark);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
}

.modal h3 {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.cancel-btn,
.confirm-btn {
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background: white;
  border: 1px solid var(--border-color);
}

.confirm-btn {
  background: var(--primary-color);
  color: white;
  border: none;
}
</style>
