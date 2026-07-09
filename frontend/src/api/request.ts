import axios from 'axios'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000,
})

request.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(error)
  },
)

export default request
