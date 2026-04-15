import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import {
  llmSettingsApi,
  type LlmProviderKey,
  type LlmProviderRegistryItem,
  type LlmSettingsPayload,
  type OauthStatusPayload,
  type OpenAiAuthMode,
} from '../api/llmSettings'

export const useLlmSettingsStore = defineStore('llmSettings', () => {
  const settings = ref<LlmSettingsPayload | null>(null)
  const registry = ref<LlmProviderRegistryItem[]>([])
  const oauthStatus = ref<OauthStatusPayload>({ status: 'disconnected', message: '' })
  const panelOpen = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const authLoading = ref(false)
  const error = ref<string | null>(null)
  let oauthPollTimer: number | null = null
  let oauthPollAttempts = 0

  const currentProvider = computed<LlmProviderKey | string>(() => settings.value?.current_provider ?? 'anthropic')
  const currentProviderState = computed(() => settings.value?.provider_settings?.[currentProvider.value] ?? null)
  const providers = computed(() => registry.value)
  const currentProviderMeta = computed(() => registry.value.find((item: LlmProviderRegistryItem) => item.key === currentProvider.value) ?? null)
  const currentModels = computed(() => currentProviderMeta.value?.models ?? [])
  const openAiState = computed(() => settings.value?.provider_settings?.openai ?? null)
  const openAiAuthMode = computed<OpenAiAuthMode>(() => openAiState.value?.auth_mode ?? 'api_key')
  const openAiReady = computed(() => openAiState.value?.ready ?? false)
  const currentModelSummary = computed(
    () => currentProviderState.value?.selected_model ?? currentProviderMeta.value?.default_model ?? '未设置'
  )

  async function loadRegistry(force = false) {
    if (!force && registry.value.length > 0) return registry.value
    const result = await llmSettingsApi.getRegistry()
    registry.value = result.providers
    return registry.value
  }

  async function refreshOauthStatus() {
    oauthStatus.value = await llmSettingsApi.getOpenAiStatus()
    if (oauthStatus.value.status !== 'pending') {
      stopOauthPolling()
    }
    return oauthStatus.value
  }

  async function loadSettings() {
    settings.value = await llmSettingsApi.getSettings()
    return settings.value
  }

  async function refreshAll(force = false) {
    loading.value = true
    error.value = null
    try {
      const [registryResult, settingsResult, oauthResult] = await Promise.allSettled([
        loadRegistry(force),
        loadSettings(),
        refreshOauthStatus(),
      ])

      if (registryResult.status === 'rejected') throw registryResult.reason
      if (settingsResult.status === 'rejected') throw settingsResult.reason
      if (oauthResult.status === 'fulfilled') {
        oauthStatus.value = oauthResult.value
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载模型设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function persistSettings(payload: {
    current_provider?: LlmProviderKey | string
    provider_settings?: Record<string, Record<string, unknown>>
  }) {
    saving.value = true
    error.value = null
    try {
      settings.value = await llmSettingsApi.updateSettings(payload)
      await refreshOauthStatus().catch(() => {})
      return settings.value
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存模型设置失败'
      throw err
    } finally {
      saving.value = false
    }
  }

  async function setCurrentProvider(provider: LlmProviderKey | string) {
    const providerMeta = registry.value.find((item: LlmProviderRegistryItem) => item.key === provider)
    const savedModel = settings.value?.provider_settings?.[provider]?.selected_model
    const selectedModel = savedModel || providerMeta?.default_model || ''
    await persistSettings({
      current_provider: provider,
      provider_settings: {
        [provider]: {
          selected_model: selectedModel,
        },
      },
    })
  }

  async function setCurrentModel(model: string) {
    await persistSettings({
      provider_settings: {
        [currentProvider.value]: {
          selected_model: model,
        },
      },
    })
  }

  async function setOpenAiAuthMode(mode: OpenAiAuthMode) {
    await persistSettings({
      provider_settings: {
        openai: {
          auth_mode: mode,
        },
      },
    })
  }

  async function startOpenAiAuth() {
    authLoading.value = true
    error.value = null
    try {
      const result = await llmSettingsApi.startOpenAiAuth()
      if (result.url) {
        const opened = window.open(result.url, 'openai-oauth', 'popup=yes,width=540,height=720')
        if (!opened) {
          throw new Error('浏览器拦截了 OAuth 登录弹窗，请允许弹窗后重试')
        }
      }
      await refreshOauthStatus().catch(() => {})
      if (result.status === 'pending') {
        startOauthPolling()
      }
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '启动 OpenAI OAuth 失败'
      throw err
    } finally {
      authLoading.value = false
    }
  }

  async function logoutOpenAiAuth() {
    authLoading.value = true
    error.value = null
    try {
      const result = await llmSettingsApi.logoutOpenAiAuth()
      oauthStatus.value = result
      await loadSettings().catch(() => {})
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : '退出 OpenAI OAuth 失败'
      throw err
    } finally {
      stopOauthPolling()
      authLoading.value = false
    }
  }

  function startOauthPolling() {
    stopOauthPolling()
    oauthPollAttempts = 0
    oauthPollTimer = window.setInterval(async () => {
      oauthPollAttempts += 1
      try {
        const status = await refreshOauthStatus()
        if (status.status === 'connected') {
          await loadSettings().catch(() => {})
          stopOauthPolling()
          return
        }
        if (status.status === 'error' || oauthPollAttempts >= 80) {
          stopOauthPolling()
        }
      } catch {
        if (oauthPollAttempts >= 80) {
          stopOauthPolling()
        }
      }
    }, 1500)
  }

  function stopOauthPolling() {
    if (oauthPollTimer !== null) {
      window.clearInterval(oauthPollTimer)
      oauthPollTimer = null
    }
  }

  function togglePanel(next?: boolean) {
    panelOpen.value = typeof next === 'boolean' ? next : !panelOpen.value
  }

  function clearError() {
    error.value = null
  }

  return {
    settings,
    registry,
    oauthStatus,
    panelOpen,
    loading,
    saving,
    authLoading,
    error,
    providers,
    currentProvider,
    currentProviderState,
    currentProviderMeta,
    currentModels,
    currentModelSummary,
    openAiAuthMode,
    openAiReady,
    refreshAll,
    refreshOauthStatus,
    persistSettings,
    setCurrentProvider,
    setCurrentModel,
    setOpenAiAuthMode,
    startOpenAiAuth,
    logoutOpenAiAuth,
    stopOauthPolling,
    togglePanel,
    clearError,
  }
})
