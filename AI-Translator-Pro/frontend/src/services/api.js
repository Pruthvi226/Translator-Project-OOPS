import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const translateApi = (body) => api.post('/translate', body)
export const speechToTextApi = (formData) => api.post('/speech-to-text', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const textToSpeechApi = (body) => api.post('/text-to-speech', body)
export const imageTranslateApi = (formData) => api.post('/image-translate', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const historyApi = (params) => api.get('/history', { params })
export const loginApi = (body) => api.post('/auth/login', body)
export const signupApi = (body) => api.post('/auth/signup', body)

export function getTTSFileUrl(fileId) {
  return `${API_BASE}/tts/file/${fileId}`
}

export default api
