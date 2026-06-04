<template>
  <div class="card">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold">Estatísticas</h2>
      <button @click="refresh" class="btn btn-secondary text-sm">
        Atualizar
      </button>
    </div>

    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="bg-gray-700 rounded-lg p-3">
        <div class="text-xs text-gray-400">Tempo Hoje</div>
        <div class="text-lg font-bold text-green-400">{{ stats.total_today }}</div>
      </div>
      <div class="bg-gray-700 rounded-lg p-3">
        <div class="text-xs text-gray-400">Tempo Semana</div>
        <div class="text-lg font-bold text-blue-400">{{ stats.total_week }}</div>
      </div>
      <div class="bg-gray-700 rounded-lg p-3">
        <div class="text-xs text-gray-400">Tempo Mês</div>
        <div class="text-lg font-bold text-purple-400">{{ stats.total_month }}</div>
      </div>
      <div class="bg-gray-700 rounded-lg p-3">
        <div class="text-xs text-gray-400">Demandas Ativas</div>
        <div class="text-lg font-bold text-yellow-400">{{ stats.active_count }}</div>
      </div>
      <div class="bg-gray-700 rounded-lg p-3">
        <div class="text-xs text-gray-400">Finalizadas Hoje</div>
        <div class="text-lg font-bold">{{ stats.demands_today }}</div>
      </div>
      <div class="bg-gray-700 rounded-lg p-3">
        <div class="text-xs text-gray-400">Finalizadas Semana</div>
        <div class="text-lg font-bold">{{ stats.demands_week }}</div>
      </div>
      <div class="bg-gray-700 rounded-lg p-3 col-span-2">
        <div class="text-xs text-gray-400">Tempo Médio por Demanda</div>
        <div class="text-lg font-bold">{{ stats.avg_time }}</div>
      </div>
    </div>

    <!-- Category Chart -->
    <div v-if="stats && stats.category_times">
      <h3 class="text-sm font-medium text-gray-400 mb-3">Tempo por Categoria</h3>
      <div class="space-y-2">
        <div v-for="(time, category) in stats.category_times" :key="category" class="flex items-center gap-3">
          <div class="w-20 text-sm">{{ category }}</div>
          <div class="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
            <div
              class="h-full rounded-full flex items-center justify-end pr-2 text-xs font-medium"
              :class="getCategoryColor(category)"
              :style="{ width: getBarWidth(time) }"
            >
              {{ time }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center text-gray-400 py-8">
      Carregando estatísticas...
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useDemandsStore } from '../stores/demands'

const store = useDemandsStore()

const stats = computed(() => store.stats)

function refresh() {
  store.fetchStats()
}

function getCategoryColor(category) {
  switch (category) {
    case 'Sprint': return 'bg-blue-600'
    case 'Furacão': return 'bg-red-600'
    case 'Meta': return 'bg-purple-600'
    case 'Extra': return 'bg-gray-600'
    default: return 'bg-gray-600'
  }
}

function getBarWidth(timeStr) {
  // Parse time string "XXh YYm ZZs" to seconds
  const match = timeStr.match(/(\d+)h\s*(\d+)m\s*(\d+)s/)
  if (!match) return '0%'

  const seconds = parseInt(match[1]) * 3600 + parseInt(match[2]) * 60 + parseInt(match[3])

  // Find max time
  const allTimes = Object.values(store.stats.category_times).map(t => {
    const m = t.match(/(\d+)h\s*(\d+)m\s*(\d+)s/)
    return m ? parseInt(m[1]) * 3600 + parseInt(m[2]) * 60 + parseInt(m[3]) : 0
  })
  const maxTime = Math.max(...allTimes, 1)

  return `${Math.max(10, (seconds / maxTime) * 100)}%`
}

onMounted(() => {
  store.fetchStats()
})
</script>
