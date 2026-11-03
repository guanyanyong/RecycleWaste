export const TRIP_STATUS = {
  0: { text: '进行中', type: 'info' },
  1: { text: '称重完成', type: 'warning' },
  2: { text: '已结算', type: 'success' },
  3: { text: '已作废', type: 'danger' }
}

export const ITEM_STATUS = {
  0: { text: '新建', type: 'info' },
  1: { text: '已核价', type: 'warning' },
  2: { text: '称重完成', type: 'primary' },
  3: { text: '已结算', type: 'success' },
  4: { text: '已作废', type: 'danger' }
}

export const PAY_STATUS = {
  0: { text: '未结', type: 'danger' },
  1: { text: '部分结清', type: 'warning' },
  2: { text: '已结清', type: 'success' }
}

export const BIZ_TYPE = {
  1: '收货',
  2: '发货'
}

export function tripStatus(v) {
  return TRIP_STATUS[v]?.text || '-'
}
export function tripTagType(v) {
  return TRIP_STATUS[v]?.type || 'info'
}
export function itemStatus(v) {
  return ITEM_STATUS[v]?.text || '-'
}
export function itemTagType(v) {
  return ITEM_STATUS[v]?.type || 'info'
}
export function payStatus(v) {
  return PAY_STATUS[v]?.text || '-'
}
export function payTagType(v) {
  return PAY_STATUS[v]?.type || 'info'
}

export function money(v) {
  const n = Number(v || 0)
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
export function weight(v) {
  if (v === null || v === undefined || v === '') return '-'
  return Number(v).toFixed(2)
}
export function percent(v) {
  if (v === null || v === undefined) return '-'
  return (Number(v) * 100).toFixed(2) + '%'
}
