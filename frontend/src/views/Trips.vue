<template>
  <div class="page trips">
    <div class="page-head">
      <div>
        <h1 class="page-title">磅单记录</h1>
        <p class="page-desc">按行程查看每一车的货物批次、地磅读数与状态流转</p>
      </div>
      <div class="head-actions">
        <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 140px" @change="load">
          <el-option label="进行中" :value="0" />
          <el-option label="称重完成" :value="1" />
          <el-option label="已结算" :value="2" />
          <el-option label="已作废" :value="3" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 250px"
          @change="load"
        />
        <el-input v-model="query.keyword" placeholder="行程号 / 车牌 / 客户" clearable style="width: 210px" :prefix-icon="Search" @keyup.enter="load" @clear="load" />
        <el-button type="primary" @click="load">查询</el-button>
      </div>
    </div>

    <div class="tech-card">
      <div class="tech-card__head">
        <div class="tech-card__title">行程列表</div>
        <span class="tech-card__sub">共 {{ list.length }} 条</span>
      </div>

      <el-table :data="list" v-loading="loading" height="calc(100vh - 236px)" empty-text="暂无数据">
        <el-table-column prop="trip_no" label="行程号" min-width="170">
          <template #default="{ row }"><span class="mono text-brand">{{ row.trip_no }}</span></template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" min-width="130" />
        <el-table-column prop="customer_phone" label="手机号" width="110">
          <template #default="{ row }">{{ row.customer_phone || '-' }}</template>
        </el-table-column>
        <el-table-column prop="plate_no" label="车牌" width="96">
          <template #default="{ row }">{{ row.plate_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="业务" width="72" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="row.biz_type === 1 ? 'warning' : 'success'">
              {{ row.biz_type === 1 ? '收货' : '发货' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="item_count" label="批次" width="60" align="center" />
        <el-table-column label="结算净重" width="104" align="right">
          <template #default="{ row }"><span class="num-glow">{{ weight(row.total_weight) }}</span> 吨</template>
        </el-table-column>
        <el-table-column label="扣杂" width="84" align="right">
          <template #default="{ row }"><span class="text-warning">{{ weight(row.total_deduct) }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="96" align="center">
          <template #default="{ row }">
            <el-tag :type="tripTagType(row.status)" effect="dark" size="small">{{ tripStatus(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="134">
          <template #default="{ row }">{{ fmt(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="78" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" plain @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer v-model="drawer" size="760px" title="行程详情">
      <div v-if="detail" class="trip-detail">
        <div class="head">
          <div>
            <span class="muted">行程号</span>
            <h3 class="mono">{{ detail.trip.trip_no }}</h3>
          </div>
          <el-tag :type="tripTagType(detail.trip.status)" effect="dark">{{ tripStatus(detail.trip.status) }}</el-tag>
        </div>

        <div class="meta">
          <div><span>客户</span><b>{{ detail.trip.customer_name }}</b></div>
          <div><span>手机号</span><b>{{ detail.trip.customer_phone || '-' }}</b></div>
          <div><span>车牌</span><b>{{ detail.trip.plate_no || '-' }}</b></div>
          <div><span>司机</span><b>{{ detail.trip.driver_name || '-' }}</b></div>
          <div><span>业务类型</span><b>{{ detail.trip.biz_type === 1 ? '收货' : '发货' }}</b></div>
          <div><span>创建时间</span><b>{{ fmt(detail.trip.create_time) }}</b></div>
        </div>

        <div class="section-title">货物批次</div>
        <el-table :data="detail.items" size="small">
          <el-table-column prop="seq" label="#" width="46" align="center" />
          <el-table-column prop="ticket_no" label="磅单号" min-width="170">
            <template #default="{ row }"><span class="mono">{{ row.ticket_no }}</span></template>
          </el-table-column>
          <el-table-column prop="material_name" label="物料" width="100" />
          <el-table-column label="毛重" width="78" align="right">
            <template #default="{ row }">{{ weight(row.start_weight) }}</template>
          </el-table-column>
          <el-table-column label="皮重" width="78" align="right">
            <template #default="{ row }">{{ weight(row.end_weight) }}</template>
          </el-table-column>
          <el-table-column label="净重" width="78" align="right">
            <template #default="{ row }">{{ weight(row.net_weight) }}</template>
          </el-table-column>
          <el-table-column label="扣杂" width="72" align="right">
            <template #default="{ row }">{{ weight(row.deduct_weight) }}</template>
          </el-table-column>
          <el-table-column label="结算净重" width="90" align="right">
            <template #default="{ row }"><span class="text-cyan">{{ weight(row.settle_weight) }}</span></template>
          </el-table-column>
          <el-table-column label="单价" width="88" align="right">
            <template #default="{ row }">{{ row.unit_price ? '¥' + Number(row.unit_price).toFixed(2) : '-' }}</template>
          </el-table-column>
          <el-table-column label="状态" width="96" align="center">
            <template #default="{ row }">
              <el-tag :type="itemTagType(row.status)" effect="dark" size="small">{{ itemStatus(row.status) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div class="section-title">地磅读数</div>
        <div class="readings">
          <div class="reading" v-for="r in detail.readings" :key="r.reading_id">
            <span class="seq mono">#{{ r.seq }}</span>
            <b class="num-glow">{{ Number(r.weight).toFixed(2) }} <em>吨</em></b>
            <span class="time">{{ fmt(r.reading_time) }}</span>
            <span class="op">{{ r.operator_name }}</span>
          </div>
          <div v-if="!detail.readings.length" class="muted">暂无读数</div>
        </div>

        <div class="summary">
          <div><span>结算净重</span><b class="text-cyan">{{ weight(detail.summary.total_settle_weight) }} 吨</b></div>
          <div><span>预估金额</span><b class="text-success">¥ {{ money(detail.summary.total_amount) }}</b></div>
          <div><span>待核价</span><b class="text-warning">{{ detail.summary.pending_price }}</b></div>
          <div><span>已结算</span><b>{{ detail.summary.settled }}</b></div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { weighApi } from '../api'
import { itemStatus, itemTagType, money, tripStatus, tripTagType, weight } from '../utils/status'

const list = ref([])
const loading = ref(false)
const drawer = ref(false)
const detail = ref(null)

const query = reactive({ status: null, keyword: '' })
const dateRange = ref([])

function fmt(v) {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'
}

async function load() {
  loading.value = true
  try {
    list.value = await weighApi.listTrips({
      status: query.status ?? undefined,
      keyword: query.keyword || undefined,
      start: dateRange.value?.[0] || undefined,
      end: dateRange.value?.[1] || undefined
    })
  } finally {
    loading.value = false
  }
}

async function openDetail(row) {
  detail.value = await weighApi.tripDetail(row.trip_id)
  drawer.value = true
}

onMounted(load)
</script>

<style scoped>
.head-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.trip-detail { display: flex; flex-direction: column; gap: 14px; }
.head { display: flex; align-items: flex-start; justify-content: space-between; }
.head h3 { margin: 4px 0 0; font-size: 20px; color: #6fd6ff; }
.head span { font-size: 11px; }

.meta {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
  padding: 14px; border-radius: 12px;
  background: rgba(31, 129, 255, 0.06);
  border: 1px solid rgba(70, 150, 255, 0.14);
}
.meta div { display: flex; flex-direction: column; gap: 3px; }
.meta span { font-size: 10.5px; color: #6f8bb0; }
.meta b { font-size: 12.5px; }

.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: #cfe2fa; margin-top: 4px;
}
.section-title::before {
  content: ''; width: 3px; height: 12px; border-radius: 2px;
  background: linear-gradient(180deg, #4fd8ff, #2f7bff);
}

.readings { display: grid; gap: 8px; }
.reading {
  display: grid; grid-template-columns: 48px 130px 1fr 90px;
  align-items: center; padding: 9px 12px; border-radius: 9px;
  background: rgba(10, 30, 58, 0.6);
  border: 1px solid rgba(70, 150, 255, 0.1);
  font-size: 12px;
}
.reading .seq { color: #4f9bff; }
.reading b { font-size: 14px; }
.reading b em { font-style: normal; font-size: 10px; color: #6f8bb0; }
.reading .time { color: #7f9ec2; }
.reading .op { color: #6f8bb0; text-align: right; }

.summary {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  padding: 14px; border-radius: 12px;
  background: linear-gradient(120deg, rgba(31, 129, 255, 0.1), rgba(31, 209, 249, 0.04));
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.summary div { display: flex; flex-direction: column; gap: 4px; }
.summary span { font-size: 10.5px; color: #6f8bb0; }
.summary b { font-size: 14px; }
</style>
