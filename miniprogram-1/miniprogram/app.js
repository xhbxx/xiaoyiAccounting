// app.js
const { request } = require('./utils/api.js')

App({
  onLaunch: async function () {
    try {
      const res = await request('/auth/wechat-login', 'POST', { code: 'test123' })
      wx.setStorageSync('token', res.token)
      console.log('登录成功', res.token)
    } catch (e) {
      console.error('登录失败', e)
    }
  }
});


