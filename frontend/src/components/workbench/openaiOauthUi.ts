import type { OpenAiAuthStatus } from '../../api/llmControl'

export function getOpenAiOauthLoginVisibility(status: OpenAiAuthStatus['status']) {
  return status !== 'connected'
}

export function getOpenAiOauthStartFeedback(result: Pick<OpenAiAuthStatus, 'status' | 'message'>) {
  if (result.status === 'connected') {
    return {
      type: 'info' as const,
      message: result.message || 'Codex OAuth 已连接，无需重复登录',
    }
  }

  return {
    type: 'success' as const,
    message: result.message || '已发起 Codex OAuth 登录',
  }
}
