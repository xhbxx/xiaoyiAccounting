const { request, mediaUrl } = require('../../utils/config.js')

Page({
  data: {
    nickName: '记账用户', avatarUrl: '', continueDay: '—', allDay: '—', allCnt: '—',
    loading: false, loadError: '', statusBarHeight: 20
  },
  onLoad() {
    this.setData({ statusBarHeight: wx.getWindowInfo().statusBarHeight })
  },
  onShow() {
    const tabBar = this.getTabBar && this.getTabBar()
    if (tabBar) tabBar.setData({ active: 4, hidden: false })
    this.loadProfile()
  },
  async loadProfile() {
    this.setData({ loading: true, loadError: '' })
    try {
      const result = await request('/profile')
      this.setData({
        nickName: result.user.nick_name || '记账用户', avatarUrl: mediaUrl(result.user.avatar_url),
        continueDay: result.statistics.consecutive_days,
        allDay: result.statistics.total_days, allCnt: result.statistics.total_bills
      })
    } catch (error) {
      this.setData({ loadError: error.message })
    } finally {
      this.setData({ loading: false })
    }
  },
  openLedgers() { wx.navigateTo({ url: '/pages/ledgers/ledgers' }) },
  openSettings() { wx.navigateTo({ url: '/pages/settings/settings' }) }
})
