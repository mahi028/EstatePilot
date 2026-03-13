import api from './api'

const apiOrigin = api.defaults.baseURL.replace(/\/api\/?$/, '')
export const getUploadUrl = (filePath) => `${apiOrigin}/${String(filePath || '').replace(/^\/+/, '')}`

// ── Manager endpoints ──
export const fetchManagedTenants = () => api.get('/manager/tenants')
export const fetchManagedTickets = (params = {}) => api.get('/manager/tickets', { params })
export const fetchManagedTicketDetail = (ticketId) => api.get(`/manager/tickets/${ticketId}`)
export const addManagedTicketComment = (ticketId, body) => api.post(`/manager/tickets/${ticketId}/comments`, { body })
export const markManagedTicketInvalid = (ticketId) => api.patch(`/manager/tickets/${ticketId}/invalid`)
export const fetchSentInvitations = (params = {}) => api.get('/manager/invitations/sent', { params })
export const searchTenants = (q) => api.get('/manager/tenants/search', { params: { q } })
export const sendInvitation = (tenantId) => api.post('/manager/invitations', { tenant_id: tenantId })
export const removeManagedTenant = (tenantId) => api.delete(`/manager/tenants/${tenantId}`)

// ── Tenant endpoints ──
export const fetchTenantTickets = (params = {}) => api.get('/tenant/tickets', { params })
export const createTicket = (payload) => api.post('/tenant/tickets', payload)
export const fetchTicketDetail = (ticketId) => api.get(`/tenant/tickets/${ticketId}`)
export const updateTicket = (ticketId, payload) => api.patch(`/tenant/tickets/${ticketId}`, payload)
export const deleteTicket = (ticketId) => api.delete(`/tenant/tickets/${ticketId}`)
export const addTenantTicketComment = (ticketId, body) => api.post(`/tenant/tickets/${ticketId}/comments`, { body })
export const uploadTicketImage = (ticketId, file) => {
  const formData = new FormData()
  formData.append('image', file)
  return api.post(`/tenant/tickets/${ticketId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const deleteTicketImage = (ticketId, imageId) => api.delete(`/tenant/tickets/${ticketId}/images/${imageId}`)
export const fetchTenantNotifications = () => api.get('/tenant/notifications')
export const markNotificationRead = (id) => api.patch(`/tenant/notifications/${id}`)
export const fetchMyNotifications = (params = {}) => api.get('/notifications', { params })
export const markMyNotificationRead = (id) => api.patch(`/notifications/${id}`)
export const fetchReceivedInvitations = (params = {}) => api.get('/tenant/invitations', { params })
export const respondToInvitation = (id, action) => api.patch(`/tenant/invitations/${id}`, { action })
export const removeMyManager = () => api.delete('/tenant/manager')

// ── Profile / Technician endpoints ──
export const updateProfile = (payload) => api.patch('/auth/profile', payload)
export const uploadProfileImage = (file) => {
  const formData = new FormData()
  formData.append('image', file)
  return api.post('/auth/profile/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const fetchTechnicianServices = () => api.get('/technician/services')
export const fetchUserProfile = (userId) => api.get(`/users/${userId}/profile`)
export const createTechnicianReview = (technicianId, payload) => api.post(`/technicians/${technicianId}/reviews`, payload)

// ── Technician ticket endpoints ──
export const fetchTechnicianTickets = (params = {}) => api.get('/technician/tickets', { params })
export const fetchTechnicianTicketDetail = (ticketId) => api.get(`/technician/tickets/${ticketId}`)
export const acceptTechnicianTicket = (ticketId) => api.patch(`/technician/tickets/${ticketId}/accept`)
export const rejectTechnicianTicket = (ticketId) => api.patch(`/technician/tickets/${ticketId}/reject`)
export const updateTechnicianTicketStatus = (ticketId, status) => api.patch(`/technician/tickets/${ticketId}/status`, { status })
export const addTechnicianTicketComment = (ticketId, body) => api.post(`/technician/tickets/${ticketId}/comments`, { body })
export const fetchTechnicianServiceAreaTickets = (params = {}) => api.get('/technician/tickets/service-area', { params })
export const fetchTechnicianServiceAreaTicketDetail = (ticketId) => api.get(`/technician/tickets/service-area/${ticketId}`)
export const submitTechnicianBid = (ticketId, payload) => api.post(`/technician/tickets/${ticketId}/bids`, payload)

// ── Manager technician search & assignment ──
export const searchTechnicians = (q, serviceId = null) => {
  const params = {}
  if (q) params.q = q
  if (serviceId) params.service_id = serviceId
  return api.get('/manager/technicians/search', { params })
}
export const fetchManagerTicketBids = (ticketId) => api.get(`/manager/tickets/${ticketId}/bids`)
export const assignTechnicianToTicket = (ticketId, technicianId) => api.patch(`/manager/tickets/${ticketId}/assign`, { technician_id: technicianId })
