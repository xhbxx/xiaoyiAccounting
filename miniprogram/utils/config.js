const BASE_URL = 'https://xiao-341383-4-1525207456.sh.run.tcloudbase.com'

function send(url, method, data, filePath) {
  const token = wx.getStorageSync('token')
  return new Promise((resolve, reject) => {
    const options = {
      url: BASE_URL + url,
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success: response => {
        let body = response.data
        try {
          if (typeof body === 'string') body = JSON.parse(body)
        } catch (error) {
          reject(new Error('服务返回异常，请重试'))
          return
        }
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(body)
          return
        }
        const detail = body && body.detail
        const message = typeof detail === 'string' ? detail : '请求失败，请稍后重试'
        const error = new Error(message)
        error.statusCode = response.statusCode
        reject(error)
      },
      fail: () => reject(new Error('网络连接失败，请检查服务是否启动'))
    }
    if (filePath) {
      wx.uploadFile({ ...options, filePath, name: 'file' })
    } else {
      wx.request({ ...options, method, data })
    }
  })
}

async function request(url, method = 'GET', data = {}, filePath = null) {
  if (url.startsWith('/auth/')) return send(url, method, data, filePath)
  const app = getApp()
  await app.ensureLogin()
  const token = wx.getStorageSync('token')
  try {
    return await send(url, method, data, filePath)
  } catch (error) {
    if (error.statusCode !== 401) throw error
    if (token === wx.getStorageSync('token')) {
      wx.removeStorageSync('token')
      await app.ensureLogin(true)
    } else {
      await app.ensureLogin()
    }
    // 每个请求只重试一次，失效登录不会形成循环。
    return send(url, method, data, filePath)
  }
}

function mediaUrl(url) {
  return url && url.startsWith('/') ? BASE_URL + url : url || ''
}

module.exports = { request, BASE_URL, mediaUrl }
