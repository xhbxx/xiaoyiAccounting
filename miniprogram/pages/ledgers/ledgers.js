const { request } = require('../../utils/config.js')

Page({
  data: { statusBarHeight: 20, ledgers: [], currentId: null, loading: false, loadError: '', saving: false,
    showDialog: false, editingId: null, draftName: '' },
  onLoad() {
    this.setData({ statusBarHeight: wx.getWindowInfo().statusBarHeight })
    this.loadLedgers()
  },
  async loadLedgers() {
    this.setData({ loading: true, loadError: '' })
    try {
      const result = await request('/ledgers')
      this.setData({ ledgers: result.items, currentId: result.current_ledger_id })
    } catch (error) { this.setData({ loadError: error.message }) }
    finally { this.setData({ loading: false }) }
  },
  openCreate() {
    if (!this.data.saving) this.setData({ showDialog: true, editingId: null, draftName: '' })
  },
  openRename(e) {
    if (this.data.saving) return
    const ledger = this.data.ledgers.find(item => item.id === Number(e.currentTarget.dataset.id))
    if (ledger) this.setData({ showDialog: true, editingId: ledger.id, draftName: ledger.name })
  },
  onNameInput(e) { this.setData({ draftName: e.detail.value }) },
  closeDialog() { if (!this.data.saving) this.setData({ showDialog: false }) },
  none() {},
  async saveLedger() {
    if (this.data.saving) return
    const name = this.data.draftName.trim()
    if (!name) { this.showError(new Error('请输入账本名称')); return }
    this.setData({ saving: true })
    try {
      const id = this.data.editingId
      await request(id ? `/ledgers/${id}` : '/ledgers', id ? 'PUT' : 'POST', { name })
      this.setData({ showDialog: false })
      await this.loadLedgers()
      wx.showToast({ title: '账本已保存' })
    } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
  },
  async selectLedger(e) {
    const id = Number(e.currentTarget.dataset.id)
    if (this.data.saving || id === this.data.currentId) return
    this.setData({ saving: true })
    try {
      await request(`/ledgers/${id}/select`, 'PUT')
      this.setData({ currentId: id })
      wx.showToast({ title: '账本已切换' })
    } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
  },
  showError(error) { wx.showToast({ title: error.message || '操作失败，请重试', icon: 'none' }) }
})
