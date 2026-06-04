<template>
  <div class="card">
    <h2 class="text-lg font-semibold mb-4">Relatórios</h2>

    <div class="flex flex-wrap gap-3 items-end mb-4">
      <div>
        <label class="block text-xs text-gray-400 mb-1">Data Início</label>
        <input v-model="startDate" type="date" class="input w-40" />
      </div>
      <div>
        <label class="block text-xs text-gray-400 mb-1">Data Fim</label>
        <input v-model="endDate" type="date" class="input w-40" />
      </div>
      <button @click="generateReport" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Gerando...' : 'Gerar Relatório' }}
      </button>
      <button @click="exportCSV" class="btn btn-secondary" :disabled="!reportData.length">
        Exportar CSV
      </button>
    </div>

    <div v-if="reportData.length" class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-700">
            <th class="text-left py-2 px-3">Nome</th>
            <th class="text-left py-2 px-3">Card</th>
            <th class="text-left py-2 px-3">Tempo</th>
            <th class="text-left py-2 px-3">Descrição</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in reportData" :key="idx" class="border-b border-gray-700/50">
            <td class="py-2 px-3">{{ row['Nome da Demanda'] }}</td>
            <td class="py-2 px-3">{{ row['Card'] }}</td>
            <td class="py-2 px-3 font-mono">{{ row['Tempo Gasto'] }}</td>
            <td class="py-2 px-3 text-gray-400">{{ row['Descrição'] }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="searched" class="text-center text-gray-400 py-8">
      Nenhuma demanda finalizada no período.
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDemandsStore } from '../stores/demands'

const store = useDemandsStore()

// Default: last 7 days
const today = new Date().toISOString().split('T')[0]
const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

const startDate = ref(weekAgo)
const endDate = ref(today)
const reportData = ref([])
const loading = ref(false)
const searched = ref(false)

async function generateReport() {
  loading.value = true
  searched.value = true
  try {
    reportData.value = await store.getReport(startDate.value, endDate.value)
  } catch (e) {
    alert('Erro ao gerar relatório: ' + e.message)
  } finally {
    loading.value = false
  }
}

function exportCSV() {
  if (!reportData.value.length) return

  const headers = ['Nome da Demanda', 'Card', 'Tempo Gasto', 'Descrição']
  const rows = reportData.value.map(row =>
    headers.map(h => `"${(row[h] || '').replace(/"/g, '""')}"`)
  )

  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `relatorio_${startDate.value}_${endDate.value}.csv`
  link.click()

  URL.revokeObjectURL(url)
}
</script>
