// pages/chart/chart.js
Page({
  /**
   * 页面的初始数据
   */
  data: {
    choise:['支出','收入'],
    choised:'支出',
    activeIndex:3
  },
  onChange(e){
    const index=e.detail.value
    let a=0
    if(index==0){ a = '支出'}
    else{a = '收入' }
    this.setData({
      choised:a 
    })
  },
  switchTime(e){

  },
  /**
   * 生命周期函数--监听页面加载
   */
  onLoad(options) {

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
      tabBar.setData({ active: 1, hidden: false });
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

  }
})
