<template>
    <div class="trending-table">
      <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th rowspan="2">年份</th>
                    <th v-for="month in months" :key="month">{{ month }}</th>
                </tr>
            </thead>
            <tbody>
                <template v-for="year in years" :key="year">
                    <tr>
                        <td>{{ year }}</td>
                        <template v-for="(value, monthIndex) in getYearData(year)" :key="year + '-month-' + monthIndex">
                            <td>{{ valueDisplay(value) }}</td>
                        </template>
                    </tr>
                </template>
            </tbody>
        </table>
      </div>
    </div>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

// reactive container for yearData
const yearData = reactive({})

// months
const months = computed(() => ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

// years computed from props.data
const years = computed(() => {
  const startYear = new Date(props.data.時間起點).getFullYear()
  const endYear = new Date(props.data.時間終點).getFullYear()
  const ys = []
  for (let year = startYear; year <= endYear; year++) {
    ys.push(year)
  }
  return ys
})

// processInitData
function processInitData() {
  const startMonth = new Date(props.data.時間起點).getMonth() + 1
  const endMonth = new Date(props.data.時間終點).getMonth() + 1
  const startYear = new Date(props.data.時間起點).getFullYear()
  const endYear = new Date(props.data.時間終點).getFullYear()

  // clear existing keys
  Object.keys(yearData).forEach(k => delete yearData[k])

  const stats = String(props.data.統計值).split(',')

  for (let year = startYear; year <= endYear; year++) {
    const yearPrices = []
    for (let month = 1; month <= 12; month++) {
      if (year === startYear && month < startMonth) {
        yearPrices.push('0')
      } else if (year === endYear && month > endMonth) {
        yearPrices.push('0')
      } else {
        const idx = month + (year - startYear) * 12 - startMonth
        yearPrices.push(stats[idx])
      }
    }
    yearData[year] = yearPrices
  }
}

// helpers
function getYearData(year) {
  return yearData[year] || Array(12).fill('0')
}

function valueDisplay(value) {
  return value === '0' ? '-' : value
}

// watch data
watch(
  () => props.data,
  (newVal) => {
    if (newVal) {
      processInitData()
    }
  },
  { deep: true, immediate: true }
)
</script>

<style scoped>
.trending-table {
    margin-top: 2em;
}

table {
    width: 100%;
    border-collapse: collapse;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.table-wrap table {
  min-width: 1200px;
  width: 100%;
  border-collapse: collapse;
}

th,
td {
    border: 1px solid #ccc;
    padding: 0.5em;
    text-align: center;
}
</style>
