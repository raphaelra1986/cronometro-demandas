<template>
  <div class="card mb-4">
    <!-- Header -->
    <div class="flex justify-between items-start mb-3">
      <div>
        <h3 class="text-lg font-semibold text-white">{{ demand.name }}</h3>
        <div class="flex gap-3 text-sm text-gray-400 mt-1">
          <span>Card: {{ demand.card }}</span>
          <span class="px-2 py-0.5 rounded text-xs" :class="categoryClass">
            {{ demand.category }}
          </span>
        </div>
      </div>
      <div class="text-right">
        <div class="text-2xl font-mono font-bold" :class="timerClass">
          {{ formatTime(demand.current_elapsed_time) }}
        </div>
        <span class="text-xs px-2 py-1 rounded" :class="statusClass">
          {{ statusLabel }}
        </span>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex gap-2 mb-3">
      <button
        @click="$emit('start', demand.id)"
        :disabled="demand.status !== 'pausada'"
        class="btn btn-success text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': demand.status !== 'pausada' }"
      >
        ▶ Play
      </button>
      <button
        @click="$emit('pause', demand.id)"
        :disabled="demand.status !== 'em_andamento'"
        class="btn btn-warning text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': demand.status !== 'em_andamento' }"
      >
        ⏸ Pause
      </button>
      <button
        @click="handleStop"
        :disabled="demand.status === 'finalizada'"
        class="btn btn-danger text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': demand.status === 'finalizada' }"
      >
        ⏹ Stop
      </button>
      <button
        @click="showTimeEdit = true"
        :disabled="demand.status === 'em_andamento'"
        class="btn btn-secondary text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': demand.status === 'em_andamento' }"
      >
        ⏱ Editar
      </button>
      <button
        @click="$emit('delete', demand.id)"
        :disabled="demand.status === 'em_andamento'"
        class="btn btn-danger text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': demand.status === 'em_andamento' }"
      >
        🗑
      </button>
    </div>

    <!-- Description -->
    <div class="flex gap-2">
      <input
        v-model="description"
        type="text"
        placeholder="Descrição..."
        class="input flex-1"
        :disabled="demand.status === 'em_andamento'"
      />
      <button
        @click="saveDescription"
        :disabled="demand.status !== 'finalizada'"
        class="btn btn-primary text-sm"
        :class="{ 'opacity-50 cursor-not-allowed': demand.status !== 'finalizada' }"
      >
        Salvar
      </button>
    </div>

    <!-- Time Edit Modal -->
    <div v-if="showTimeEdit" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-gray-800 rounded-xl p-6 w-80">
        <h3 class="text-lg font-semibold mb-4">Editar Tempo</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Horas</label>
            <input v-model.number="editHours" type="number" min="0" class="input" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Minutos</label>
            <input v-model.number="editMinutes" type="number" min="0" max="59" class="input" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Segundos</label>
            <input v-model.number="editSeconds" type="number" min="0" max="59" class="input" />
          </div>
        </div>
        <div class="flex gap-2 mt-4">
          <button @click="saveTime" class="btn btn-primary flex-1">Salvar</button>
          <button @click="showTimeEdit = false" class="btn btn-secondary flex-1">Cancelar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useDemandsStore } from '../stores/demands'

const props = defineProps({
  demand: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['start', 'pause', 'stop', 'delete', 'update-time', 'update-description'])

const store = useDemandsStore()

const description = ref(props.demand.description || '')
const showTimeEdit = ref(false)
const editHours = ref(0)
const editMinutes = ref(0)
const editSeconds = ref(0)

watch(() => props.demand.description, (newVal) => {
  description.value = newVal || ''
})

const statusClass = computed(() => {
  switch (props.demand.status) {
    case 'em_andamento': return 'bg-green-600 text-white'
    case 'pausada': return 'bg-yellow-600 text-white'
    case 'finalizada': return 'bg-gray-600 text-white'
    default: return 'bg-gray-600 text-white'
  }
})

const statusLabel = computed(() => {
  switch (props.demand.status) {
    case 'em_andamento': return 'Em Andamento'
    case 'pausada': return 'Pausada'
    case 'finalizada': return 'Finalizada'
    default: return props.demand.status
  }
})

const timerClass = computed(() => {
  return props.demand.status === 'em_andamento' ? 'text-green-400' : 'text-white'
})

const categoryClass = computed(() => {
  switch (props.demand.category) {
    case 'Sprint': return 'bg-blue-600'
    case 'Furacão': return 'bg-red-600'
    case 'Meta': return 'bg-purple-600'
    case 'Extra': return 'bg-gray-600'
    default: return 'bg-gray-600'
  }
})

function formatTime(seconds) {
  return store.formatTime(seconds)
}

function handleStop() {
  if (!description.value.trim()) {
    alert('Por favor, preencha a descrição antes de finalizar.')
    return
  }
  emit('stop', props.demand.id, description.value)
}

function saveDescription() {
  if (description.value.trim()) {
    emit('update-description', props.demand.id, description.value)
  }
}

function openTimeEdit() {
  const total = Math.floor(props.demand.accumulated_time || 0)
  editHours.value = Math.floor(total / 3600)
  editMinutes.value = Math.floor((total % 3600) / 60)
  editSeconds.value = total % 60
  showTimeEdit.value = true
}

watch(showTimeEdit, (show) => {
  if (show) {
    openTimeEdit()
  }
})

function saveTime() {
  const totalSeconds = (editHours.value * 3600) + (editMinutes.value * 60) + editSeconds.value
  emit('update-time', props.demand.id, totalSeconds)
  showTimeEdit.value = false
}
</script>
