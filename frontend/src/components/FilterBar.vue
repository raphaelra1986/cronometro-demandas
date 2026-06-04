<template>
  <div class="card mb-4">
    <div class="flex flex-wrap gap-3 items-center">
      <div class="flex-1 min-w-[200px]">
        <input
          v-model="store.searchQuery"
          type="text"
          placeholder="Buscar por nome ou card..."
          class="input"
        />
      </div>

      <div class="w-40">
        <select v-model="store.statusFilter" class="select">
          <option value="Todos">Todos os Status</option>
          <option value="pausada">Pausada</option>
          <option value="em_andamento">Em Andamento</option>
          <option value="finalizada">Finalizada</option>
        </select>
      </div>

      <div class="w-40">
        <select v-model="store.categoryFilter" class="select">
          <option value="Todas">Todas Categorias</option>
          <option v-for="cat in categories" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
      </div>

      <button @click="store.clearFilters" class="btn btn-secondary">
        Limpar Filtros
      </button>

      <button @click="$emit('clear-finalized')" class="btn btn-danger">
        Limpar Finalizadas
      </button>
    </div>
  </div>
</template>

<script setup>
import { useDemandsStore } from '../stores/demands'

const store = useDemandsStore()
const categories = store.categories.length ? store.categories : ['Sprint', 'Furacão', 'Meta', 'Extra']

defineEmits(['clear-finalized'])
</script>
