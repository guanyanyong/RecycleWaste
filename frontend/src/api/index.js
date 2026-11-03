import http from './http'

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  refresh: () => http.post('/auth/refresh'),
  logout: () => http.post('/auth/logout'),
  me: () => http.get('/auth/me')
}

export const dashboardApi = {
  overview: () => http.get('/dashboard/overview'),
  trend: (days = 7) => http.get('/dashboard/trend', { params: { days } }),
  materialDistribution: (days = 30) => http.get('/dashboard/material-distribution', { params: { days } }),
  stationDistribution: () => http.get('/dashboard/station-distribution'),
  recentTrips: () => http.get('/dashboard/recent-trips')
}

export const weighApi = {
  createTrip: (data) => http.post('/weigh/trips', data),
  listTrips: (params) => http.get('/weigh/trips', { params }),
  activeTrips: (params) => http.get('/weigh/trips/active', { params }),
  tripDetail: (id) => http.get(`/weigh/trips/${id}`),
  cancelTrip: (id) => http.post(`/weigh/trips/${id}/cancel`),
  addItem: (tripId, data) => http.post(`/weigh/trips/${tripId}/items`, data),
  pendingItems: (params) => http.get('/weigh/items/pending', { params }),
  unsettledItems: (params) => http.get('/weigh/items/unsettled', { params }),
  price: (itemId, data) => http.post(`/weigh/items/${itemId}/price`, data),
  complete: (itemId, data) => http.post(`/weigh/items/${itemId}/complete`, data),
  cancel: (itemId) => http.post(`/weigh/items/${itemId}/cancel`)
}

export const settleApi = {
  create: (data) => http.post('/settlements', data),
  list: (params) => http.get('/settlements', { params }),
  detail: (id) => http.get(`/settlements/${id}`),
  pay: (id, data) => http.post(`/settlements/${id}/pay`, data),
  cancel: (id) => http.post(`/settlements/${id}/cancel`)
}

export const basicApi = {
  materials: (params) => http.get('/materials', { params }),
  createMaterial: (data) => http.post('/materials', data),
  updateMaterial: (id, data) => http.put(`/materials/${id}`, data),
  categories: () => http.get('/categories/tree'),
  createCategory: (data) => http.post('/categories', data),
  stations: () => http.get('/stations'),
  createStation: (data) => http.post('/stations', data),
  updateStation: (id, data) => http.put(`/stations/${id}`, data),
  customers: (params) => http.get('/customers', { params }),
  searchCustomers: (params) => http.get('/customers/search', { params }),
  createCustomer: (data) => http.post('/customers', data),
  updateCustomer: (id, data) => http.put(`/customers/${id}`, data),
  deductRules: () => http.get('/deduct-rules'),
  saveDeductRule: (data, ruleId) => http.post('/deduct-rules', data, { params: { rule_id: ruleId } }),
  users: (params) => http.get('/users', { params }),
  createUser: (data) => http.post('/users', data),
  updateUser: (id, data) => http.put(`/users/${id}`, data),
  roles: () => http.get('/roles'),
  permissions: () => http.get('/permissions')
}

export const reportApi = {
  daily: (params) => http.get('/reports/daily', { params })
}
