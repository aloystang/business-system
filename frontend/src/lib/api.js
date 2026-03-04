const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export function getToken() {
  return localStorage.getItem('token')
}

export function setToken(token) {
  localStorage.setItem('token', token)
}

export function clearToken() {
  localStorage.removeItem('token')
}

async function request(path, options = {}) {
  const headers = options.headers ? { ...options.headers } : {}
  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    })
  } catch (err) {
    throw new Error('无法连接后端服务，请确认备用 Mac 上的后端服务与公网访问链路已启动')
  }

  const shouldRedirectLogin = response.status === 401
  if (shouldRedirectLogin) {
    clearToken()
  }

  if (!response.ok) {
    let message = 'Request failed'
    let detailPayload = null
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') {
        message = data.detail
      } else if (Array.isArray(data.detail) && data.detail.length > 0) {
        const first = data.detail[0] || {}
        const field = Array.isArray(first.loc) ? first.loc.join('.') : ''
        const detailText = typeof first.msg === 'string' ? first.msg : '参数校验失败'
        message = field ? `参数错误：${field} - ${detailText}` : detailText
      } else if (data.detail && typeof data.detail === 'object') {
        detailPayload = data.detail
        message = data.detail.message || message
      } else if (typeof data.message === 'string') {
        message = data.message
      }
      if (!detailPayload && data.missing_fields) {
        detailPayload = { missing_fields: data.missing_fields }
      }
    } catch (err) {
      // ignore
    }
    if (message === 'Request failed') {
      message = `请求失败（${response.status}）`
    }
    if (message === 'Not authenticated') {
      message = '未登录，请先登录'
    }
    if (
      shouldRedirectLogin &&
      typeof window !== 'undefined' &&
      window.location.pathname !== '/login'
    ) {
      window.location.href = '/login'
    }
    const reqErr = new Error(message)
    if (detailPayload && typeof detailPayload === 'object') {
      Object.assign(reqErr, detailPayload)
    }
    throw reqErr
  }

  return response
}

export async function apiJson(path, options = {}) {
  const response = await request(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })
  return response.json()
}

export async function apiUpload(path, formData) {
  const response = await request(path, {
    method: 'POST',
    body: formData,
  })
  return response.json()
}

export async function apiDownload(path) {
  const response = await request(path)
  return response.blob()
}

export { API_BASE }
