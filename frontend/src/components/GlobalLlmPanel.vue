<template>
  <div class="global-llm-panel">
    <n-button
      class="global-llm-trigger"
      type="primary"
      secondary
      round
      size="small"
      :loading="loading"
      @click="togglePanel"
    >
      <span class="trigger-label">LLM</span>
      <span v-if="currentSummary" class="trigger-summary">{{ currentSummary }}</span>
    </n-button>

    <n-collapse-transition>
      <n-card
        v-if="panelOpen"
        class="global-llm-card"
        size="small"
        :bordered="true"
        :segmented="{ content: true, footer: 'soft' }"
      >
        <template #header>
          <div class="panel-header">
            <div>
              <div class="panel-title">全局 LLM 设置</div>
              <n-text depth="3" class="panel-subtitle">先选提供商，再选该提供商的模型</n-text>
            </div>
            <n-button quaternary circle size="small" aria-label="关闭面板" @click="togglePanel(false)">
              ×
            </n-button>
          </div>
        </template>

        <n-spin :show="loading" size="small">
          <n-space vertical :size="16" class="panel-body">
            <n-alert v-if="error" type="error" closable @close="store.clearError">
              {{ error }}
            </n-alert>

            <n-form-item label="Provider">
              <n-select
                :value="currentProvider"
                :options="providerOptions"
                placeholder="选择提供商"
                @update:value="handleProviderChange"
              />
            </n-form-item>

            <n-form-item label="Model">
              <n-select
                :value="currentModel"
                :options="currentModelOptions"
                placeholder="选择模型"
                :disabled="!currentProvider"
                @update:value="handleModelChange"
              />
            </n-form-item>

            <template v-if="currentProvider === 'openai'">
              <n-form-item label="Auth Mode">
                <n-radio-group :value="openAiAuthMode" @update:value="handleAuthModeChange">
                  <n-space :size="12">
                    <n-radio value="api_key">API Key</n-radio>
                    <n-radio value="oauth">OAuth</n-radio>
                  </n-space>
                </n-radio-group>
              </n-form-item>

              <n-alert type="info" :show-icon="false">
                <n-space vertical :size="6">
                  <n-space align="center" :size="8" wrap>
                    <n-tag :type="openAiReady ? 'success' : 'warning'" size="small" round>
                      Codex OAuth {{ openAiReady ? '已就绪' : '未就绪' }}
                    </n-tag>
                    <n-tag :type="authTagType" size="small" round>
                      {{ oauthStatusMessage }}
                    </n-tag>
                  </n-space>
                  <n-text depth="3">
                    {{ openAiAuthHint }}
                  </n-text>
                </n-space>
              </n-alert>

              <n-space :size="8" wrap>
                <n-button
                  v-if="openAiAuthMode === 'oauth' && !openAiConnected"
                  type="primary"
                  :loading="authLoading"
                  @click="handleOpenAiLogin"
                >
                  登录 OAuth
                </n-button>
                <n-button
                  v-if="openAiAuthMode === 'oauth' && oauthStatus?.status === 'connected'"
                  secondary
                  :loading="authLoading"
                  @click="handleOpenAiLogout"
                >
                  退出登录
                </n-button>
              </n-space>
            </template>

            <n-alert
              v-if="currentProvider !== 'openai'"
              :type="currentProviderReady ? 'success' : 'warning'"
              :show-icon="false"
            >
              <n-text depth="3">
                {{ currentProviderHint }}
              </n-text>
            </n-alert>

            <n-alert type="success" :show-icon="false">
              <n-space justify="space-between" align="center" wrap style="width: 100%">
                <span>{{ saving ? '正在保存到后端…' : '更改会自动保存到后端' }}</span>
                <n-tag v-if="saving" type="warning" size="small" round>保存中</n-tag>
              </n-space>
            </n-alert>
          </n-space>
        </n-spin>
      </n-card>
    </n-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useMessage } from 'naive-ui'
import { useLlmSettingsStore } from '../stores/llmSettingsStore'

const store = useLlmSettingsStore()
const message = useMessage()

const panelOpen = computed(() => store.panelOpen)
const currentProvider = computed(() => store.currentProvider)
const currentProviderMeta = computed(() => store.currentProviderMeta)
const currentProviderState = computed(() => store.currentProviderState)
const currentModel = computed(() =>
  store.currentProviderState?.selected_model || currentProviderMeta.value?.default_model || ''
)
const currentModelOptions = computed(() =>
  store.currentModels.map(model => ({ label: model, value: model }))
)
const providerOptions = computed(() =>
  store.providers.map(provider => ({ label: provider.label, value: provider.key }))
)
const loading = computed(() => store.loading || store.saving)
const saving = computed(() => store.saving)
const authLoading = computed(() => store.authLoading)
const error = computed(() => store.error)
const oauthStatus = computed(() => store.oauthStatus)
const openAiAuthMode = computed(() => store.openAiAuthMode)
const openAiReady = computed(() => store.openAiReady)
const openAiConnected = computed(() => oauthStatus.value.status === 'connected')
const currentProviderReady = computed(() => currentProviderState.value?.ready ?? false)

