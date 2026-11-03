// 访问令牌仅保存在内存，不写入 localStorage，降低 XSS 风险
let accessToken = ''

export function setAccessToken(token) {
  accessToken = token || ''
}

export function getAccessToken() {
  return accessToken
}
