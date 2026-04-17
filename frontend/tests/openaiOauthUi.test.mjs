import test from 'node:test'
import assert from 'node:assert/strict'

import {
  getOpenAiOauthLoginVisibility,
  getOpenAiOauthStartFeedback,
} from '../src/components/workbench/openaiOauthUi.ts'

test('hides the login button when OAuth is already connected', () => {
  assert.equal(getOpenAiOauthLoginVisibility('connected'), false)
  assert.equal(getOpenAiOauthLoginVisibility('pending'), true)
  assert.equal(getOpenAiOauthLoginVisibility('disconnected'), true)
})

test('returns an informational message when the backend is already connected', () => {
  assert.deepEqual(
    getOpenAiOauthStartFeedback({ status: 'connected', message: 'Already logged in' }),
    {
      type: 'info',
      message: 'Already logged in',
    }
  )
})

test('returns the normal success message when a new OAuth flow starts', () => {
  assert.deepEqual(
    getOpenAiOauthStartFeedback({ status: 'pending' }),
    {
      type: 'success',
      message: '已发起 Codex OAuth 登录',
    }
  )
})
