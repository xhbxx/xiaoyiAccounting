// pages/detail/detail.js
const { request } = require('../../utils/config.js')
const { categoryImage } = require('../../utils/categories.js')

Page({
  /**
   * 页面的初始数据
   */
  data: {
    year: "2025",
    month: "06",
    totleIncome: '0.00',
    totleOutcome: '0.00',
    groups: [],
    ledger: null,
    loading: false,
    loadError: '',
    deleting: false

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
    const app = getApp()
    if (app.globalData.viewMonth) {
      this.setData(app.globalData.viewMonth)
      app.globalData.viewMonth = null
    }
    const tabBar = this.getTabBar && this.getTabBar();
    if (tabBar) {
      tabBar.setData({ active: 0, hidden: false });
    }
    this.loadHome();

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
    const requestId = (this.homeRequestId || 0) + 1
    this.homeRequestId = requestId
    const { year, month } = this.data;
    this.setData({ loading: true, loadError: '' })
    try {
      const data = await request(`/home?year=${year}&month=${parseInt(month)}`)
      if (requestId !== this.homeRequestId) return
      this.setData({
        totleIncome: data.period.income,
        totleOutcome: data.period.expense,
        groups: data.groups.map(group => ({ ...group,
          items: group.items.map(item => ({ ...item, image: categoryImage(item.category) })) })),
        ledger: data.ledger
      });
    } catch (e) {
      if (requestId === this.homeRequestId) this.setData({ loadError: e.message || '加载失败，请重试' })
    } finally {
      if (requestId === this.homeRequestId) this.setData({ loading: false })
    }
  },

  onBillTap(e) {
    if (this.data.deleting) return
    const id = Number(e.currentTarget.dataset.id)
    const bill = this.data.groups.flatMap(group => group.items).find(item => item.id === id)
    if (!bill) return
    wx.showActionSheet({
      itemList: ['编辑账单', '删除账单'],
      success: result => {
        if (result.tapIndex === 0) {
          getApp().globalData.editingBill = { ...bill, ledger_id: this.data.ledger.id }
          wx.switchTab({ url: '/pages/bill/bill' })
        } else {
          this.confirmDelete(bill)
        }
      }
    })
  },

  confirmDelete(bill) {
    wx.showModal({
      title: '删除账单',
      content: '确定删除这笔账单吗？此操作不可撤销。',
      confirmColor: '#b93830',
      success: async result => {
        if (!result.confirm || this.data.deleting) return
        this.setData({ deleting: true })
        try {
          await request(`/bills/${bill.id}`, 'DELETE')
          wx.showToast({ title: '账单已删除', icon: 'success' })
          await this.loadHome()
        } catch (error) {
          wx.showToast({ title: error.message || '删除失败，请重试', icon: 'none' })
        } finally {
          this.setData({ deleting: false })
        }
      }
    })
  }
})
