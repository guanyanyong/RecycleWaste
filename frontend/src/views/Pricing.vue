<template>
  <div class="page pricing">
    <div class="page-head">
      <div>
        <h1 class="page-title">质检核价</h1>
        <p class="page-desc">对新建批次定质定价，核价后即可进入称重完成环节</p>
      </div>
      <div class="head-actions">
        <el-input
          v-model="keyword"
          placeholder="搜索磅单 / 物料 / 客户 / 车牌"
          clearable
          style="width: 260px"
          :prefix-icon="Search"
          @keyup.enter="load"
          @clear="load"
        />
        <el-button type="primary" @click="load">查询</el-button>
      </div>
    </div>

    <div class="queue-stats">
      <div class="q-item" :class="{ active: status === 0 }" @click="switchStatus(0)">
        <span>待核价</span>
        <b class="text-warning">{{ status === 0 ? list.length : '—' }}</b>
      </div>
      <div class="q-item" :class="{ active: status === 1 }" @click="switchStatus(1)">
        <span>已核价待称重</span>
        <b class="text-brand">{{ status === 1 ? list.length : '—' }}</b>
      </div>
      <div class="q-hint">
        <el-icon><InfoFilled /></el-icon>
        核价会记录扣重规则快照，后续规则调整不影响历史磅单
      </div>
    </div>

    <div class="tech-card">
      <div class="tech-card__head">
        <div class="tech-card__title">{{ status === 0 ? '待核价队列' : '已核价待称重' }}</div>
        <el-button text type="primary" @click="load">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table :data="list" v-loading="loading" height="calc(100vh - 330px)" empty-text="暂无待处理批次">
        <el-table-column prop="ticket_no" label="磅单号" min-width="180">
          <template #default="{ row }"><span class="mono text-brand">{{ row.ticket_no }}</span></template>
        </el-table-column>
        <el-table-column prop="material_name" label="物料" min-width="110" />
        <el-table-column prop="customer_name" label="客户" min-width="110" />
        <el-table-column prop="plate_no" label="车牌" width="94">
          <template #default="{ row }">{{ row.plate_no || '-' }}</template>
        </el-table-column>
        <el-table-column label="称重模式" width="84" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="row.weigh_mode === 2 ? 'success' : 'info'">
              {{ row.weigh_mode === 2 ? '单次' : '两次' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="毛重" width="84" align="right">
          <template #default="{ row }"><span class="num-glow">{{ weight(row.start_weight) }}</span></template>
        </el-table-column>
        <el-table-column label="净重" width="84" align="right">
          <template #default="{ row }"><span class="num-glow">{{ weight(row.net_weight) }}</span></template>
        </el-table-column>
        <el-table-column label="单价" width="100" align="right">
          <template #default="{ row }">
            <span v-if="row.unit_price" class="text-success">¥{{ Number(row.unit_price).toFixed(2) }}</span>
            <span v-else class="muted">未定价</span>
          </template>
        </el-table-column>
        <el-table-column label="建单时间" width="124">
          <template #default="{ row }">{{ fmt(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="116" fixed="right" align="center">
          <template #default="{ row }">
            <el-button v-if="row.status === 0" size="small" type="warning" @click="openPrice(row)">立即核价</el-button>
            <el-button v-else size="small" type="primary" @click="openTare(row)">完成称重</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <PriceDialog v-model="priceVisible" :item="current" @success="load" />

    <el-dialog v-model="tareVisible" title="完成称重" width="420px">
      <div class="tare" v-if="current">
        <div class="tare__row"><span>磅单</span><b class="mono text-brand">{{ current.ticket_no }}</b></div>
        <div class="tare__row"><span>毛重</span><b class="num-glow">{{ weight(current.start_weight) }} 吨</b></div>
        <div class="tare__row" v-if="current.weigh_mode === 1">
          <span>皮重</span>
          <el-input-number v-model="tareWeight" :min="0.01" :max="200" :precision="2" :step="0.1" controls-position="right" style="width: 150px" />
          <em>吨</em>
        </div>
        <p class="tare__net">
          净重：<b class="text-cyan">{{ weight(netPreview) }} 吨</b>
          <span class="muted" style="margin-left: 12px">
            预计扣重 {{ weight(current.deduct_preview ?? current.deduct_weight) }} 吨
          </span>
        </p>
      </div>
      <template #footer>
        <el-button @click="tareVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitTare">确认完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { weighApi } from '../api'
import { weight } from '../utils/status'
import PriceDialog from '../components/PriceDialog.vue'

const list = ref([])
const keyword = ref('')
const status = ref(0)
const loading = ref(false)

const priceVisible = ref(false)
const tareVisible = ref(false)
const current = ref(null)
const tareWeight = ref(0)
const saving = ref(false)

const netPreview = computed(() => {
  if (!current.value) return 0
  if (current.value.weigh_mode === 2) return Number(current.value.start_weight || 0)
  return Math.max(0, Number(current.value.start_weight || 0) - Number(tareWeight.value || 0))
})

function fmt(v) {
  return v ? dayjs(v).format('MM-DD HH:mm') : '-'
}

async function load() {
  loading.value = true
  try {
    list.value = await weighApi.pendingItems({ status: status.value, keyword: keyword.value || undefined })
  } finally {
    loading.value = false
  }
}

function switchStatus(v) {
  status.value = v
  load()
}

function openPrice(row) {
  current.value = row
  priceVisible.value = true
}

function openTare(row) {
  current.value = row
  tareWeight.value = 0
  tareVisible.value = true
}

async function submitTare() {
  if (!current.value) return
  if (current.value.weigh_mode === 1 && (!tareWeight.value || tareWeight.value <= 0)) {
    return ElMessage.warning('请输入皮重')
  }
  saving.value = true
  try {
    await weighApi.complete(current.value.item_id, {
      end_weight: current.value.weigh_mode === 1 ? tareWeight.value : null
    })
    ElMessage.success('称重完成')
    tareVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.head-actions { display: flex; gap: 10px; align-items: center; }

.queue-stats {
  display: flex; align-items: stretch; gap: 14px; margin-bottom: 16px;
}
.q-item {
  display: flex; flex-direction: column; gap: 4px;
  min-width: 160px; padding: 12px 18px;
  border-radius: 12px; cursor: pointer;
  border: 1px solid rgba(70, 150, 255, 0.16);
  background: rgba(10, 30, 58, 0.55);
  transition: all 0.2s ease;
}
.q-item span { font-size: 11.5px; color: #8fb0d4; }
.q-item b { font-size: 22px; font-family: 'JetBrains Mono', Consolas, monospace; }
.q-item.active {
  border-color: rgba(79, 216, 255, 0.5);
  box-shadow: 0 0 24px rgba(31, 209, 249, 0.15);
  background: linear-gradient(120deg, rgba(31, 129, 255, 0.18), rgba(31, 209, 249, 0.06));
}
.q-hint {
  flex: 1; display: flex; align-items: center; gap: 8px;
  font-size: 11.5px; color: #6f8bb0;
  padding: 0 16px; border-radius: 12px;
  border: 1px dashed rgba(70, 150, 255, 0.2);
}
.q-hint :deep(.el-icon) { color: #4f9bff; }

.tare { display: grid; gap: 10px; }
.tare__row { display: flex; align-items: center; gap: 10px; font-size: 12.5px; }
.tare__row span { width: 54px; color: #7f9ec2; }
.tare__row em { font-style: normal; color: #6f8bb0; font-size: 11px; }
.tare__net { margin: 6px 0 0; font-size: 13px; }
</style>
