import { apiClient } from './config'

export type LlmAuthMode = 'api_key' | 'oauth'
export type LlmProviderKey = string
export type OpenAiAuthMode = LlmAuthMode

export interface LlmProviderRegistryItem {
  key: string
  label: string
  default_model: string
  models: string[]
  auth_modes: LlmAuthMode[]
}

export interface LlmProviderRegistryResponse {
  providers: LlmProviderRegistryItem[]
}

export interface LlmProviderSettings {
  selected_model: string
  auth_mode?: LlmAuthMode
  ready?: boolean
  [key: string]: unknown
}

export interface LlmSettingsState {
  current_provider: string
  provider_settings: Record<string, LlmProviderSettings>
}

export interface LlmSettingsPatch {
  current_provider?: string
  provider_settings?: Record<string, Record<string, unknown>>
}

export type LlmSettingsPayload = LlmSettingsState
export type OauthStatusPayload = OpenAiAuthStatus

export interface OpenAiAuthStatus {
  status: 'connected' | 'disconnected' | 'pending' | 'error'
  message?: string
  url?: string
}

export const llmSettingsApi = {
  getSettings: () =>
    apiClient.get<LlmSettingsState>('/settings/llm') as Promise<LlmSettingsState>,

  getRegistry: () =>
    apiClient.get<LlmProviderRegistryResponse>('/settings/llm/registry') as Promise<LlmProviderRegistryResponse>,

  updateSettings: (payload: LlmSettingsPatch) =>
    apiClient.put<LlmSettingsState>('/settings/llm', payload) as Promise<LlmSettingsState>,

  getOpenAiAuthStatus: () =>
    apiClient.get<OpenAiAuthStatus>('/auth/openai/status') as Promise<OpenAiAuthStatus>,

  getOpenAiStatus: () =>
    apiClient.get<OpenAiAuthStatus>('/auth/openai/status') as Promise<OpenAiAuthStatus>,

  startOpenAiAuth: () =>
    apiClient.post<OpenAiAuthStatus>('/auth/openai/start', {}) as Promise<OpenAiAuthStatus>,

  logoutOpenAiAuth: () =>
    apiClient.post<OpenAiAuthStatus>('/auth/openai/logout', {}) as Promise<OpenAiAuthStatus>,
}
