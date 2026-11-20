import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Centralized response error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let friendlyMessage = 'An unexpected error occurred. Please try again.'
    let errorCode = null
    let errorDetails = null

    if (error.response?.data?.error) {
      const errObj = error.response.data.error
      friendlyMessage = errObj.message || friendlyMessage
      errorCode = errObj.code || null
      errorDetails = errObj.details || null
    } else if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      if (typeof detail === 'string') {
        friendlyMessage = detail
      } else if (detail.error?.message) {
        friendlyMessage = detail.error.message
        errorCode = detail.error.code
        errorDetails = detail.error.details
      }
    } else if (error.message) {
      friendlyMessage = error.message
    }

    const enhancedError = new Error(friendlyMessage)
    enhancedError.code = errorCode
    enhancedError.details = errorDetails
    enhancedError.status = error.response?.status
    enhancedError.originalError = error

    return Promise.reject(enhancedError)
  }
)

// API methods
export const api = {
  // Health
  checkHealth: async () => {
    const res = await apiClient.get('/health')
    return res.data
  },

  // Profile
  getProfile: async () => {
    const res = await apiClient.get('/profile')
    return res.data
  },
  updateProfile: async (profileData) => {
    const res = await apiClient.put('/profile', profileData)
    return res.data
  },

  // Medications
  getMedications: async () => {
    const res = await apiClient.get('/medications')
    return res.data
  },
  createMedication: async (medicationData) => {
    const res = await apiClient.post('/medications', medicationData)
    return res.data
  },
  updateMedication: async (id, medicationData) => {
    const res = await apiClient.put(`/medications/${id}`, medicationData)
    return res.data
  },
  deleteMedication: async (id) => {
    const res = await apiClient.delete(`/medications/${id}`)
    return res.data
  },

  // Care Episodes
  getEpisodes: async () => {
    const res = await apiClient.get('/episodes')
    return res.data
  },
  createEpisode: async (episodeData) => {
    const res = await apiClient.post('/episodes', episodeData)
    return res.data
  },
  updateEpisode: async (id, episodeData) => {
    const res = await apiClient.put(`/episodes/${id}`, episodeData)
    return res.data
  },
  deleteEpisode: async (id) => {
    const res = await apiClient.delete(`/episodes/${id}`)
    return res.data
  },

  // Episode Progress Updates
  getEpisodeUpdates: async (episodeId) => {
    const res = await apiClient.get(`/episodes/${episodeId}/updates`)
    return res.data
  },
  createEpisodeUpdate: async (episodeId, updateData) => {
    const res = await apiClient.post(`/episodes/${episodeId}/updates`, updateData)
    return res.data
  },
  deleteEpisodeUpdate: async (episodeId, updateId) => {
    const res = await apiClient.delete(`/episodes/${episodeId}/updates/${updateId}`)
    return res.data
  },

  // Documents
  getDocuments: async () => {
    const res = await apiClient.get('/documents')
    return res.data
  },
  uploadDocument: async (file, onUploadProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    })
    return res.data
  },
  deleteDocument: async (id) => {
    const res = await apiClient.delete(`/documents/${id}`)
    return res.data
  },

  // Health Copilot / Chat
  sendMessage: async ({ message, document_ids = [], episode_id = null }) => {
    const res = await apiClient.post('/chat', {
      message,
      document_ids,
      episode_id,
    })
    return res.data
  },
}

export default api
