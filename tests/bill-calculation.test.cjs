const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

const billDirectory = path.join(__dirname, '../miniprogram/pages/bill')
const source = fs.readFileSync(path.join(billDirectory, 'bill.js'), 'utf8')

function createPage() {
  let definition
  const requests = []
  const messages = []
  vm.runInNewContext(source, {
    Page: value => { definition = value },
    require: name => name.includes('config')
      ? { request: async (url, method, data) => { requests.push({ url, method, data }) } }
      : require(path.resolve(billDirectory, name)),
    wx: { showToast: value => messages.push(value.title), switchTab() {} }
  })
  const page = {
    ...definition,
    data: { ...definition.data, selectedName: '餐饮', date: '2026-11-04' },
    setData(values) { Object.assign(this.data, values) }
  }
  return { page, requests, messages }
}

function enter(page, expression) {
  for (const key of expression) {
    if (key === '+' || key === '-') {
      page.onOperatorTap({ currentTarget: { dataset: { operator: key } } })
    } else {
      page.onKeyTap({ currentTarget: { dataset: { key } } })
    }
  }
}

for (const [expression, expected] of [
  ['12+3-2', '13.00'], ['0.1+0.2', '0.30'], ['1-2+3', '2.00'],
  ['10+-2', '8.00'], ['.5+.25', '0.75'], ['9.99+0.01', '10.00'],
  ['9999999999.99+0.01-0.01', '9999999999.99'], ['18.50', '18.50']
]) {
  test(`完成后提交计算结果 ${expression} = ${expected}`, async () => {
    const { page, requests } = createPage()
    enter(page, expression)
    await page.submitBill()
    assert.equal(requests.length, 1)
    assert.equal(requests[0].data.amount, expected)
  })
}

for (const expression of ['12+', '1-2', '1-1', '9999999999.99+0.01']) {
  test(`拦截未完成或超出金额范围的计算 ${expression}`, async () => {
    const { page, requests, messages } = createPage()
    enter(page, expression)
    const draft = page.data.amount
    await page.submitBill()
    assert.equal(requests.length, 0)
    assert.equal(page.data.amount, draft)
    assert.equal(messages.length, 1)
  })
}

test('退格可删除数字与运算符，每个数字保留两位小数', async () => {
  const { page, requests } = createPage()
  enter(page, '1.234+5')
  assert.equal(page.data.amount, '1.23+5')
  page.onKeyDelete()
  page.onKeyDelete()
  assert.equal(page.data.amount, '1.23')
  enter(page, '+.2')
  await page.submitBill()
  assert.equal(requests[0].data.amount, '1.43')
})

test('保存过程中金额键盘保持锁定', () => {
  const { page } = createPage()
  enter(page, '12+3')
  page.setData({ submitting: true })
  enter(page, '-4')
  page.onKeyDelete()
  assert.equal(page.data.amount, '12+3')
})

test('编辑账单继续复用原提交入口', async () => {
  const { page, requests } = createPage()
  page.setData({ editingId: 9, amount: '12.00' })
  enter(page, '+3')
  await page.submitBill()
  assert.equal(requests[0].url, '/bills/9')
  assert.equal(requests[0].method, 'PUT')
  assert.equal(requests[0].data.amount, '15.00')
})
