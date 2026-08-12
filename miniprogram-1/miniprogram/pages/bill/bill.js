// pages/bill/bill.js
const { request } = require('../../utils/api.js')
Page({
  /**
   * 页面的初始数据
   */
  data: {
    currentType: 'expense',
    itemE: [],
    currentTab: 0,
    itemI: [],
    selectedId:0,
    selectedName:'',
    showPopup:false,
    billDateText:'今天',
    amount:'',
    date:'',
    remark:''
  },
  async loadCategories() {
    try {
      const dataE = await request(`/categories?type=expense`)
      this.setData({ itemE: dataE.items })
      const dataI = await request(`/categories?type=income`)
      this.setData({ itemI: dataI.items })
    } catch (e) {
      console.error('加载分类失败', e)
    }
  },

  switchType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      currentType: type,
      currentTab: type === 'expense' ? 0 : 1
    })

  },
  onRemarkInput(e){
    this.setData({ remark: e.detail.value })
  },
  async submitBill() {
    const { amount, remark, date, selectedName, currentType } = this.data
    if (!amount) { return }
    const today = this.formatDate(new Date())
    const billDate = date || today
    try {
      await request(`/bills?amount=${amount}&type=${currentType}&category=${selectedName}&bill_date=${billDate}&remark=${encodeURIComponent(remark || '')}`, 'POST')
      this.setData({ showPopup: false, amount: '', remark: '', date: billDate, billDateText: billDate === today ? '今天' : billDate })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/detail/detail' })
      }, 1000)
    } catch (e) {
    }
  },
  onSwiperChange(e) {
    const tab = e.detail.current
    this.setData({
      currentTab: tab,
      currentType: tab === 0 ? 'expense' : 'income'
    })
  },
  none(e){},
  selected(e){
    const {id,name}=e.currentTarget.dataset
    this.setData({
      selectedName:name,
      selectedId:id,
      showPopup: true 
    })
  },
  closePopup(e){
    this.setData({
      showPopup:false
    })
  },
  onKeyTap(e){
      const key = e.currentTarget.dataset.key
      let amount = this.data.amount || ''
      if(amount === '' && key === '0') return
      if (amount === '' && key === '.') return
      if (key === '.' && amount.includes('.')) return
      if (amount.includes('.') && amount.split('.')[1].length >= 2) return
      this.setData({ amount: amount + key })
  },
  onKeyDelete(e){ 
    let money=this.data.amount
    if (money === '') return
    this.setData({ amount: money.slice(0,-1) })
  },
  date(e){
    const val = e.detail.value
    const today = this.formatDate(new Date())
    this.setData({
      date: val,
      billDateText: val === today ? '今天' : val
    })
  },
  formatDate(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {
    const today = this.formatDate(new Date())
    this.setData({ date: today, billDateText: '今天' })
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
      tabBar.setData({ active: 2, hidden: true });
    }
    this.loadCategories();
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

  }
})
