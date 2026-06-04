<template>
  <div class="card mb-6">
    <h2 class="text-lg font-semibold mb-4">Nova Demanda</h2>
    <form @submit.prevent="handleSubmit" class="flex flex-wrap gap-3">
      <div class="flex-1 min-w-[200px]">
        <input
          v-model="name"
          type="text"
          placeholder="Nome da demanda"
          class="input"
          required
        />
      </div>
      <div class="w-32">
        <input
          v-model="card"
          type="text"
          placeholder="Card"
          class="input"
          required
        />
      </div>
      <div class="w-40">
        <select v-model="category" class="select">
          <option v-for="cat in categories" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="loading">
        {{ loading ? 'Adicionando...' : 'Adicionar' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDemandsStore } from '../stores/demands'

const store = useDemandsStore()

const name = ref('')
const card = ref('')
const category = ref('Extra')
const loading = ref(false)

const categories = store.categories.length ? store.categories : ['Sprint', 'Furacão', 'Meta', 'Extra']

async function handleSubmit() {
  if (!name.value.trim() || !card.value.trim()) return

  loading.value = true
  try {
    await store.createDemand(name.value, card.value, category.value)
    name.value = ''
    card.value = ''
    category.value = 'Extra'
  } catch (e) {
    alert('Erro ao criar demanda: ' + e.message)
  } finally {
    loading.value = false
  }
}
</script>
