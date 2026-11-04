const names = ['餐饮', '交通', '购物', '娱乐', '住房', '医疗', '学习', '工资', '兼职', '红包', '理财']

function categoryImage(name, selected = false) {
  return names.includes(name) ? `/images/${name}${selected ? '1' : ''}.png` : '/images/bill.png'
}

module.exports = { categoryImage }
