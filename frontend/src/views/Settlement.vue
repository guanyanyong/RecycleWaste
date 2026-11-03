<template>
  <div class="page settlement">
    <div class="page-head">
      <div>
        <h1 class="page-title">结算管理</h1>
        <p class="page-desc">勾选称重完成批次生成结算单，登记收付款并跟踪结清状态</p>
      </div>
      <div class="head-actions">
        <el-input v-model="keyword" placeholder="结算单号 / 客户 / 手机号" clearable style="width: 240px" :prefix-icon="Search" @keyup.enter="loadRecords" @clear="loadRecords" />
        <el-button @click="loadRecords">查询</el-button>
      </div>
    </div>

    <el-tabs v-model="tab" class="settle-tabs" @tab-change="onTab">
      <!-- 待结算 -->
      <el-tab-pane label="待结算批次" name="pending">
        <div class="tech-card">
          <div class="tech-card__head">
            <div class="tech-card__title">称重完成 · 待结算</div>
            <div class="head-tools">
              <span class="muted">已选 {{ selection.length }} 条</span>
              <el-button size="small" @click="loadPending">刷新</el-button>
              <el-button type="primary" size="small" :disabled="!selection.length" @click="openCreate">
                生成结算单
              </el-button>
            </div>
          </div>

          <el-table :data="pending" v-loading="loadingPending" height="calc(100vh - 300px)" @selection-change="onSelect" empty-text="暂无待结算批次">
            <el-table-column type="selection" width="46" />
            <el-table-column prop="ticket_no" label="磅单号" min-width="185">
              <template #default="{ row }"><span class="mono text-brand">{{ row.ticket_no }}</span></template>
            </el-table-column>
            <el-table-column prop="customer_name" label="客户" min-width="120" />
            <el-table-column prop="material_name" label="物料" min-width="110" />
            <el-table-column label="净重" width="96" align="right">
              <template #default="{ row }">{{ weight(row.net_weight) }}</template>
            </el-table-column>
            <el-table-column label="扣杂" width="88" align="right">
              <template #default="{ row }"><span class="text-warning">{{ weight(row.deduct_weight) }}</span></template>
            </el-table-column>
            <el-table-column label="结算净重" width="104" align="right">
              <template #default="{ row }"><span class="num-glow text-cyan">{{ weight(row.settle_weight) }}</span></template>
            </el-table-column>
            <el-table-column label="单价" width="104" align="right">
              <template #default="{ row }">¥{{ Number(row.unit_price).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="金额" width="120" align="right">
              <template #default="{ row }"><span class="num-glow text-success">¥{{ money(row.amount) }}</span></template>
            </el-table-column>
            <el-table-column label="业务" width="86" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain" :type="row.biz_type === 1 ? 'warning' : 'success'">
                  {{ row.biz_type === 1 ? '收货' : '发货' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- 结算单 -->
      <el-tab-pane label="结算单" name="records">
        <div class="tech-card">
          <div class="tech-card__head">
            <div class="tech-card__title">结算单列表</div>
            <span class="tech-card__sub">共 {{ records.length }} 单</span>
          </div>

          <el-table :data="records" v-loading="loadingRecords" height="calc(100vh - 300px)" empty-text="暂无结算单">
            <el-table-column prop="settle_no" label="结算单号" min-width="180">
              <template #default="{ row }"><span class="mono text-brand">{{ row.settle_no }}</span></template>
            </el-table-column>
            <el-table-column prop="customer_name" label="客户" min-width="120" />
            <el-table-column label="批次" width="72" align="center">
              <template #default="{ row }">{{ row.item_count }}</template>
            </el-table-column>
            <el-table-column label="结算净重" width="110" align="right">
              <template #default="{ row }"><span class="num-glow">{{ weight(row.total_settle_weight) }}</span> 吨</template>
            </el-table-column>
            <el-table-column label="金额" width="130" align="right">
              <template #default="{ row }"><span class="num-glow text-success">¥{{ money(row.total_amount) }}</span></template>
            </el-table-column>
            <el-table-column label="已结" width="120" align="right">
              <template #default="{ row }">¥{{ money(row.paid_amount) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="104" align="center">
              <template #default="{ row }">
                <el-tag :type="payTagType(row.pay_status)" effect="dark" size="small">{{ payStatus(row.pay_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="settle_date" label="结算日期" width="112" />
            <el-table-column label="操作" width="196" fixed="right" align="center">
              <template #default="{ row }">
                <el-button size="small" plain @click="openDetail(row)">明细</el-button>
                <el-button size="small" type="primary" :disabled="row.pay_status === 2" @click="openPay(row)">收付款</el-button>
                <el-button size="small" type="danger" text :disabled="row.paid_amount > 0" @click="cancelRecord(row)">作废</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 生成结算单 -->
    <el-dialog v-model="createVisible" title="生成结算单" width="520px">
      <div class="create-summary">
        <div><span>批次数量</span><b>{{ selection.length }} 单</b></div>
        <div><span>结算净重</span><b class="text-cyan">{{ weight(selectedWeight) }} 吨</b></div>
        <div><span>结算金额</span><b class="text-success">¥ {{ money(selectedAmount) }}</b></div>
      </div>
      <el-alert v-if="mixedCustomer" type="warning" :closable="false" show-icon title="所选批次包含多个客户，一次结算只能选择同一客户" class="mb" />
      <el-form label-position="top">
        <el-form-item label="备注">
          <el-input v-model="remark" type="textarea" :rows="2" maxlength="200" placeholder="选填，如：现金结算 / 对公转账" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="mixedCustomer" @click="submitCreate">确认生成</el-button>
      </template>
    </el-dialog>

    <!-- 明细 -->
    <el-drawer v-model="detailVisible" size="720px" title="结算单明细">
      <div v-if="currentRecord" class="detail">
        <div class="detail-head">
          <div>
            <span class="muted">结算单号</span>
            <h3 class="mono">{{ currentRecord.settle_no }}</h3>
          </div>
          <el-tag :type="payTagType(currentRecord.pay_status)" effect="dark">{{ payStatus(currentRecord.pay_status) }}</el-tag>
        </div>
        <div class="detail-grid">
          <div><span>客户</span><b>{{ currentRecord.customer_name }}</b></div>
          <div><span>手机号</span><b>{{ currentRecord.customer_phone || '-' }}</b></div>
          <div><span>结算日期</span><b>{{ currentRecord.settle_date }}</b></div>
          <div><span>业务类型</span><b>{{ currentRecord.biz_type === 1 ? '收货付款' : '发货收款' }}</b></div>
          <div><span>结算净重</span><b class="text-cyan">{{ weight(currentRecord.total_settle_weight) }} 吨</b></div>
          <div><span>结算金额</span><b class="text-success">¥ {{ money(currentRecord.total_amount) }}</b></div>
          <div><span>已结金额</span><b>¥ {{ money(currentRecord.paid_amount) }}</b></div>
          <div><span>未结金额</span><b class="text-warning">¥ {{ money(currentRecord.total_amount - currentRecord.paid_amount) }}</b></div>
        </div>

        <div class="tech-card__title" style="margin: 20px 0 12px">结算明细</div>
        <el-table :data="currentRecord.details" size="small">
          <el-table-column prop="ticket_no" label="磅单号" min-width="160">
            <template #default="{ row }"><span class="mono">{{ row.ticket_no }}</span></template>
          </el-table-column>
          <el-table-column prop="material_name" label="物料" width="100" />
          <el-table-column label="净重" width="84" align="right">
            <template #default="{ row }">{{ weight(row.net_weight) }}</template>
          </el-table-column>
          <el-table-column label="扣杂" width="76" align="right">
            <template #default="{ row }">{{ weight(row.deduct_weight) }}</template>
          </el-table-column>
          <el-table-column label="结算净重" width="96" align="right">
            <template #default="{ row }">{{ weight(row.settle_weight) }}</template>
          </el-table-column>
          <el-table-column label="单价" width="90" align="right">
            <template #default="{ row }">¥{{ Number(row.unit_price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="金额" width="110" align="right">
            <template #default="{ row }"><span class="text-success">¥{{ money(row.final_amount) }}</span></template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <!-- 收付款 -->
    <el-dialog v-model="payVisible" title="登记收付款" width="420px">
      <div v-if="currentRecord" class="pay-body">
        <div class="pay-row"><span>结算单</span><b class="mono text-brand">{{ currentRecord.settle_no }}</b></div>
        <div class="pay-row"><span>应付合计</span><b>¥ {{ money(currentRecord.total_amount) }}</b></div>
        <div class="pay-row"><span>未结金额</span><b class="text-warning">¥ {{ money(currentRecord.total_amount - currentRecord.paid_amount) }}</b></div>
        <div class="pay-row">
          <span>本次金额</span>
          <el-input-number v-model="payAmount" :min="0.01" :max="currentRecord.total_amount - currentRecord.paid_amount" :precision="2" controls-position="right" style="width: 180px" />
        </div>
      </div>
      <template #footer>
        <el-button @click="payVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitPay">确认登记</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { settleApi, weighApi } from '../api'
import { money, payStatus, payTagType, weight } from '../utils/status'

const route = useRoute()
const tab = ref('pending')

const pending = ref([])
const records = ref([])
const selection = ref([])
const keyword = ref('')

const loadingPending = ref(false)
const loadingRecords = ref(false)
const saving = ref(false)

const createVisible = ref(false)
const detailVisible = ref(false)
const payVisible = ref(false)
const currentRecord = ref(null)
const remark = ref('')
const payAmount = ref(0)

const selectedWeight = computed(() =>
  selection.value.reduce((s, r) => s + Number(r.settle_weight || 0), 0)
)
const selectedAmount = computed(() => selection.value.reduce((s, r) => s + Number(r.amount || 0), 0))
const mixedCustomer = computed(() => new Set(selection.value.map((r) => r.customer_id)).size > 1)

async function loadPending() {
  loadingPending.value = true
  try {
    pending.value = await weighApi.unsettledItems({
      customer_id: route.query.customer_id || undefined
    })
  } finally {
    loadingPending.value = false
  }
}

async function loadRecords() {
  loadingRecords.value = true
  try {
    records.value = await settleApi.list({ keyword: keyword.value || undefined })
  } finally {
    loadingRecords.value = false
  }
}

function onTab() {
  if (tab.value === 'pending') loadPending()
  else loadRecords()
}

function onSelect(rows) {
  selection.value = rows
}

function openCreate() {
  if (mixedCustomer.value) return ElMessage.warning('所选批次必须属于同一客户')
  remark.value = ''
  createVisible.value = true
}

async function submitCreate() {
  saving.value = true
  try {
    const rec = await settleApi.create({
      item_ids: selection.value.map((r) => r.item_id),
      settle_mode: 3,
      remark: remark.value || null
    })
    ElMessage.success(`结算单 ${rec.settle_no} 已生成`)
    createVisible.value = false
    await loadPending()
    tab.value = 'records'
    await loadRecords()
  } finally {
    saving.value = false
  }
}

async function openDetail(row) {
  currentRecord.value = await settleApi.detail(row.settle_id)
  detailVisible.value = true
}

function openPay(row) {
  currentRecord.value = { ...row }
  payAmount.value = Math.max(0.01, Math.round((row.total_amount - row.paid_amount) * 100) / 100)
  payVisible.value = true
}

async function submitPay() {
  saving.value = true
  try {
    await settleApi.pay(currentRecord.value.settle_id, { amount: payAmount.value })
    ElMessage.success('收付款已登记')
    payVisible.value = false
    await loadRecords()
  } finally {
    saving.value = false
  }
}

async function cancelRecord(row) {
  try {
    await ElMessageBox.confirm(`确认作废结算单 ${row.settle_no}？批次将退回待结算。`, '作废确认', {
      type: 'warning',
      confirmButtonText: '作废',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  await settleApi.cancel(row.settle_id)
  ElMessage.success('结算单已作废')
  await loadRecords()
}

onMounted(() => {
  loadPending()
  loadRecords()
})
</script>

<style scoped>
.head-actions { display: flex; gap: 10px; }
.head-tools { display: flex; align-items: center; gap: 10px; }

.settle-tabs :deep(.el-tabs__header) { margin-bottom: 14px; }
.settle-tabs :deep(.el-tabs__nav-wrap::after) { background-color: rgba(70, 150, 255, 0.12); }

.create-summary {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  padding: 14px; margin-bottom: 16px; border-radius: 11px;
  background: linear-gradient(120deg, rgba(31, 129, 255, 0.12), rgba(31, 209, 249, 0.05));
  border: 1px solid rgba(70, 150, 255, 0.18);
}
.create-summary div { display: flex; flex-direction: column; gap: 4px; }
.create-summary span { font-size: 11px; color: #7f9ec2; }
.create-summary b { font-size: 15px; }
.mb { margin-bottom: 14px; }

.detail-head { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px; }
.detail-head h3 { margin: 4px 0 0; font-size: 20px; color: #6fd6ff; letter-spacing: 0.6px; }
.detail-head span { font-size: 11px; }
.detail-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px 20px;
  padding: 16px; border-radius: 12px;
  background: rgba(31, 129, 255, 0.06);
  border: 1px solid rgba(70, 150, 255, 0.14);
}
.detail-grid div { display: flex; flex-direction: column; gap: 3px; }
.detail-grid span { font-size: 10.5px; color: #6f8bb0; }
.detail-grid b { font-size: 13px; }

.pay-body { display: grid; gap: 12px; }
.pay-row { display: flex; align-items: center; justify-content: space-between; font-size: 12.5px; }
.pay-row span { color: #7f9ec2; }
</style>
