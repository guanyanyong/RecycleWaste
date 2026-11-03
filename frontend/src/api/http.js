import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getAccessToken, setAccessToken } from './token'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 20000,
  withCredentials: true
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = null

async function refreshAccessToken() {
  if (!refreshing) {
    refreshing = axios
      .post('/api/v1/auth/refresh', {}, { withCredentials: true })
      .then((res) => {
        const data = res.data?.data
        if (!data?.access_token) throw new Error('refresh failed')
        setAccessToken(data.access_token)
        return data
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

const AUTH_WHITELIST = ['/auth/login', '/auth/refresh']

http.interceptors.response.use(
  (response) => {
    const payload = response.data
    if (payload && typeof payload === 'object' && 'code' in payload) {
      if (payload.code !== 'OK') {
        const err = new Error(payload.message || '请求失败')
        err.code = payload.code
        err.details = payload.data
        throw err
      }
      return payload.data
    }
    return payload
  },
  async (error) => {
    const { response, config } = error
    const status = response?.status
    const url = config?.url || ''
    const payload = response?.data

    if (status === 401 && !config._retried && !AUTH_WHITELIST.some((p) => url.includes(p))) {
      config._retried = true
      try {
        await refreshAccessToken()
        return http(config)
      } catch {
        setAccessToken('')
        if (!location.hash.includes('/login')) {
          location.hash = '#/login'
          ElMessage.warning('登录已过期，请重新登录')
        }
        return Promise.reject(error)
      }
    }

    const message = payload?.message || (status ? `请求失败（${status}）` : '网络连接失败，请检查后端服务')
    if (status !== 401) ElMessage.error(message)
    const err = new Error(message)
    err.code = payload?.code
    err.status = status
    return Promise.reject(err)
  }
)

export default http
