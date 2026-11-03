<template>
  <div class="page dashboard">
    <div class="page-head">
      <div>
        <h1 class="page-title">运营看板</h1>
        <p class="page-desc">实时掌握进厂过磅、核价待办与结算回款</p>
      </div>
      <div class="head-actions">
        <el-radio-group v-model="trendDays" size="small" @change="loadTrend">
          <el-radio-button :value="7">近 7 天</el-radio-button>
          <el-radio-button :value="14">近 14 天</el-radio-button>
          <el-radio-button :value="30">近 30 天</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 指标卡 -->
    <div class="grid grid-4 stats">
      <div class="stat" v-for="s in statCards" :key="s.key">
        <div class="stat__glow" :style="{ background: s.color }"></div>
        <div class="stat__top">
          <span class="stat__label">{{ s.label }}</span>
          <div class="stat__icon" :style="{ color: s.color, boxShadow: `0 0 22px ${s.color}44` }">
            <el-icon><component :is="s.icon" /></el-icon>
          </div>
        </div>
        <div class="stat__value">
          <span class="num-glow">{{ s.value }}</span>
          <em>{{ s.unit }}</em>
        </div>
        <div class="stat__foot">{{ s.foot }}</div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="grid chart-row">
      <div class="tech-card chart-card">
        <div class="tech-card__head">
          <div class="tech-card__title">过磅趋势</div>
          <span class="tech-card__sub">结算净重（吨） / 结算金额（元）</span>
        </div>
        <div ref="trendRef" class="chart"></div>
      </div>

      <div class="tech-card chart-card">
        <div class="tech-card__head">
          <div class="tech-card__title">物料结构</div>
          <span class="tech-card__sub">近 30 天</span>
        </div>
        <div ref="pieRef" class="chart"></div>
      </div>
    </div>

    <!-- 最近行程 -->
    <div class="tech-card recent">
      <div class="tech-card__head">
        <div class="tech-card__title">最近磅单</div>
        <el-button text type="primary" @click="$router.push('/trips')">
          查看全部 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      <el-table :data="recent" height="264" size="default">
        <el-table-column prop="trip_no" label="行程号" min-width="170">
          <template #default="{ row }"><span class="mono text-brand">{{ row.trip_no }}</span></template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" min-width="130" />
        <el-table-column prop="plate_no" label="车牌" width="110" />
        <el-table-column prop="item_count" label="批次" width="70" align="center" />
        <el-table-column label="结算净重" width="120" align="right">
          <template #default="{ row }"><span class="num-glow">{{ row.total_weight.toFixed(2) }}</span> 吨</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="tripTagType(row.status)" effect="dark" size="small">{{ tripStatus(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ fmt(row.create_time) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { dashboardApi } from '../api'
import { tripStatus, tripTagType } from '../utils/status'

const overview = ref({})
const recent = ref([])
const trendDays = ref(7)

const trendRef = ref()
const pieRef = ref()
let trendChart = null
let pieChart = null
let alive = true

const statCards = computed(() => [
  {
    key: 'trips',
    label: '今日过磅车次',
    value: overview.value.today_trips ?? 0,
    unit: '车',
    icon: 'Van',
    color: '#2f7bff',
    foot: '含收货与发货行程'
  },
  {
    key: 'weight',
    label: '今日结算净重',
    value: (overview.value.today_weight ?? 0).toFixed(2),
    unit: '吨',
    icon: 'Odometer',
    color: '#1fd1f9',
    foot: '已完成称重与结算批次'
  },
  {
    key: 'pending',
    label: '待核价批次',
    value: overview.value.pending_price ?? 0,
    unit: '单',
    icon: 'PriceTag',
    color: '#ffb84d',
    foot: '新建 / 已核价待完成'
  },
  {
    key: 'unpaid',
    label: '未结金额',
    value: unpaid.value.value,
    unit: unpaid.value.unit,
    icon: 'Wallet',
    color: '#22e0a1',
    foot: '结算单未结清合计'
  }
])

function fmt(v) {
  return v ? dayjs(v).format('MM-DD HH:mm') : '-'
}
const unpaid = computed(() => moneyParts(overview.value.unpaid_amount))

function moneyParts(v) {
  const n = Number(v || 0)
  if (n >= 10000) return { value: (n / 10000).toFixed(2), unit: '万元' }
  return { value: n.toFixed(2), unit: '元' }
}

