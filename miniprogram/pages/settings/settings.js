const { request, mediaUrl } = require('../../utils/config.js')
const { categoryImage } = require('../../utils/categories.js')

Page({
  data: {
    nickName: '', avatarUrl: '', defaultType: 'expense', categoryType: 'expense', categories: [],
    loading: false, loadError: '', saving: false, nameDialog: false, categoryDialog: false,
    draftName: '', editingCategoryId: null, canChooseAvatar: false
  },
  onLoad() {
    this.setData({ canChooseAvatar: wx.canIUse('button.open-type.chooseAvatar') })
    this.loadSettings()
  },
  async loadSettings() {
    this.setData({ loading: true, loadError: '' })
    try {
      const result = await request('/profile')
      this.setData({ nickName: result.user.nick_name || '', avatarUrl: mediaUrl(result.user.avatar_url),
        defaultType: result.settings.default_bill_type })
      await this.loadCategories()
    } catch (error) {
      this.setData({ loadError: error.message })
    } finally {
      this.setData({ loading: false })
    }
  },
  async loadCategories() {
    const requestId = (this.categoryRequestId || 0) + 1
    this.categoryRequestId = requestId
    const result = await request(`/categories?type=${this.data.categoryType}`)
    if (requestId === this.categoryRequestId) {
      this.setData({ categories: result.items.map(item => ({ ...item, image: categoryImage(item.name) })) })
    }
  },
  async switchCategory(e) {
    if (this.data.saving) return
    this.setData({ categoryType: e.currentTarget.dataset.type, categories: [] })
    try { await this.loadCategories() } catch (error) { this.showError(error) }
  },
  editName() {
    if (!this.data.saving) this.setData({ nameDialog: true, draftName: this.data.nickName })
  },
  onNameInput(e) { this.setData({ draftName: e.detail.value }) },
  closeDialog() {
    if (!this.data.saving) this.setData({ nameDialog: false, categoryDialog: false })
  },
  none() {},
  async saveName() {
    if (this.data.saving) return
    const name = this.data.draftName.trim()
    if (!name) { this.showError(new Error('请输入姓名')); return }
    this.setData({ saving: true })
    try {
      const user = await request('/profile', 'PUT', { nick_name: name })
      this.setData({ nickName: user.nick_name, nameDialog: false })
      wx.showToast({ title: '姓名已保存' })
    } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
  },
  async changeDefault(e) {
    if (this.data.saving) return
    this.setData({ saving: true })
    try {
      const type = e.detail.value
      await request('/profile/settings', 'PUT', { default_bill_type: type })
      this.setData({ defaultType: type })
      wx.showToast({ title: '默认类型已保存' })
    } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
  },
  onChooseAvatar(e) { this.saveAvatar(e.detail.avatarUrl) },
  chooseImage() {
    if (this.data.saving) return
    wx.chooseImage({ count: 1, sizeType: ['compressed'], success: result => this.saveAvatar(result.tempFilePaths[0]) })
  },
  async saveAvatar(path) {
    if (!path || this.data.saving) return
    this.setData({ saving: true })
    try {
      const result = await request('/profile/avatar', 'POST', {}, path)
      this.setData({ avatarUrl: mediaUrl(result.avatar_url) })
      wx.showToast({ title: '头像已保存' })
    } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
  },
  addCategory() {
    if (!this.data.saving) this.setData({ categoryDialog: true, editingCategoryId: null, draftName: '' })
  },
  editCategory(e) {
    if (this.data.saving) return
    const category = this.data.categories.find(item => item.id === Number(e.currentTarget.dataset.id))
    if (category && !category.is_system) {
      this.setData({ categoryDialog: true, editingCategoryId: category.id, draftName: category.name })
    }
  },
  async saveCategory() {
    if (this.data.saving) return
    const name = this.data.draftName.trim()
    if (!name) { this.showError(new Error('请输入类别名称')); return }
    const id = this.data.editingCategoryId
    this.setData({ saving: true })
    try {
      await request(id ? `/categories/${id}` : '/categories', id ? 'PUT' : 'POST',
        { name, type: this.data.categoryType })
      this.setData({ categoryDialog: false })
      await this.loadCategories()
      wx.showToast({ title: '类别已保存' })
    } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
  },
  deleteCategory(e) {
    if (this.data.saving) return
    const id = Number(e.currentTarget.dataset.id)
    wx.showModal({ title: '删除类别', content: '删除后，该类别的历史账单仍保留原来的分类名称。',
      success: async result => {
        if (!result.confirm || this.data.saving) return
        this.setData({ saving: true })
        try {
          await request(`/categories/${id}`, 'DELETE')
          await this.loadCategories()
          wx.showToast({ title: '类别已删除' })
        } catch (error) { this.showError(error) } finally { this.setData({ saving: false }) }
      }
    })
  },
  showError(error) { wx.showToast({ title: error.message || '操作失败，请重试', icon: 'none' }) }
})
