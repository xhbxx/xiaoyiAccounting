const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const source = fs.readFileSync(path.join(__dirname, '../miniprogram/pages/discover/discover.js'), 'utf8')
function createPage(budget) {
  let definition
  vm.runInNewContext(source, {
    Page: value => { definition = value },
    require: () => ({ request: async () => ({ ledger: { id: 1, name: '默认账本' },
      period: { income: '0.00', expense: '113.00' }, budget }) })
  })
  return { ...definition, data: { ...definition.data, budget },
    setData(values) { Object.assign(this.data, values) } }
}

for (const [percent, expected, right, left] of [
  [0, 0, -135, 45], [25, 25, -45, 45], [50, 50, 45, 45],
  [75, 75, 45, 135], [100, 100, 45, 225],
  [-10, 0, -135, 45], [120, 100, 45, 225], ['invalid', 0, -135, 45]
]) {
  test(`剩余比例 ${percent} 对应圆环和中心文字`, () => {
    const page = createPage({ remaining_percent: percent })
    page.updateBudgetRing()
    assert.equal(page.data.remainingPercent, expected)
    assert.equal(page.data.rightRotation, right)
    assert.equal(page.data.leftRotation, left)
  })
}

test('预算接口加载后刷新圆环', async () => {
  const page = createPage({ amount: '1000.00', remaining: '887.00', remaining_percent: 88.7 })
  await page.loadMonth()
  assert.equal(page.data.remainingPercent, 89)
  assert.equal(page.data.rightRotation, 45)
  assert.ok(Math.abs(page.data.leftRotation - 184.32) < 0.0001)
  assert.equal(page.data.loadError, '')
})

test('未设置预算时显示空环', () => {
  const page = createPage(null)
  page.updateBudgetRing()
  assert.equal(page.data.remainingPercent, 0)
  assert.equal(page.data.rightRotation, -135)
  assert.equal(page.data.leftRotation, 45)
})

test('打开关闭弹窗保留圆环显示状态', () => {
  const page = createPage({ remaining_percent: 75 })
  page.updateBudgetRing()
  page.openBudget()
  page.closeBudget()
  assert.equal(page.data.remainingPercent, 75)
  assert.equal(page.data.showBudgetDialog, false)
})
