const { mediaUrl } = require('./config.js')

const categoryIcons = [
  { name: '餐饮', icon: 'food' },
  { name: '交通', icon: 'transport' },
  { name: '购物', icon: 'shopping' },
  { name: '娱乐', icon: 'entertainment' },
  { name: '住房', icon: 'house' },
  { name: '医疗', icon: 'medical' },
  { name: '学习', icon: 'study' },
  { name: '工资', icon: 'salary' },
  { name: '兼职', icon: 'parttime' },
  { name: '红包', icon: 'redpacket' },
  { name: '理财', icon: 'finance' }
]

function categoryImage(value, selected = false) {
  const category = typeof value === 'string' ? { name: value } : value || {}
  if (category.icon && category.icon.startsWith('/uploads/icons/')) return mediaUrl(category.icon)
  const preset = categoryIcons.find(item => item.icon === category.icon)
    || categoryIcons.find(item => item.name === category.name)
  return preset ? `/images/${preset.name}${selected ? '1' : ''}.png` : '/images/bill.png'
}

module.exports = { categoryImage, categoryIcons }
