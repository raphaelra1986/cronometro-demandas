<template>
  <div class="min-h-screen bg-gray-900 text-white">
    <!-- Header -->
    <header class="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div class="max-w-6xl mx-auto flex justify-between items-center">
        <h1 class="text-xl font-bold">⏱️ Cronômetro de Demandas</h1>
        <div class="flex gap-4">
          <button
            @click="activeTab = 'demands'"
            :class="[
              'px-4 py-2 rounded-lg transition-colors',
              activeTab === 'demands' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-white'
            ]"
          >
            Demandas
          </button>
          <button
            @click="activeTab = 'stats'"
            :class="[
              'px-4 py-2 rounded-lg transition-colors',
              activeTab === 'stats' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-white'
            ]"
          >
            Estatísticas
          </button>
          <button
            @click="activeTab = 'reports'"
            :class="[
              'px-4 py-2 rounded-lg transition-colors',
              activeTab === 'reports' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-white'
            ]"
          >
            Relatórios
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto p-6">
      <!-- Demands Tab -->
      <div v-show="activeTab === 'demands'">
        <DemandForm />
        <FilterBar @clear-finalized="handleClearFinalized" />

        <div v-if="store.loading" class="text-center py-8 text-gray-400">
          Carregando demandas...
        </div>

        <div v-else-if="store.filteredDemands.length === 0" class="text-center py-8 text-gray-400">
          Nenhuma demanda encontrada.
        </div>

        <div v-else>
          <DemandCard
            v-for="demand in store.filteredDemands"
            :key="demand.id"
            :demand="demand"
            @start="handleStart"
            @pause="handlePause"
            @stop="handleStop"
            @delete="handleDelete"
            @update-time="handleUpdateTime"
            @update-description="handleUpdateDescription"
          />
        </div>
      </div>

      <!-- Stats Tab -->
      <div v-show="activeTab === 'stats'">
        <StatsPanel />
      </div>

      <!-- Reports Tab -->
      <div v-show="activeTab === 'reports'">
        <ReportPanel />
      </div>
    </main>

    <!-- Footer -->
    <footer class="text-center py-4 text-gray-500 text-sm">
      Cronômetro de Demandas v2.0 - Web App
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useDemandsStore } from './stores/demands'
import DemandForm from './components/DemandForm.vue'
import FilterBar from './components/FilterBar.vue'
import DemandCard from './components/DemandCard.vue'
import StatsPanel from './components/StatsPanel.vue'
import ReportPanel from './components/ReportPanel.vue'

const store = useDemandsStore()
const activeTab = ref('demands')

onMounted(async () => {
  await store.fetchCategories()
  await store.fetchDemands()
  store.connectWebSocket()
})

async function handleStart(id) {
  try {
    await store.startDemand(id)
  } catch (e) {
    alert('Erro ao iniciar: ' + e.message)
  }
}

async function handlePause(id) {
  try {
    await store.pauseDemand(id)
  } catch (e) {
    alert('Erro ao pausar: ' + e.message)
  }
}

async function handleStop(id, description) {
  try {
    await store.stopDemand(id, description)
  } catch (e) {
    alert('Erro ao finalizar: ' + e.message)
  }
}

async function handleDelete(id) {
  if (!confirm('Deseja realmente excluir esta demanda?')) return
  try {
    await store.deleteDemand(id)
  } catch (e) {
    alert('Erro ao excluir: ' + e.message)
  }
}

async function handleUpdateTime(id, seconds) {
  try {
    await store.updateTime(id, seconds)
  } catch (e) {
    alert('Erro ao atualizar tempo: ' + e.message)
  }
}

async function handleUpdateDescription(id, description) {
  try {
    await store.updateDescription(id, description)
  } catch (e) {
    alert('Erro ao atualizar descrição: ' + e.message)
  }
}

async function handleClearFinalized() {
  if (!confirm('Deseja remover todas as demandas finalizadas?')) return
  try {
    await store.clearFinalized()
  } catch (e) {
    alert('Erro ao limpar: ' + e.message)
  }
}
</script>