function initTrend(data) {
  if (!alive || !trendRef.value) return
  if (!trendChart) trendChart = echarts.init(trendRef.value)
  trendChart.setOption({
    grid: { left: 42, right: 46, top: 30, bottom: 28 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(8,24,46,.94)',
      borderColor: 'rgba(64,153,255,.35)',
      textStyle: { color: '#dbeafe', fontSize: 12 }
    },
    legend: {
      right: 0,
      top: 0,
      textStyle: { color: '#7f9ec2', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 6
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.date),
      axisLine: { lineStyle: { color: 'rgba(90,150,220,.25)' } },
      axisTick: { show: false },
      axisLabel: { color: '#6f8bb0', fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        name: '吨',
        nameTextStyle: { color: '#5a7799', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(90,150,220,.1)' } },
        axisLabel: { color: '#6f8bb0', fontSize: 11 }
      },
      {
        type: 'value',
        name: '元',
        nameTextStyle: { color: '#5a7799', fontSize: 10 },
        splitLine: { show: false },
        axisLabel: { color: '#6f8bb0', fontSize: 11 }
      }
    ],
    series: [
      {
        name: '结算净重',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: data.map((d) => d.weight),
        lineStyle: { width: 2.5, color: '#3ea0ff', shadowColor: 'rgba(62,160,255,.6)', shadowBlur: 14 },
        itemStyle: { color: '#7fd3ff', borderColor: '#0b2444', borderWidth: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(62,160,255,.35)' },
            { offset: 1, color: 'rgba(62,160,255,0)' }
          ])
        }
      },
      {
        name: '结算金额',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: 10,
        data: data.map((d) => d.amount),
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(34,224,161,.85)' },
            { offset: 1, color: 'rgba(34,224,161,.12)' }
          ])
        }
      }
    ]
  })
}

function initPie(data) {
  if (!alive || !pieRef.value) return
  if (!pieChart) pieChart = echarts.init(pieRef.value)
  const palette = ['#2f7bff', '#1fd1f9', '#7c5cff', '#22e0a1', '#ffb84d', '#ff5c7a', '#4fd8ff', '#9d8bff']
  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(8,24,46,.94)',
      borderColor: 'rgba(64,153,255,.35)',
      textStyle: { color: '#dbeafe', fontSize: 12 },
      formatter: '{b}<br/>{c} 吨 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'center',
      textStyle: { color: '#8fb0d4', fontSize: 11 },
      itemWidth: 9,
      itemHeight: 9
    },
    series: [
      {
        type: 'pie',
        radius: ['52%', '74%'],
        center: ['38%', '52%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: 'rgba(6,20,40,.9)', borderWidth: 2 },
        label: { show: false },
        emphasis: {
          label: { show: true, color: '#eaf4ff', fontSize: 13, fontWeight: 600, formatter: '{b}\n{d}%' },
          scaleSize: 6
        },
        data: data.length ? data : [{ name: '暂无数据', value: 1 }],
        color: palette
      }
    ]
  })
}

async function loadTrend() {
  const data = await dashboardApi.trend(trendDays.value)
  initTrend(data)
}

async function loadAll() {
  const [ov, trend, dist, trips] = await Promise.all([
    dashboardApi.overview(),
    dashboardApi.trend(trendDays.value),
    dashboardApi.materialDistribution(30),
    dashboardApi.recentTrips()
  ])
  overview.value = ov
  recent.value = trips
  await nextTick()
  if (!alive) return
  initTrend(trend)
  initPie(dist)
}

function resize() {
  trendChart?.resize()
  pieChart?.resize()
}

onMounted(() => {
  loadAll()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  alive = false
  window.removeEventListener('resize', resize)
  trendChart?.dispose()
  pieChart?.dispose()
  trendChart = null
  pieChart = null
})
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 16px; }
.head-actions :deep(.el-radio-button__inner) {
  background: rgba(10, 30, 58, 0.6);
  border-color: rgba(70, 150, 255, 0.2);
  color: #8fb0d4;
}
.head-actions :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(96deg, #2f7bff, #1fa8f9);
  border-color: transparent;
  box-shadow: 0 4px 16px rgba(47, 123, 255, 0.35);
}

.stats { margin-bottom: 2px; }

.stat {
  position: relative;
  overflow: hidden;
  padding: 18px 18px 16px;
  border-radius: var(--radius);
  background: linear-gradient(150deg, rgba(14, 38, 72, 0.85), rgba(6, 18, 36, 0.75));
  border: 1px solid var(--line);
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(12px);
  transition: transform 0.22s ease, border-color 0.22s ease;
}
.stat:hover { transform: translateY(-3px); border-color: rgba(79, 155, 255, 0.4); }
.stat__glow {
  position: absolute;
  width: 150px; height: 150px;
  right: -60px; top: -60px;
  border-radius: 50%;
  filter: blur(48px);
  opacity: 0.28;
}
.stat__top { display: flex; align-items: center; justify-content: space-between; }
.stat__label { font-size: 12px; letter-spacing: 1px; color: #8fb0d4; }
.stat__icon {
  width: 36px; height: 36px;
  display: grid; place-items: center;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 18px;
}
.stat__value { display: flex; align-items: baseline; gap: 6px; margin: 14px 0 8px; }
.stat__value span { font-size: 30px; font-weight: 700; letter-spacing: 0.5px; color: #f2f8ff; }
.stat__value em { font-style: normal; font-size: 12px; color: #6f8bb0; }
.stat__foot { font-size: 11.5px; color: #5c7899; }

.chart-row { grid-template-columns: 1.65fr 1fr; }
.chart-card { padding-bottom: 8px; }
.chart { height: 300px; width: 100%; }

.recent { padding-bottom: 12px; }

@media (max-width: 1180px) {
  .chart-row { grid-template-columns: 1fr; }
}
</style>
