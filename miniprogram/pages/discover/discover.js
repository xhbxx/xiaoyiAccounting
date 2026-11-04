const { request } = require('../../utils/config.js')

Page({
  data: {
    year: '', month: '', ledgerName: '', ledgerId: null,
    income: '0.00', expense: '0.00', balance: '0.00', budget: null,
    loading: false, loadError: '', showBudgetDialog: false, budgetAmount: '', saving: false,
    statusBarHeight: 20, remainingPercent: 0, rightRotation: -135, leftRotation: 45
  },
  onLoad() {
    const now = new Date()
    this.setData({ year: String(now.getFullYear()), month: String(now.getMonth() + 1).padStart(2, '0'),
      statusBarHeight: wx.getWindowInfo().statusBarHeight })
  },
  onShow() {
    const tabBar = this.getTabBar && this.getTabBar()
    if (tabBar) tabBar.setData({ active: 3, hidden: false })
    this.loadMonth()
  },
  onUnload() {
    this.monthRequestId = (this.monthRequestId || 0) + 1
  },
  async loadMonth() {
    const id = (this.monthRequestId || 0) + 1
    this.monthRequestId = id
    this.setData({ loading: true, loadError: '' })
    try {
      const result = await request(`/home?year=${this.data.year}&month=${Number(this.data.month)}`)
      if (id !== this.monthRequestId) return
      const income = result.period.income
      const expense = result.period.expense
      const balance = ((Math.round(Number(income) * 100) - Math.round(Number(expense) * 100)) / 100).toFixed(2)
      this.setData({ income, expense, balance, budget: result.budget,
        ledgerName: result.ledger.name, ledgerId: result.ledger.id })
      this.updateBudgetRing()
    } catch (error) {
      if (id === this.monthRequestId) this.setData({ loadError: error.message })
    } finally {
      if (id === this.monthRequestId) this.setData({ loading: false })
    }
  },
  onMonthChange(e) {
    const [year, month] = e.detail.value.split('-')
    this.setData({ year, month })
    this.loadMonth()
  },
  openBills() {
    getApp().globalData.viewMonth = { year: this.data.year, month: this.data.month }
    wx.switchTab({ url: '/pages/detail/detail' })
  },
  openBudget() {
    if (this.data.loading || this.data.loadError) return
    this.setData({ budgetAmount: this.data.budget ? this.data.budget.amount : '' })
    this.setBudgetDialog(true)
  },
  setBudgetDialog(visible) {
    this.setData({ showBudgetDialog: visible })
    const tabBar = this.getTabBar && this.getTabBar()
    if (tabBar) tabBar.setData({ hidden: visible })
  },
  closeBudget() { if (!this.data.saving) this.setBudgetDialog(false) },
  none() {},
  onBudgetInput(e) { this.setData({ budgetAmount: e.detail.value }) },
  async saveBudget() {
    if (this.data.saving) return
    const amount = this.data.budgetAmount.trim()
    if (!/^\d{1,10}(\.\d{1,2})?$/.test(amount) || Number(amount) <= 0) {
      wx.showToast({ title: '请输入大于 0、最多两位小数的预算', icon: 'none' })
      return
    }
    this.setData({ saving: true })
    try {
      await request('/home/budget', 'PUT', { ledger_id: this.data.ledgerId,
        year: Number(this.data.year), month: Number(this.data.month), amount })
      this.setBudgetDialog(false)
      await this.loadMonth()
      wx.showToast({ title: '月预算已保存' })
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败，请重试', icon: 'none' })
    } finally { this.setData({ saving: false }) }
  },
  updateBudgetRing() {
    const budget = this.data.budget
    const value = budget ? Number(budget.remaining_percent) : 0
    const percent = Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : 0
    // 两个半圆分别绘制前 50% 和后 50%，从圆顶顺时针填充。
    this.setData({
      remainingPercent: Math.round(percent),
      rightRotation: -135 + Math.min(percent, 50) * 3.6,
      leftRotation: 45 + Math.max(percent - 50, 0) * 3.6
    })
  }
})
