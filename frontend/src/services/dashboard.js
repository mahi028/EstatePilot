import api from './api'

// ── Manager endpoints ──
export const fetchManagedTenants = () => api.get('/manager/tenants')
export const fetchManagedTickets = (params = {}) => api.get('/manager/tickets', { params })
export const fetchSentInvitations = (params = {}) => api.get('/manager/invitations/sent', { params })
export const searchTenants = (q) => api.get('/manager/tenants/search', { params: { q } })
export const sendInvitation = (tenantId) => api.post('/manager/invitations', { tenant_id: tenantId })

// ── Tenant endpoints ──
export const fetchTenantTickets = (params = {}) => api.get('/tenant/tickets', { params })
export const createTicket = (payload) => api.post('/tenant/tickets', payload)
export const fetchTenantNotifications = () => api.get('/tenant/notifications')
export const markNotificationRead = (id) => api.patch(`/tenant/notifications/${id}`)
export const fetchReceivedInvitations = (params = {}) => api.get('/tenant/invitations', { params })
export const respondToInvitation = (id, action) => api.patch(`/tenant/invitations/${id}`, { action })
