import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Em produção, usa a URL da API do Render; em dev, usa proxy local
const API_BASE = import.meta.env.VITE_API_URL || '/api'

export const useDemandsStore = defineStore('demands', () => {
  // State
  const demands = ref([])
  const categories = ref([])
  const stats = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const ws = ref(null)

  // Filters
  const searchQuery = ref('')
  const statusFilter = ref('Todos')
  const categoryFilter = ref('Todas')

  // Computed
  const filteredDemands = computed(() => {
    return demands.value.filter(d => {
      // Search filter
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        if (!d.name.toLowerCase().includes(query) && !d.card.toLowerCase().includes(query)) {
          return false
        }
      }

      // Status filter
      if (statusFilter.value !== 'Todos' && d.status !== statusFilter.value) {
        return false
      }

      // Category filter
      if (categoryFilter.value !== 'Todas' && d.category !== categoryFilter.value) {
        return false
      }

      return true
    })
  })

  // Actions
  async function fetchDemands() {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/demands`)
      demands.value = await res.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories() {
    try {
      const res = await fetch(`${API_BASE}/categories`)
      categories.value = await res.json()
    } catch (e) {
      console.error('Error fetching categories:', e)
    }
  }

  async function fetchStats() {
    try {
      const res = await fetch(`${API_BASE}/stats`)
      stats.value = await res.json()
    } catch (e) {
      console.error('Error fetching stats:', e)
    }
  }

  async function createDemand(name, card, category) {
    try {
      const res = await fetch(`${API_BASE}/demands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, card, category })
      })
      const newDemand = await res.json()
      demands.value.push(newDemand)
      return newDemand
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function startDemand(id) {
    try {
      const res = await fetch(`${API_BASE}/demands/${id}/start`, { method: 'POST' })
      const updated = await res.json()
      updateDemandInList(updated)
      return updated
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function pauseDemand(id) {
    try {
      const res = await fetch(`${API_BASE}/demands/${id}/pause`, { method: 'POST' })
      const updated = await res.json()
      updateDemandInList(updated)
      return updated
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function stopDemand(id, description) {
    try {
      const res = await fetch(`${API_BASE}/demands/${id}/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description })
      })
      const updated = await res.json()
      updateDemandInList(updated)
      return updated
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function deleteDemand(id) {
    try {
      await fetch(`${API_BASE}/demands/${id}`, { method: 'DELETE' })
      demands.value = demands.value.filter(d => d.id !== id)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function updateTime(id, timeSeconds) {
    try {
      const res = await fetch(`${API_BASE}/demands/${id}/time`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ time_seconds: timeSeconds })
      })
      const updated = await res.json()
      updateDemandInList(updated)
      return updated
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function updateDescription(id, description) {
    try {
      const res = await fetch(`${API_BASE}/demands/${id}/description?description=${encodeURIComponent(description)}`, {
        method: 'PATCH'
      })
      const updated = await res.json()
      updateDemandInList(updated)
      return updated
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function clearFinalized() {
    try {
      await fetch(`${API_BASE}/demands/finalized/clear`, { method: 'DELETE' })
      demands.value = demands.value.filter(d => d.status !== 'finalizada')
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function getReport(startDate, endDate) {
    try {
      const res = await fetch(`${API_BASE}/reports?start_date=${startDate}&end_date=${endDate}`)
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  function updateDemandInList(updated) {
    const index = demands.value.findIndex(d => d.id === updated.id)
    if (index !== -1) {
      demands.value[index] = updated
    }
  }

  // WebSocket
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/timers`

    ws.value = new WebSocket(wsUrl)

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'timers') {
        // Update timer values
        for (const [id, timer] of Object.entries(data.data)) {
          const demand = demands.value.find(d => d.id === parseInt(id))
          if (demand) {
            demand.current_elapsed_time = timer.current_elapsed_time
            demand.status = timer.status
          }
        }
      }
    }

    ws.value.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
  }

  function clearFilters() {
    searchQuery.value = ''
    statusFilter.value = 'Todos'
    categoryFilter.value = 'Todas'
  }

  // Format time helper
  function formatTime(seconds) {
    const s = Math.floor(seconds || 0)
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = s % 60
    return `${h.toString().padStart(2, '0')}h ${m.toString().padStart(2, '0')}m ${sec.toString().padStart(2, '0')}s`
  }

  return {
    // State
    demands,
    categories,
    stats,
    loading,
    error,
    searchQuery,
    statusFilter,
    categoryFilter,

    // Computed
    filteredDemands,

    // Actions
    fetchDemands,
    fetchCategories,
    fetchStats,
    createDemand,
    startDemand,
    pauseDemand,
    stopDemand,
    deleteDemand,
    updateTime,
    updateDescription,
    clearFinalized,
    getReport,
    connectWebSocket,
    clearFilters,
    formatTime
  }
})
