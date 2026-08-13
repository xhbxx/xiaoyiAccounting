// pages/detail/detail.js
const { request } = require('../../utils/config.js')

Page({
  /**
   * 页面的初始数据
   */
  data: {
    year: "2025",
    month: "06",
    totleIncome: '0.00',
    totleOutcome: '0.00',
    groups: []

  },

  goIncome(e) {

    wx.navigateTo({ url: '/pages/outcome/outcome' });
  },

  goOutcome(e) {
    wx.navigateTo({ url: '/pages/income/income' })
  },

  onDateChange(e) {
    const arr = e.detail.value.split('-');
    this.setData({
      year: arr[0],
      month: arr[1]
    });
    this.loadHome();
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    const now = new Date();
    const m = now.getMonth() + 1;
    this.setData({
      year: String(now.getFullYear()),
      month: m < 10 ? '0' + m : String(m)
    })
  },

  /**
   * 生命周期函数--监听页面初次渲染完成
   */
  onReady() {

  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    const tabBar = this.getTabBar && this.getTabBar();
    if (tabBar) {
      tabBar.setData({ active: 0, hidden: false });
      this.loadHome();
    }

  },

  /**
   * 生命周期函数--监听页面隐藏
   */
  onHide() {

  },

  /**
   * 生命周期函数--监听页面卸载
   */
  onUnload() {

  },

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {

  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {

  },

  /**
   * 用户点击右上角分享
   */
  onShareAppMessage() {

  },

  async loadHome() {
    const { year, month } = this.data;
    try {
      const data = await request(`/home?year=${year}&month=${parseInt(month)}`)
      this.setData({
        totleIncome: data.period.income,
        totleOutcome: data.period.outcome,
        groups: data.groups
      });
    } catch (e) {
      console.error('加载失败', e);
    }
  }
})
