const { request } = require('../../utils/config.js')
const { categoryImage } = require('../../utils/categories.js')

function calculateAmount(expression) {
  if (!/^\d{1,10}(\.\d{0,2})?([+-]\d{1,10}(\.\d{0,2})?)*$/.test(expression)) return null
  // 按整数分累计，避免 0.1 + 0.2 产生浮点误差。
  return expression.match(/[+-]?\d+(?:\.\d*)?/g).reduce((total, term) => {
    const sign = term.startsWith('-') ? -1 : 1
    const [whole, fraction = ''] = term.replace(/^[+-]/, '').split('.')
    return total + sign * (Number(whole) * 100 + Number(fraction.padEnd(2, '0')))
  }, 0)
}

Page({
  data: {
    currentType: 'expense',
    currentTab: 0,
    itemE: [],
    itemI: [],
    selectedId: 0,
    selectedName: '',
    showPopup: false,
    billDateText: '今天',
    amount: '',
    date: '',
    remark: '',
    editingId: null,
    ledgerId: null,
    submitting: false,
    loading: false,
    loadError: ''
  },

  async loadCategories() {
    this.setData({ loading: true, loadError: '' })
    try {
      const [expense, income, profile] = await Promise.all([
        request('/categories?type=expense'),
        request('/categories?type=income'),
        request('/profile')
      ])
      this.setData({
        itemE: expense.items.map(item => ({ ...item, image: categoryImage(item.name, true) })),
        itemI: income.items.map(item => ({ ...item, image: categoryImage(item.name, true) }))
      })
      if (!this.data.editingId && !this.typeTouched) {
        const type = profile.settings.default_bill_type
        this.setData({ currentType: type, currentTab: type === 'income' ? 1 : 0 })
      }
    } catch (error) {
      this.setData({ loadError: error.message || '分类加载失败，请点击重试' })
    } finally {
      this.setData({ loading: false })
    }
  },

  switchType(e) {
    this.typeTouched = true
    const type = e.currentTarget.dataset.type
    this.setData({ currentType: type, currentTab: type === 'expense' ? 0 : 1,
      selectedId: 0, selectedName: '' })
  },

  onSwiperChange(e) {
    const tab = e.detail.current
    if (tab === this.data.currentTab) return
    this.typeTouched = true
    this.setData({ currentTab: tab, currentType: tab === 0 ? 'expense' : 'income',
      selectedId: 0, selectedName: '' })
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  async submitBill() {
    if (this.data.submitting) return
    const { amount, remark, date, selectedName, currentType, editingId, ledgerId } = this.data
    const cents = calculateAmount(amount)
    if (cents === null) {
      wx.showToast({ title: '请输入完整的计算金额', icon: 'none' })
      return
    }
    if (!Number.isSafeInteger(cents) || cents <= 0 || cents > 999999999999) {
      wx.showToast({ title: '金额须大于 0 且不超过 9999999999.99', icon: 'none' })
      return
    }
    if (!selectedName) {
      wx.showToast({ title: '请选择分类', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      await request(editingId ? `/bills/${editingId}` : '/bills', editingId ? 'PUT' : 'POST', {
        ledger_id: ledgerId,
        amount: `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')}`,
        type: currentType,
        category: selectedName,
        bill_date: this.originalBillDate && this.originalBillDate.slice(0, 10) === date
          ? this.originalBillDate : date || this.formatDate(new Date()),
        remark: remark.trim()
      })
      this.setData({ showPopup: false })
      wx.showToast({ title: editingId ? '账单已更新' : '记账成功', icon: 'success' })
      wx.switchTab({ url: '/pages/detail/detail' })
    } catch (error) {
      wx.showToast({ title: error.message || '保存失败，请重试', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  none() {},
  selected(e) {
    this.typeTouched = true
    const { id, name } = e.currentTarget.dataset
    this.setData({ selectedName: name, selectedId: id, showPopup: true })
  },
  closePopup() {
    if (!this.data.submitting) this.setData({ showPopup: false })
  },
  goBack() {
    if (!this.data.submitting) wx.switchTab({ url: '/pages/detail/detail' })
  },
  onKeyTap(e) {
    if (this.data.submitting) return
    const key = e.currentTarget.dataset.key
    let amount = this.data.amount
    const operand = amount.split(/[+-]/).pop()
    if (amount.length >= 128) return
    if (key === '.' && operand.includes('.')) return
    if (operand.includes('.') && operand.split('.')[1].length >= 2) return
    if (!operand.includes('.') && operand.length >= 10 && key !== '.') return
    if (key === '.' && !operand) amount += '0'
    if (operand === '0' && key !== '.') amount = amount.slice(0, -1)
    this.setData({ amount: amount + key })
  },
  onOperatorTap(e) {
    if (this.data.submitting || !this.data.amount) return
    const operator = e.currentTarget.dataset.operator
    const amount = this.data.amount
    if (/[+-]$/.test(amount)) {
      this.setData({ amount: amount.slice(0, -1) + operator })
    } else if (amount.length < 128) {
      this.setData({ amount: amount + operator })
    }
  },
  onKeyDelete() {
    if (!this.data.submitting) this.setData({ amount: this.data.amount.slice(0, -1) })
  },
  date(e) {
    const value = e.detail.value
    this.setData({ date: value, billDateText: value === this.formatDate(new Date()) ? '今天' : value })
  },
  formatDate(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  },
  onShow() {
    const tabBar = this.getTabBar && this.getTabBar()
    if (tabBar) tabBar.setData({ active: 2, hidden: true })
    const app = getApp()
    const bill = app.globalData.editingBill
    app.globalData.editingBill = null
    this.typeTouched = false
    const today = this.formatDate(new Date())
    const date = bill ? bill.bill_date.slice(0, 10) : today
    this.originalBillDate = bill ? bill.bill_date : null
    this.setData({
      editingId: bill ? bill.id : null,
      ledgerId: bill ? bill.ledger_id : null,
      currentType: bill ? bill.type : 'expense',
      currentTab: bill && bill.type === 'income' ? 1 : 0,
      selectedId: 0,
      selectedName: bill ? bill.category : '',
      amount: bill ? bill.amount : '',
      remark: bill ? bill.remark || '' : '',
      date,
      billDateText: date.slice(0, 10) === today ? '今天' : date.slice(0, 10),
      showPopup: Boolean(bill)
    })
    this.loadCategories()
  }
})
