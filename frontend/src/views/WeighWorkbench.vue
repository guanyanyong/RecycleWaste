<template>
  <div class="page workbench">
    <div class="page-head">
      <div>
        <h1 class="page-title">过磅工作台</h1>
        <p class="page-desc">
          多车并行作业 · 在场 {{ tickets.length }} 单（上限 {{ maxActive }} 单）· 点击卡片切换车辆，左侧表单随时可为下一辆车开单
        </p>
      </div>
      <div class="head-actions">
        <label class="auto-switch">
          <el-switch v-model="autoRefresh" size="small" />
          <span>自动刷新</span>
        </label>
        <el-button plain :loading="refreshing" @click="reloadAll(false)">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-button type="primary" :disabled="!trip" @click="goSettle">
          <el-icon><Wallet /></el-icon> 去结算
        </el-button>
      </div>
    </div>

    <!-- 在场工单：并行车辆队列 -->
    <div class="tech-card tickets">
      <div class="tech-card__head">
        <div class="tech-card__title">在场工单</div>
        <span class="tech-card__sub">
          并行 {{ tickets.length }} 单<template v-if="tickets.length">
            · 共 {{ totalOpenItems }} 个有效批次 · 待核价 {{ pendingPriceTotal }} 件
          </template>
        </span>
      </div>

      <div class="tickets__body" :class="{ 'has-more': railCanNext, 'has-prev': railCanPrev }">
        <button
          v-if="railCanPrev"
          type="button"
          class="rail-nav prev"
          title="上一辆"
          @click="scrollRail(-1)"
        >
          <el-icon><ArrowLeft /></el-icon>
        </button>

        <div ref="railRef" class="tickets__rail" @wheel="onRailWheel" @scroll="updateRailNav">
          <button
            v-for="(t, idx) in tickets"
            :key="t.trip_id"
            type="button"
            class="ticket"
            :class="{ 'is-active': t.trip_id === activeTripId, 'is-done': t.status === 1 }"
            @click="selectTrip(t.trip_id)"
          >
            <div class="ticket__top">
              <span class="ticket__idx mono">{{ String(idx + 1).padStart(2, '0') }}</span>
              <el-tag size="small" effect="plain" :type="t.biz_type === 1 ? 'warning' : 'success'">
                {{ t.biz_type === 1 ? '收货' : '发货' }}
              </el-tag>
              <span class="ticket__state" :class="t.status === 1 ? 'is-done' : 'is-run'">
                <i></i>{{ t.status === 1 ? '待结算' : '作业中' }}
              </span>
              <span
                v-if="t.item_count === 0"
                class="ticket__close"
                title="作废空工单"
                @click.stop="cancelTrip(t)"
              >✕</span>
            </div>

            <div class="ticket__main">
              <b>{{ t.plate_no || t.customer_name }}</b>
              <span>{{ t.plate_no ? t.customer_name : (t.driver_name || '未登记司机') }}</span>
            </div>

            <div class="ticket__metrics">
              <div><span>批次</span><b>{{ t.item_count }}</b></div>
              <div><span>待核价</span><b :class="{ 'text-warning': t.pending_price > 0 }">{{ t.pending_price }}</b></div>
              <div><span>已称重</span><b class="text-brand">{{ t.completed + t.settled }}/{{ t.effective_count }}</b></div>
              <div><span>净重</span><b class="text-cyan num-glow">{{ weight(t.total_settle_weight) }}</b></div>
            </div>

            <div class="ticket__bar"><i :style="{ width: t.progress + '%' }"></i></div>
            <div class="ticket__foot mono">
              <span>{{ t.trip_no }}</span>
              <em>{{ elapsedText(t.elapsed_minutes) }}</em>
            </div>
          </button>
        </div>

        <button
          v-if="railCanNext"
          type="button"
          class="rail-nav next"
          title="下一辆"
          @click="scrollRail(1)"
        >
          <el-icon><ArrowRight /></el-icon>
        </button>

        <button
          type="button"
          class="ticket ticket--new"
          :disabled="tickets.length >= maxActive"
          @click="newTicket"
        >
          <el-icon><Plus /></el-icon>
          <b>新开一单</b>
          <span>{{ tickets.length >= maxActive ? '已达并行上限' : '识别下一辆来车' }}</span>
        </button>
      </div>
    </div>

    <div class="workbench__grid">
      <!-- 左列：开单 + 读数 -->
      <div class="col-left">
        <div class="tech-card">
          <div class="tech-card__head">
            <div class="tech-card__title">01 识别客户 / 开单</div>
            <span class="tech-card__sub">刷卡 · 姓名 · 手机号</span>
          </div>

          <el-form label-position="top" class="trip-form">
            <el-form-item label="业务类型">
              <el-radio-group v-model="form.biz_type">
                <el-radio-button :value="1">收货（付款）</el-radio-button>
                <el-radio-button :value="2">发货（收款）</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="作业站点">
              <el-select v-model="form.station_id" placeholder="选择站点" style="width: 100%">
                <el-option v-for="s in stations" :key="s.station_id" :label="s.station_name" :value="s.station_id" />
              </el-select>
            </el-form-item>

            <el-form-item label="识别客户">
              <el-select
                ref="customerSelectRef"
                v-model="form.customer_id"
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchCustomers"
                :loading="customerLoading"
                :disabled="newCustomer"
                placeholder="输入姓名 / 手机号搜索"
                style="width: 100%"
                @change="onCustomerChange"
              >
                <el-option
                  v-for="c in customers"
                  :key="c.customer_id"
                  :label="`${c.customer_name}（${c.phone || '无手机号'}）`"
                  :value="c.customer_id"
                />
              </el-select>
            </el-form-item>

            <el-checkbox v-model="newCustomer" class="new-customer">
              首次来厂，新建客户
            </el-checkbox>

            <template v-if="newCustomer">
              <el-form-item label="客户姓名">
                <el-input v-model="form.customer_name" placeholder="请输入姓名" maxlength="50" />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="form.customer_phone" placeholder="用于下次快速识别" maxlength="20" />
              </el-form-item>
            </template>

            <div class="two-col">
              <el-form-item label="车牌号">
                <el-input v-model="form.plate_no" placeholder="粤B12345" maxlength="20" />
              </el-form-item>
              <el-form-item label="司机">
                <el-input v-model="form.driver_name" placeholder="选填" maxlength="50" />
              </el-form-item>
            </div>

            <el-button type="primary" class="create-btn" :loading="creating" @click="createTrip">
              <el-icon><Plus /></el-icon> 创建过磅工单
            </el-button>
            <p class="form-hint">
              每次开单代表一辆在场车辆，可连续开单实现多车同时作业；同一车牌不允许重复开单。
            </p>
          </el-form>
        </div>

        <div class="tech-card trip-card" v-if="trip">
          <div class="tech-card__head">
            <div class="tech-card__title">读数记录</div>
            <el-tag :type="tripTagType(trip.status)" effect="dark" size="small">{{ tripStatus(trip.status) }}</el-tag>
          </div>
          <div class="reading-trip mono">{{ trip.trip_no }}</div>
          <div class="readings__list">
            <div class="reading" v-for="r in readings" :key="r.reading_id">
              <i></i>
              <div class="reading__body">
                <b class="num-glow">{{ Number(r.weight).toFixed(2) }} <em>吨</em></b>
                <span>#{{ r.seq }} · {{ fmtTime(r.reading_time) }}</span>
              </div>
            </div>
            <div v-if="!readings.length" class="empty-hint">暂无读数，请添加货物</div>
          </div>

          <div class="trip-actions">
            <el-button plain @click="goSettle">
              <el-icon><Wallet /></el-icon> 去结算
            </el-button>
            <el-button v-if="trip.item_count === 0" plain type="danger" @click="cancelTrip(tickets.find((x) => x.trip_id === trip.trip_id))">
              作废空工单
            </el-button>
          </div>
        </div>
      </div>

      <!-- 右列：选中工单明细 -->
      <div class="col-right">
        <div class="tech-card detail-card" v-if="trip">
          <div class="tech-card__head">
            <div class="tech-card__title">
              02 过磅明细
              <span class="trip-no mono">{{ trip.trip_no }}</span>
              <span v-if="detailLoading" class="loading-hint">同步中…</span>
            </div>
            <div class="legend">
              <span><i class="dot dot-blue"></i>新建</span>
              <span><i class="dot dot-gold"></i>已核价</span>
              <span><i class="dot dot-green"></i>称重完成</span>
            </div>
          </div>

          <div class="trip-hero">
            <div class="hero-item">
              <span>客户</span>
              <b>{{ trip.customer_name }}</b>
              <em>{{ trip.customer_phone || '-' }}</em>
            </div>
            <div class="hero-item">
              <span>车牌 / 司机</span>
              <b>{{ trip.plate_no || '-' }}</b>
              <em>{{ trip.driver_name || '未登记' }}</em>
            </div>
            <div class="hero-item">
              <span>业务</span>
              <b>{{ trip.biz_type === 1 ? '收货（付款）' : '发货（收款）' }}</b>
              <em>{{ tripStatus(trip.status) }}</em>
            </div>
            <div class="hero-item">
              <span>称重进度</span>
              <b>{{ summary.completed || 0 }} / {{ items.filter((i) => i.status !== 4).length }}</b>
              <em>待核价 {{ summary.pending_price || 0 }} 件</em>
            </div>
            <div class="hero-item">
              <span>读数</span>
              <b>{{ readings.length }} 次</b>
              <em>{{ elapsedText(ticketOf(trip.trip_id)?.elapsed_minutes) }}</em>
            </div>
          </div>

          <div class="add-bar">
            <div class="add-bar__row">
              <el-select v-model="addForm.material_id" filterable placeholder="选择物料" style="width: 196px">
                <el-option
                  v-for="m in materials"
                  :key="m.material_id"
                  :label="m.material_name"
                  :value="m.material_id"
                >
                  <span>{{ m.material_name }}</span>
                  <span class="opt-sub">{{ m.category_name }} · ¥{{ Number(m.default_price || 0).toFixed(0) }}/吨</span>
                </el-option>
              </el-select>

              <el-radio-group v-model="addForm.weigh_mode">
                <el-radio-button :value="1">两次过磅</el-radio-button>
                <el-radio-button :value="2">单次过磅</el-radio-button>
              </el-radio-group>

              <el-input-number
                v-model="addForm.weight"
                :min="0.01"
                :max="200"
                :precision="2"
                :step="0.5"
                :disabled="addForm.reuse"
                controls-position="right"
                style="width: 128px"
                placeholder="磅读数"
                @keyup.enter="addItem"
              />
              <span class="unit">吨</span>

              <el-checkbox v-model="addForm.reuse" :disabled="!canReuse || addForm.weigh_mode !== 1">
                沿用上件皮重
                <em v-if="canReuse" class="hint">#{{ lastReadingSeq }}（{{ weight(lastReadingWeight) }} 吨）</em>
              </el-checkbox>

              <el-button type="primary" :loading="adding" @click="addItem">
                <el-icon><Plus /></el-icon> 加入货物
              </el-button>
            </div>
          </div>

          <el-table :data="items" :height="tableHeight" empty-text="暂无货物明细">
            <el-table-column prop="seq" label="#" width="44" align="center">
              <template #default="{ row }"><span class="mono">{{ String(row.seq).padStart(2, '0') }}</span></template>
            </el-table-column>
            <el-table-column label="物料 / 磅单号" min-width="150">
              <template #default="{ row }">
                <div class="mat-cell">
                  <div class="mat-name">
                    {{ row.material_name }}
                    <el-tag size="small" effect="plain" :type="row.weigh_mode === 2 ? 'success' : 'info'">
                      {{ row.weigh_mode === 2 ? '单次' : '两次' }}
                    </el-tag>
                  </div>
                  <span class="mono mat-ticket">{{ row.ticket_no }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="毛重" width="70" align="right">
              <template #default="{ row }"><span class="num-glow">{{ weight(row.start_weight) }}</span></template>
            </el-table-column>
            <el-table-column label="皮重" width="70" align="right">
              <template #default="{ row }">
                <span class="num-glow" :class="{ muted: row.end_weight == null }">{{ weight(row.end_weight) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="净重" width="70" align="right">
              <template #default="{ row }"><span class="num-glow">{{ weight(row.net_weight) }}</span></template>
            </el-table-column>
            <el-table-column label="扣杂" width="70" align="right">
              <template #default="{ row }"><span class="text-warning">{{ weight(row.deduct_weight) }}</span></template>
            </el-table-column>
            <el-table-column label="结算净重" width="84" align="right">
              <template #default="{ row }"><span class="num-glow text-cyan">{{ weight(row.settle_weight) }}</span></template>
            </el-table-column>
            <el-table-column label="状态" width="84" align="center">
              <template #default="{ row }">
                <el-tag :type="itemTagType(row.status)" effect="dark" size="small">{{ itemStatus(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="146" fixed="right" align="center">
              <template #default="{ row }">
                <template v-if="row.status === 0">
                  <el-button size="small" type="warning" @click="openPrice(row)">核价</el-button>
                  <el-button size="small" type="danger" plain @click="cancelItem(row)">作废</el-button>
                </template>
                <template v-else-if="row.status === 1">
                  <el-button size="small" type="primary" @click="openTare(row)">
                    {{ row.weigh_mode === 2 ? '完成' : '录入皮重' }}
                  </el-button>
                  <el-button size="small" type="danger" plain @click="cancelItem(row)">作废</el-button>
                </template>
                <span v-else-if="row.status === 2" class="muted">待结算</span>
                <span v-else-if="row.status === 3" class="text-success">已结算</span>
                <span v-else class="muted">已作废</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="summary-bar">
            <div class="summary-item">
              <span>批次</span><b>{{ items.length }}</b>
            </div>
            <div class="summary-item">
              <span>待核价</span><b class="text-warning">{{ summary.pending_price || 0 }}</b>
            </div>
            <div class="summary-item">
              <span>称重完成</span><b class="text-brand">{{ summary.completed || 0 }}</b>
            </div>
            <div class="summary-item">
              <span>结算净重</span><b class="text-cyan num-glow">{{ weight(summary.total_settle_weight) }} 吨</b>
            </div>
            <div class="summary-item">
              <span>预估金额</span><b class="text-success num-glow">¥ {{ money(summary.total_amount) }}</b>
            </div>
            <div class="summary-item summary-item--tail">
              <el-button size="small" plain @click="reloadAll(false)">同步明细</el-button>
            </div>
          </div>
        </div>

        <div class="tech-card empty-card" v-else>
          <el-icon class="empty-ico"><Odometer /></el-icon>
          <h3>暂无选中的在场工单</h3>
          <p>在左侧识别来车客户并开单，可同时并行 3~5 辆车的过磅作业；也可点击上方卡片切换要操作的车辆。</p>
          <el-button type="primary" plain @click="newTicket">立即开单</el-button>
        </div>
      </div>
    </div>

    <!-- 核价弹窗 -->
    <PriceDialog v-model="priceVisible" :item="currentItem" @success="onItemChanged" />

    <!-- 皮重弹窗 -->
    <el-dialog v-model="tareVisible" :title="currentItem?.weigh_mode === 2 ? '完成称重' : '录入皮重'" width="440px">
      <div class="tare-body" v-if="currentItem">
        <div class="tare-row"><span>磅单号</span><b class="mono text-brand">{{ currentItem.ticket_no }}</b></div>
        <div class="tare-row"><span>物料</span><b>{{ currentItem.material_name }}</b></div>
        <div class="tare-row"><span>毛重</span><b class="num-glow">{{ weight(currentItem.start_weight) }} 吨</b></div>
        <div class="tare-row" v-if="currentItem.weigh_mode === 1">
          <span>皮重</span>
          <el-input-number v-model="tareWeight" :min="0.01" :max="200" :precision="2" :step="0.1" controls-position="right" style="width: 160px" />
          <em>吨</em>
        </div>
        <div class="tare-calc">
          <div><span>净重</span><b class="text-cyan">{{ weight(previewNet) }} 吨</b></div>
          <div><span>预计扣重</span><b class="text-warning">{{ weight(currentItem.deduct_preview ?? currentItem.deduct_weight) }} 吨</b></div>
          <div><span>结算净重</span><b class="text-success">{{ weight(Math.max(0, previewNet - Number(currentItem.deduct_preview ?? currentItem.deduct_weight ?? 0))) }} 吨</b></div>
        </div>
        <p class="tip" v-if="currentItem.weigh_mode === 2">单次过磅模式：本次读数直接作为净重，无需录入皮重。</p>
      </div>
      <template #footer>
        <el-button @click="tareVisible = false">取消</el-button>
        <el-button type="primary" :loading="completing" @click="submitTare">确认完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import { basicApi, weighApi } from '../api'
import { itemStatus, itemTagType, money, tripStatus, tripTagType, weight } from '../utils/status'
import PriceDialog from '../components/PriceDialog.vue'

const router = useRouter()
const POLL_INTERVAL = 12000

const stations = ref([])
const materials = ref([])
const customers = ref([])
const customerLoading = ref(false)
const customerSelectRef = ref(null)
const newCustomer = ref(false)

const form = reactive({
  biz_type: 1,
  station_id: null,
  customer_id: null,
  customer_name: '',
  customer_phone: '',
  plate_no: '',
  driver_name: ''
})

/* ---------------- 在场工单（多车并行） ---------------- */
const tickets = ref([])
const maxActive = ref(12)
const activeTripId = ref(null)
const railRef = ref(null)
const detail = ref(null)
const detailLoading = ref(false)
const refreshing = ref(false)
const autoRefresh = ref(true)
const busy = ref(false)

const trip = computed(() => detail.value?.trip || null)
const items = computed(() => detail.value?.items || [])
const readings = computed(() => detail.value?.readings || [])
const summary = computed(() => detail.value?.summary || {})
const totalOpenItems = computed(() => tickets.value.reduce((n, t) => n + t.effective_count, 0))
const pendingPriceTotal = computed(() => tickets.value.reduce((n, t) => n + t.pending_price, 0))

/* ---------------- 表单与弹窗状态 ---------------- */
const creating = ref(false)
const adding = ref(false)
const completing = ref(false)

// 每张工单独立草稿：切换车辆时不丢失已输入的磅读数与物料
const drafts = reactive({})
const fallbackDraft = reactive({ material_id: null, weight: null, weigh_mode: 1, reuse: false })

function draftOf(tripId) {
  if (!tripId) return fallbackDraft
  if (!drafts[tripId]) {
    drafts[tripId] = {
      material_id: materials.value[0]?.material_id || null,
      weight: null,
      weigh_mode: 1,
      reuse: false
    }
  }
  return drafts[tripId]
}
const addForm = computed(() => draftOf(activeTripId.value))

const priceVisible = ref(false)
const currentItem = ref(null)
const tareVisible = ref(false)
const tareWeight = ref(0)

/* ---------------- 派生数据 ---------------- */
function endReadingOf(list) {
  const arr = [...(list || [])].reverse()
  return arr.find((i) => i.end_reading_id)?.end_reading_id || null
}

const lastEndReading = computed(() => endReadingOf(items.value))
const canReuse = computed(() => Boolean(lastEndReading.value))
const lastReading = computed(() => {
  if (!lastEndReading.value) return null
  return readings.value.find((r) => r.reading_id === lastEndReading.value) || null
})
const lastReadingSeq = computed(() => lastReading.value?.seq ?? '-')
const lastReadingWeight = computed(() => lastReading.value?.weight ?? 0)

const previewNet = computed(() => {
  if (!currentItem.value) return 0
  if (currentItem.value.weigh_mode === 2) return Number(currentItem.value.start_weight || 0)
  const v = Number(currentItem.value.start_weight || 0) - Number(tareWeight.value || 0)
  return Math.max(0, Math.round(v * 100) / 100)
})

/* 明细表格高度：随窗口自适应 */
const viewportH = ref(typeof window === 'undefined' ? 900 : window.innerHeight)
const tableHeight = computed(() => Math.max(200, viewportH.value - 688))
function onResize() {
  viewportH.value = window.innerHeight
  updateRailNav()
}

function fmtTime(v) {
  return v ? dayjs(v).format('HH:mm:ss') : '-'
}

function elapsedText(minutes) {
  const m = Number(minutes || 0)
  if (m < 1) return '刚刚开单'
  if (m < 60) return `${m} 分钟`
  return `${Math.floor(m / 60)} 小时 ${m % 60} 分`
}

function ticketOf(tripId) {
  return tickets.value.find((t) => t.trip_id === tripId) || null
}

/* ---------------- 数据加载 ---------------- */
async function loadRefs(silent = true) {
  const [st, mt] = await Promise.all([basicApi.stations(), basicApi.materials({ status: 1 })])
  stations.value = st
  materials.value = mt
  if (!form.station_id && st.length) form.station_id = st[0].station_id
  if (!silent) ElMessage.success('基础数据已刷新')
}

async function searchCustomers(keyword) {
  customerLoading.value = true
  try {
    customers.value = await basicApi.searchCustomers({ keyword: keyword || undefined })
  } finally {
    customerLoading.value = false
  }
}

async function refreshTickets() {
  const data = await weighApi.activeTrips()
  tickets.value = data.trips || []
  maxActive.value = data.max_active || 12

  // 清理已离场工单的草稿
  Object.keys(drafts).forEach((key) => {
    if (!tickets.value.some((t) => String(t.trip_id) === String(key))) delete drafts[key]
  })

  if (!tickets.value.length) {
    activeTripId.value = null
    detail.value = null
    return
  }

  const currentAlive = tickets.value.some((t) => t.trip_id === activeTripId.value)
  if (!currentAlive) {
    const hadSelection = activeTripId.value !== null
    // 优先落到有批次、需要继续操作的工单上，避免空工单占用明细区
    const next = tickets.value.find((t) => t.item_count > 0) || tickets.value[0]
    await selectTrip(next.trip_id)
    if (hadSelection) {
      ElMessage.info(`原工单已完结，已切换到 ${next.plate_no || next.customer_name} 的工单`)
    }
  }
}

/* 工单队列横向滚动：滚轮上下即左右浏览，选中项自动滚入可视区 */
const railCanPrev = ref(false)
const railCanNext = ref(false)

function updateRailNav() {
  const el = railRef.value
  if (!el) return
  railCanPrev.value = el.scrollLeft > 4
  railCanNext.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 4
}

function scrollRail(dir) {
  const el = railRef.value
  if (!el) return
  el.scrollBy({ left: dir * Math.max(240, el.clientWidth * 0.7), behavior: 'smooth' })
}

function onRailWheel(e) {
  if (!railRef.value || e.deltaX || !e.deltaY) return
  railRef.value.scrollLeft += e.deltaY
  e.preventDefault()
}

watch(activeTripId, async (id) => {
  if (!id) return
  await nextTick()
  railRef.value
    ?.querySelector('.ticket.is-active')
    ?.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' })
  setTimeout(updateRailNav, 320)
})

watch(() => tickets.value.length, async () => {
  await nextTick()
  updateRailNav()
})

async function selectTrip(tripId) {
  if (!tripId) {
    activeTripId.value = null
    detail.value = null
    return
  }
  activeTripId.value = tripId
  detailLoading.value = true
  try {
    detail.value = await weighApi.tripDetail(tripId)
    const draft = draftOf(tripId)
    if (draft.reuse && !endReadingOf(detail.value.items)) draft.reuse = false
  } finally {
    detailLoading.value = false
  }
}

async function refreshCurrent() {
  if (!activeTripId.value) return
  detail.value = await weighApi.tripDetail(activeTripId.value)
}

async function reloadAll(silent = true) {
  if (!silent) refreshing.value = true
  try {
    await refreshTickets()
    if (activeTripId.value) await refreshCurrent()
    if (!silent) ElMessage.success('在场工单已刷新')
  } finally {
    refreshing.value = false
  }
}

async function onItemChanged() {
  await refreshTickets()
  if (activeTripId.value) await refreshCurrent()
}

/* ---------------- 开单 ---------------- */
function resetForm() {
  form.customer_id = null
  form.customer_name = ''
  form.customer_phone = ''
  form.plate_no = ''
  form.driver_name = ''
  newCustomer.value = false
  searchCustomers('')
}

function newTicket() {
  resetForm()
  customerSelectRef.value?.focus?.()
}

function onCustomerChange(id) {
  const c = customers.value.find((x) => x.customer_id === id)
  if (c) {
    form.customer_name = c.customer_name
    form.customer_phone = c.phone || ''
  }
}

async function createTrip() {
  if (!form.station_id) return ElMessage.warning('请选择作业站点')
  if (!form.customer_id && !form.customer_name) return ElMessage.warning('请识别客户或填写客户姓名')
  if (tickets.value.length >= maxActive.value) {
    return ElMessage.warning(`在场工单已达并行上限 ${maxActive.value} 单，请先完成部分工单`)
  }

  creating.value = true
  busy.value = true
  try {
    const data = await weighApi.createTrip({
      station_id: form.station_id,
      biz_type: form.biz_type,
      customer_id: form.customer_id || null,
      customer_name: form.customer_id ? null : form.customer_name,
      customer_phone: form.customer_id ? null : form.customer_phone || null,
      plate_no: form.plate_no || null,
      driver_name: form.driver_name || null
    })
    activeTripId.value = data.trip.trip_id
    detail.value = data
    draftOf(data.trip.trip_id)
    resetForm()
    await refreshTickets()
    ElMessage.success(`已开单 ${data.trip.trip_no}，可继续为下一辆车开单`)
  } finally {
    creating.value = false
    busy.value = false
  }
}

/* ---------------- 明细操作 ---------------- */
async function addItem() {
  if (!trip.value) return ElMessage.warning('请先选择或新开一张工单')
  const draft = addForm.value
  if (!draft.material_id) return ElMessage.warning('请选择物料')
  if (!draft.reuse && (!draft.weight || draft.weight <= 0)) return ElMessage.warning('请输入地磅读数')

  adding.value = true
  busy.value = true
  try {
    detail.value = await weighApi.addItem(trip.value.trip_id, {
      material_id: draft.material_id,
      weight: draft.reuse ? null : draft.weight,
      weigh_mode: draft.weigh_mode,
      reuse_reading_id: draft.reuse ? lastEndReading.value : null
    })
    draft.weight = null
    draft.reuse = false
    ElMessage.success(`已加入 ${trip.value.plate_no || trip.value.customer_name} 的过磅明细`)
    await refreshTickets()
  } finally {
    adding.value = false
    busy.value = false
  }
}

function openPrice(row) {
  currentItem.value = row
  priceVisible.value = true
}

function openTare(row) {
  currentItem.value = row
  tareWeight.value = 0
  tareVisible.value = true
}

async function submitTare() {
  if (!currentItem.value) return
  if (currentItem.value.weigh_mode === 1 && (!tareWeight.value || tareWeight.value <= 0)) {
    return ElMessage.warning('请输入皮重')
  }
  if (currentItem.value.weigh_mode === 1 && tareWeight.value >= Number(currentItem.value.start_weight)) {
    return ElMessage.warning('皮重必须小于毛重')
  }
  completing.value = true
  busy.value = true
  try {
    await weighApi.complete(currentItem.value.item_id, {
      end_weight: currentItem.value.weigh_mode === 1 ? tareWeight.value : null
    })
    tareVisible.value = false
    await onItemChanged()
    ElMessage.success('称重完成，可进入结算')
  } finally {
    completing.value = false
    busy.value = false
  }
}

async function cancelItem(row) {
  try {
    await ElMessageBox.confirm(`确认作废批次 ${row.ticket_no}？`, '作废确认', {
      type: 'warning',
      confirmButtonText: '作废',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  await weighApi.cancel(row.item_id)
  await onItemChanged()
  ElMessage.success('已作废')
}

async function cancelTrip(t) {
  if (!t) return
  try {
    await ElMessageBox.confirm(
      `作废工单 ${t.trip_no}？该操作仅适用于尚未录入有效批次的工单。`,
      '作废工单',
      { type: 'warning', confirmButtonText: '作废', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  busy.value = true
  try {
    await weighApi.cancelTrip(t.trip_id)
    if (activeTripId.value === t.trip_id) {
      activeTripId.value = null
      detail.value = null
    }
    await refreshTickets()
    ElMessage.success('工单已作废并移出工作台')
  } finally {
    busy.value = false
  }
}

function goSettle() {
  if (!trip.value) return ElMessage.warning('请先选择工单')
  router.push({ path: '/settlement', query: { customer_id: trip.value.customer_id } })
}

/* ---------------- 轮询：其他磅房/操作员的开单实时可见 ---------------- */
let timer = null
function stopPolling() {
  if (timer) clearInterval(timer)
  timer = null
}
function startPolling() {
  stopPolling()
  timer = setInterval(async () => {
    if (!autoRefresh.value || busy.value || priceVisible.value || tareVisible.value || creating.value) return
    try {
      await refreshTickets()
      if (activeTripId.value && !priceVisible.value && !tareVisible.value) await refreshCurrent()
    } catch {
      /* 轮询失败静默，等待下一次 */
    }
  }, POLL_INTERVAL)
}

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await loadRefs()
  await searchCustomers('')
  await refreshTickets()
  await nextTick()
  updateRailNav()
  startPolling()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  stopPolling()
})
</script>

<style scoped>
.workbench { display: flex; flex-direction: column; gap: 16px; }
.workbench__grid { display: grid; grid-template-columns: 316px minmax(0, 1fr); gap: 16px; align-items: start; }
.col-left { display: flex; flex-direction: column; gap: 16px; }

.head-actions { display: flex; align-items: center; gap: 10px; }
.auto-switch {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; color: var(--text-3); cursor: pointer;
}

/* ---------------- 在场工单卡片 ---------------- */
.tickets { padding: 14px 16px 12px; }
.tickets .tech-card__head { margin-bottom: 10px; }
.tickets__body { position: relative; display: flex; align-items: stretch; gap: 10px; }
.tickets__rail {
  flex: 1 1 auto; min-width: 0;
  display: flex; gap: 10px; align-items: stretch;
  overflow-x: auto; overflow-y: hidden; padding: 2px 2px 6px;
}

.rail-nav {
  position: absolute; top: 50%; transform: translateY(-50%); z-index: 4;
  width: 24px; height: 52px; padding: 0; cursor: pointer;
  display: flex; align-items: center; justify-content: center; font-size: 13px;
  color: #bfe0ff;
  background: linear-gradient(180deg, rgba(18, 44, 80, 0.98), rgba(8, 22, 42, 0.98));
  border: 1px solid rgba(79, 155, 255, 0.55); border-radius: 8px;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.55), 0 0 12px rgba(31, 129, 255, 0.25);
  transition: all 0.16s ease;
}
.rail-nav:hover { color: #fff; border-color: rgba(31, 209, 249, 0.75); box-shadow: 0 0 16px rgba(31, 209, 249, 0.45); }
.rail-nav.prev { left: -6px; }
.rail-nav.next { right: 132px; }

/* 右侧渐隐，提示还有更多在场工单 */
.tickets__body::after {
  content: ''; position: absolute; z-index: 3; top: 2px; bottom: 6px; right: 118px; width: 46px;
  background: linear-gradient(90deg, rgba(8, 22, 42, 0) 0%, rgba(8, 22, 42, 0.86) 62%, rgba(9, 24, 45, 0.97) 100%);
  opacity: 0; transition: opacity 0.18s ease; pointer-events: none;
}
.tickets__body.has-more::after { opacity: 1; }

.ticket {
  position: relative; flex: 0 0 226px; width: 226px; text-align: left;
  padding: 9px 11px 8px; border-radius: 12px; cursor: pointer;
  background: linear-gradient(155deg, rgba(13, 36, 68, 0.92), rgba(7, 19, 38, 0.88));
  border: 1px solid rgba(70, 150, 255, 0.16);
  color: inherit; font-family: inherit;
  transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
  overflow: hidden;
}
.ticket:hover { border-color: rgba(79, 155, 255, 0.5); transform: translateY(-2px); }
.ticket.is-active {
  border-color: rgba(31, 209, 249, 0.62);
  background: linear-gradient(155deg, rgba(20, 58, 104, 0.96), rgba(9, 26, 50, 0.92));
  box-shadow: 0 0 0 1px rgba(31, 209, 249, 0.32), 0 12px 30px rgba(31, 129, 255, 0.28);
}
.ticket.is-active::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--cyan), var(--brand));
  box-shadow: 0 0 12px rgba(31, 209, 249, 0.9);
}

.ticket__top { display: flex; align-items: center; gap: 6px; }
.ticket__idx { font-size: 10px; color: #5f7f9f; letter-spacing: 0.5px; }
.ticket__state {
  display: inline-flex; align-items: center; gap: 4px;
  margin-left: auto; font-size: 10.5px; letter-spacing: 0.3px;
}
.ticket__state i { width: 5px; height: 5px; border-radius: 50%; }
.ticket__state.is-run { color: var(--cyan); }
.ticket__state.is-run i { background: var(--cyan); box-shadow: 0 0 8px var(--cyan); animation: dot-pulse 1.6s ease-in-out infinite; }
.ticket__state.is-done { color: var(--warning); }
.ticket__state.is-done i { background: var(--warning); box-shadow: 0 0 8px var(--warning); }
@keyframes dot-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.35; transform: scale(0.8); }
}
.ticket__close {
  margin-left: 2px; font-size: 11px; line-height: 1; color: #6f8bb0;
  padding: 2px 3px; border-radius: 4px; transition: all 0.15s ease;
}
.ticket__close:hover { color: var(--danger); background: rgba(255, 92, 122, 0.14); }

.ticket__main { display: flex; flex-direction: column; gap: 2px; margin-top: 6px; }
.ticket__main b {
  font-size: 14px; letter-spacing: 0.4px; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ticket__main span { font-size: 10.5px; color: var(--text-3); }

.ticket__metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; margin-top: 8px; }
.ticket__metrics div { display: flex; flex-direction: column; gap: 1px; }
.ticket__metrics span { font-size: 9.5px; color: #5f7f9f; }
.ticket__metrics b { font-size: 12px; color: var(--text-2); }

.ticket__bar { height: 3px; border-radius: 3px; margin-top: 8px; background: rgba(60, 120, 200, 0.22); overflow: hidden; }
.ticket__bar i {
  display: block; height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--brand), var(--cyan));
  box-shadow: 0 0 10px rgba(31, 209, 249, 0.6);
  transition: width 0.4s ease;
}
.ticket__foot {
  display: flex; justify-content: space-between; gap: 8px;
  margin-top: 5px; font-size: 9.5px; color: #4f6d90;
}
.ticket__foot em { font-style: normal; color: #4f6d90; }

.ticket--new {
  flex: 0 0 118px; width: 118px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
  border-style: dashed; color: #7f9ec2; text-align: center;
}
.ticket--new b { font-size: 12.5px; color: var(--brand-light); }
.ticket--new span { font-size: 10px; color: #5f7f9f; }
.ticket--new .el-icon { font-size: 18px; color: var(--brand-light); }
.ticket--new:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

/* ---------------- 左列表单 ---------------- */
.trip-form :deep(.el-form-item) { margin-bottom: 10px; }
.trip-form :deep(.el-form-item__label) { font-size: 12px; color: #8fb0d4; padding-bottom: 5px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.new-customer { margin: -2px 0 12px; }
.create-btn { width: 100%; height: 40px; margin-top: 2px; }
.form-hint { margin: 8px 0 0; font-size: 11px; line-height: 1.7; color: #5f7f9f; }

.trip-card { padding-bottom: 14px; }
.reading-trip { font-size: 12px; letter-spacing: 0.6px; color: #6fd6ff; margin: -6px 0 10px; }
.readings__list { max-height: 122px; overflow-y: auto; display: grid; gap: 8px; }
.reading { display: flex; gap: 10px; align-items: flex-start; }
.reading i {
  width: 7px; height: 7px; border-radius: 50%; margin-top: 6px;
  background: #4fd8ff; box-shadow: 0 0 8px #4fd8ff;
}
.reading__body { display: flex; flex-direction: column; }
.reading__body b { font-size: 13px; color: #dbeafe; }
.reading__body b em { font-style: normal; font-size: 10px; color: #6f8bb0; }
.reading__body span { font-size: 10.5px; color: #5f7f9f; }
.empty-hint { font-size: 11.5px; color: #5c7899; padding: 8px 0; }
.trip-actions { display: flex; gap: 8px; margin-top: 10px; }
.trip-actions .el-button { flex: 1; margin-left: 0; }

/* ---------------- 右侧明细 ---------------- */
.detail-card { display: flex; flex-direction: column; }
.trip-no { font-size: 11px; color: #6fd6ff; letter-spacing: 0.4px; font-weight: 400; }
.loading-hint { font-size: 10.5px; color: var(--text-3); font-weight: 400; }
.legend { display: flex; gap: 14px; font-size: 11px; color: #7f9ec2; }
.legend span { display: inline-flex; align-items: center; gap: 5px; }
.dot { width: 6px; height: 6px; border-radius: 50%; }
.dot-blue { background: #4f9bff; }
.dot-gold { background: #ffb84d; }
.dot-green { background: #22e0a1; }

.trip-hero {
  display: flex; align-items: center; gap: 26px; flex-wrap: wrap;
  padding: 9px 14px; margin-bottom: 12px; border-radius: 10px;
  background: linear-gradient(100deg, rgba(18, 48, 90, 0.7), rgba(8, 24, 46, 0.5));
  border: 1px solid rgba(70, 150, 255, 0.14);
}
.hero-item { display: flex; flex-direction: column; gap: 1px; min-width: 92px; }
.hero-item span { font-size: 10px; color: #6f8bb0; letter-spacing: 0.4px; }
.hero-item b { font-size: 13px; color: var(--text-1); }
.hero-item em { font-style: normal; font-size: 10px; color: #5f7f9f; }

.add-bar {
  padding: 10px 12px; margin-bottom: 12px; border-radius: 11px;
  background: linear-gradient(100deg, rgba(31, 129, 255, 0.1), rgba(31, 209, 249, 0.04));
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.add-bar__row { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
.hint { font-size: 10.5px; color: #5f7f9f; letter-spacing: 0.2px; font-style: normal; }
.unit { font-size: 11.5px; color: #6f8bb0; margin-left: -2px; }
.opt-sub { float: right; margin-left: 18px; font-size: 11px; color: #6f8bb0; }

.mat-cell { display: flex; flex-direction: column; gap: 3px; line-height: 1.2; }
.mat-name { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #dbeafe; }
.mat-ticket { font-size: 9.5px; color: #5f86b8; letter-spacing: -0.2px; }

.summary-bar {
  display: flex; align-items: center; gap: 34px; flex-wrap: wrap;
  margin-top: 12px; padding: 12px 16px; border-radius: 11px;
  background: linear-gradient(100deg, rgba(10, 30, 58, 0.8), rgba(6, 18, 36, 0.6));
  border: 1px solid rgba(70, 150, 255, 0.14);
}
.summary-item { display: flex; flex-direction: column; gap: 4px; }
.summary-item span { font-size: 10.5px; color: #6f8bb0; letter-spacing: 0.5px; }
.summary-item b { font-size: 15px; }
.summary-item--tail { margin-left: auto; }

.empty-card { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 80px 24px; text-align: center; }
.empty-ico { font-size: 40px; color: rgba(79, 155, 255, 0.55); }
.empty-card h3 { margin: 0; font-size: 15px; color: var(--text-1); letter-spacing: 0.5px; }
.empty-card p { margin: 0; max-width: 420px; font-size: 12px; line-height: 1.8; color: var(--text-3); }

.tare-body { display: grid; gap: 10px; }
.tare-row { display: flex; align-items: center; gap: 10px; font-size: 12.5px; }
.tare-row span { width: 64px; color: #7f9ec2; }
.tare-row em { font-style: normal; color: #6f8bb0; font-size: 11px; }
.tare-calc {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
  margin-top: 6px; padding: 12px; border-radius: 10px;
  background: rgba(31, 129, 255, 0.08); border: 1px solid rgba(70, 150, 255, 0.16);
}
.tare-calc div { display: flex; flex-direction: column; gap: 4px; }
.tare-calc span { font-size: 10.5px; color: #7f9ec2; }
.tare-calc b { font-size: 13.5px; }
.tip { margin: 4px 0 0; font-size: 11.5px; color: #7f9ec2; line-height: 1.7; }

@media (max-width: 1280px) {
  .workbench__grid { grid-template-columns: 300px minmax(0, 1fr); }
  .trip-hero { gap: 18px; }
}
</style>