const currentSummary = computed(() => {
  if (!currentProvider.value) return ''
  const label = currentProviderMeta.value?.label ?? currentProvider.value
  return currentModel.value ? `${label} · ${currentModel.value}` : label
})

const authTagType = computed(() => {
  switch (oauthStatus.value.status) {
    case 'connected':
      return 'success'
    case 'pending':
      return 'warning'
    case 'error':
      return 'error'
    default:
      return 'default'
  }
})

const oauthStatusMessage = computed(() => {
  return oauthStatus.value.message || oauthStatus.value.status
})

const openAiAuthHint = computed(() => {
  if (openAiAuthMode.value !== 'oauth') {
    return '当前为 API Key 模式。切换到 OAuth 后，登录状态会由后台自动校验。'
  }
  if (oauthStatus.value.status === 'connected') {
    return 'Codex OAuth 已连接。当前会通过 ChatGPT Codex 后端消耗 Codex 额度，不走 OpenAI API credits。'
  }
  return '点击登录会拉起 Codex OAuth 授权页；授权成功后，OpenAI Provider 将走 ChatGPT Codex 后端。'
})

const currentProviderHint = computed(() => {
  if (currentProvider.value === 'minimax') {
    return currentProviderReady.value
      ? 'MiniMax 已就绪，当前会通过后端配置的 MINIMAX_API_KEY 与 MINIMAX_BASE_URL 调用模型。'
      : '当前后端未检测到 MINIMAX_API_KEY。请先配置 MINIMAX_API_KEY（可选 MINIMAX_BASE_URL），然后刷新页面。'
  }

  if (currentProvider.value === 'anthropic') {
    return currentProviderReady.value
      ? 'Claude 已就绪，当前会通过后端配置的 ANTHROPIC_API_KEY 调用模型。'
      : '当前后端未检测到 ANTHROPIC_API_KEY。请先配置 ANTHROPIC_API_KEY，然后刷新页面。'
  }

  return '当前提供商状态由后端统一校验。'
})

async function initialize() {
  try {
    await store.refreshAll()
  } catch {
    message.error('LLM 设置加载失败')
  }
}

function togglePanel(next?: boolean) {
  store.togglePanel(next)
}

function handleProviderChange(value: string | number | null) {
  if (typeof value === 'string') {
    void store.setCurrentProvider(value)
  }
}

function handleModelChange(value: string | number | null) {
  if (typeof value === 'string') {
    void store.setCurrentModel(value)
  }
}

function handleAuthModeChange(value: string | number | null) {
  if (value === 'api_key' || value === 'oauth') {
    void store.setOpenAiAuthMode(value)
  }
}

async function handleOpenAiLogin() {
  try {
    const result = await store.startOpenAiAuth()
    if (result.status === 'connected' && !result.url) {
      message.info(result.message || 'Codex OAuth 已连接，如需更换账号请先退出登录')
      return
    }
    message.success('已发起 Codex OAuth 登录')
  } catch {
    message.error('Codex 登录失败')
  }
}

async function handleOpenAiLogout() {
  try {
    await store.logoutOpenAiAuth()
    message.success('已退出 Codex OAuth')
  } catch {
    message.error('Codex 退出登录失败')
  }
}

async function handleOauthMessage(event: MessageEvent) {
  const payload = event.data
  if (!payload || typeof payload !== 'object' || payload.type !== 'openai-oauth-complete') {
    return
  }

  await store.refreshOauthStatus().catch(() => {})
  await store.refreshAll(true).catch(() => {})

  if (payload.status === 'connected') {
    message.success(payload.message || 'Codex OAuth 登录成功')
    return
  }
  message.error(payload.message || 'Codex OAuth 登录失败')
}

onMounted(() => {
  window.addEventListener('message', handleOauthMessage)
  void initialize()
})

onUnmounted(() => {
  window.removeEventListener('message', handleOauthMessage)
  store.stopOauthPolling()
})
</script>

<style scoped>
.global-llm-panel {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 1200;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  pointer-events: none;
}

.global-llm-trigger,
.global-llm-card {
  pointer-events: auto;
}

.global-llm-trigger {
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(12px);
}

.trigger-label {
  font-weight: 700;
  letter-spacing: 0.02em;
}

.trigger-summary {
  margin-left: 8px;
  font-size: 12px;
  opacity: 0.82;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-llm-card {
  width: min(92vw, 380px);
  max-height: calc(100vh - 96px);
  overflow: hidden;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.18);
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
}

.panel-subtitle {
  display: block;
  margin-top: 2px;
  font-size: 12px;
}

.panel-body {
  width: 100%;
}

:deep(.n-form-item) {
  margin-bottom: 0;
}
</style>
