const { request } = require('../../utils/config.js')
const echarts = require('../../ec-canvas/echarts')

function emptyStatistics() {
  return { index: 0, label: '', total: '0.00', average: '0.00', trend: [], ranking: [] }
}

Page({
  data: {
    ec: { lazyLoad: true },
    choise: ['支出', '收入'],
    choiseIndex: 0,
    choised: '支出',
    activeIndex: 0,
    statisticsData: { items: [], current_index: 0 },
    currentStatistics: emptyStatistics(),
    selectedPeriodIndex: 0,
    periodScrollLeft: 0,
    loading: false,
    loadError: ''
  },

  onChange(e) {
    const index = Number(e.detail.value)
    this.setData({ choiseIndex: index, choised: this.data.choise[index] })
    this.loadStatistics()
  },
  switchTime(e) {
    this.setData({ activeIndex: Number(e.currentTarget.dataset.index) })
    this.loadStatistics()
  },
  formatDate(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
  },
  async loadStatistics() {
    const requestId = (this.statisticsRequestId || 0) + 1
    this.statisticsRequestId = requestId
    const type = this.data.choised === '支出' ? 'expense' : 'income'
    const period = ['week', 'month', 'year'][this.data.activeIndex]
    const date = this.formatDate(new Date())
    this.setData({ loading: true, loadError: '' })
    try {
      const result = await request(`/statistics?type=${type}&period=${period}&date=${date}`)
      if (requestId !== this.statisticsRequestId) return
      this.setData({ statisticsData: result })
      this.applyPeriod(result.current_index)
    } catch (error) {
      if (requestId === this.statisticsRequestId) {
        this.setData({ loadError: error.message || '统计加载失败，请重试' })
      }
    } finally {
      if (requestId === this.statisticsRequestId) this.setData({ loading: false })
    }
  },
  selectPeriod(e) {
    this.applyPeriod(Number(e.currentTarget.dataset.index))
  },
  applyPeriod(index) {
    const items = this.data.statisticsData.items
    const position = items.findIndex(item => item.index === index)
    const currentStatistics = items[position] || emptyStatistics()
    const windowWidth = wx.getWindowInfo().windowWidth
    const itemWidth = 150 * windowWidth / 750
    const maxScroll = Math.max(0, items.length * itemWidth - windowWidth)
    const scrollLeft = position * itemWidth - (windowWidth - itemWidth) / 2
    this.setData({
      selectedPeriodIndex: index,
      currentStatistics,
      periodScrollLeft: Math.max(0, Math.min(maxScroll, scrollLeft))
    })
    this.updateChart()
  },
  updateChart() {
    if (!this.trendChart) return
    const trend = this.data.currentStatistics.trend
    this.trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 20, right: 24, top: 30, bottom: 24, containLabel: true },
      xAxis: { type: 'category', data: trend.map(item => item.label) },
      yAxis: { type: 'value', min: 0 },
      series: [{ name: this.data.choised, type: 'line',
        data: trend.map(item => Number(item.amount)),
        itemStyle: { color: '#b78b00' }, lineStyle: { color: '#b78b00' } }]
    })
  },
  onReady() {
    this.selectComponent('#trendChart').init((canvas, width, height, dpr) => {
      const chart = echarts.init(canvas, null, { width, height, devicePixelRatio: dpr })
      canvas.setChart(chart)
      this.trendChart = chart
      this.updateChart()
      return chart
    })
  },
  onShow() {
    const tabBar = this.getTabBar && this.getTabBar()
    if (tabBar) tabBar.setData({ active: 1, hidden: false })
    this.loadStatistics()
  },
  onUnload() {
    this.statisticsRequestId = (this.statisticsRequestId || 0) + 1
    if (this.trendChart) this.trendChart.dispose()
    this.trendChart = null
  }
})
