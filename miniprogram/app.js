const { request } = require('./utils/config.js')

App({
  globalData: { editingBill: null, user: null, loginPromise: null },
  onLaunch() {
    if (wx.getStorageSync('authMode') !== 'wechat') wx.removeStorageSync('token')
    this.ensureLogin().catch(error => console.error('登录失败', error.message))
  },
  ensureLogin(force = false) {
    if (this.globalData.loginPromise) return this.globalData.loginPromise
    if (!force && wx.getStorageSync('token')) return Promise.resolve()
    const login = new Promise((resolve, reject) => {
      wx.login({
        success: result => result.code ? resolve(result.code) : reject(new Error('未获取到微信登录凭证')),
        fail: () => reject(new Error('微信登录失败，请重试'))
      })
    }).then(code => request('/auth/wechat-login', 'POST', { code }))
      .then(result => {
        wx.setStorageSync('token', result.token)
        wx.setStorageSync('authMode', 'wechat')
        this.globalData.user = result.user
      })
    this.globalData.loginPromise = login
    const clear = () => { this.globalData.loginPromise = null }
    login.then(clear, clear)
    return login
  }
})
