<template>
  <div class="page reports">
    <div class="page-head">
      <div>
        <h1 class="page-title">报表中心</h1>
        <p class="page-desc">按物料维度汇总区间内的过磅净重、扣杂与结算净重</p>
      </div>
      <div class="head-actions">
        <el-date-picker
          v-model="range"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          @change="load"
        />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button plain :disabled="!rows.length" @click="exportCsv">
          <el-icon><Download /></el-icon> 导出 CSV
        </el-button>
      </div>
    </div>

    <div class="grid grid-4 summary-cards">
      <div class="sum-card">
        <span>过磅净重</span>
        <b class="num-glow text-cyan">{{ weight(summary.net_weight) }} <em>吨</em></b>
      </div>
      <div class="sum-card">
        <span>扣杂合计</span>
        <b class="num-glow text-warning">{{ weight(summary.deduct_weight) }} <em>吨</em></b>
      </div>
      <div class="sum-card">
        <span>结算净重</span>
        <b class="num-glow text-success">{{ weight(summary.settle_weight) }} <em>吨</em></b>
      </div>
      <div class="sum-card">
        <span>批次数量</span>
        <b class="num-glow text-brand">{{ summary.item_count || 0 }} <em>单</em></b>
      </div>
    </div>

    <div class="tech-card">
      <div class="tech-card__head">
        <div class="tech-card__title">物料汇总</div>
        <span class="tech-card__sub">{{ range?.[0] }} ~ {{ range?.[1] }}</span>
      </div>

      <el-table :data="rows" v-loading="loading" height="calc(100vh - 340px)" show-summary :summary-method="summaryMethod" empty-text="区间内暂无数据">
        <el-table-column prop="material_name" label="物料" min-width="160" />
        <el-table-column label="过磅净重（吨）" min-width="140" align="right">
          <template #default="{ row }"><span class="num-glow">{{ weight(row.net_weight) }}</span></template>
        </el-table-column>
        <el-table-column label="扣杂（吨）" min-width="130" align="right">
          <template #default="{ row }"><span class="text-warning">{{ weight(row.deduct_weight) }}</span></template>
        </el-table-column>
        <el-table-column label="结算净重（吨）" min-width="140" align="right">
          <template #default="{ row }"><span class="num-glow text-cyan">{{ weight(row.settle_weight) }}</span></template>
        </el-table-column>
        <el-table-column prop="item_count" label="批次数" min-width="100" align="center" />
        <el-table-column label="扣杂率" width="120" align="right">
          <template #default="{ row }">
            {{ row.net_weight ? ((row.deduct_weight / row.net_weight) * 100).toFixed(2) + '%' : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { reportApi } from '../api'
import { weight } from '../utils/status'

const rows = ref([])
const summary = ref({})
const loading = ref(false)
const range = ref([dayjs().subtract(6, 'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')])

async function load() {
  if (!range.value?.[0]) return
  loading.value = true
  try {
    const data = await reportApi.daily({ start: range.value[0], end: range.value[1] })
    rows.value = data.rows
    summary.value = data.summary
  } finally {
    loading.value = false
  }
}

function summaryMethod({ columns }) {
  return columns.map((col, index) => {
    if (index === 0) return '合计'
    if (col.label === '过磅净重（吨）') return weight(summary.value.net_weight)
    if (col.label === '扣杂（吨）') return weight(summary.value.deduct_weight)
    if (col.label === '结算净重（吨）') return weight(summary.value.settle_weight)
    if (col.label === '批次数') return summary.value.item_count
    if (col.label === '扣杂率') {
      const n = Number(summary.value.net_weight || 0)
      return n ? ((Number(summary.value.deduct_weight || 0) / n) * 100).toFixed(2) + '%' : '-'
    }
    return ''
  })
}

function exportCsv() {
  const header = ['物料', '过磅净重(吨)', '扣杂(吨)', '结算净重(吨)', '批次数']
  const lines = [header.join(',')]
  rows.value.forEach((r) => {
    lines.push([r.material_name, r.net_weight, r.deduct_weight, r.settle_weight, r.item_count].join(','))
  })
  lines.push(['合计', summary.value.net_weight, summary.value.deduct_weight, summary.value.settle_weight, summary.value.item_count].join(','))

  const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `物料汇总_${range.value[0]}_${range.value[1]}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出 CSV')
}

onMounted(load)
</script>

<style scoped>
.head-actions { display: flex; gap: 10px; align-items: center; }

.summary-cards { margin-bottom: 16px; }
.sum-card {
  padding: 16px 18px; border-radius: var(--radius);
  background: linear-gradient(150deg, rgba(14, 38, 72, 0.85), rgba(6, 18, 36, 0.72));
  border: 1px solid var(--line);
  display: flex; flex-direction: column; gap: 8px;
}
.sum-card span { font-size: 11.5px; color: #8fb0d4; letter-spacing: 0.6px; }
.sum-card b { font-size: 24px; color: #eaf4ff; }
.sum-card b em { font-style: normal; font-size: 11px; color: #6f8bb0; }
</style>
