<template>
  <div class="touch">
    <!-- 顶部状态条 -->
    <header class="bar">
      <div class="bar__brand">
        <div class="bar__mark"><el-icon><ScaleToOriginal /></el-icon></div>
        <div class="bar__name">
          <b>触摸过磅台</b>
          <span>TOUCH WEIGH STATION</span>
        </div>
      </div>

      <div class="bar__stats">
        <div class="stat"><span>在场车辆</span><b>{{ tickets.length }}</b></div>
        <div class="stat"><span>待核价</span><b class="text-warning">{{ totalPending }}</b></div>
        <div class="stat"><span>待称皮重</span><b class="text-cyan">{{ totalTare }}</b></div>
        <div class="stat"><span>已完成净重</span><b class="text-success">{{ w2(totalDoneWeight) }}</b><em>吨</em></div>
      </div>

      <div class="bar__right">
        <div class="bar__clock">
          <b>{{ clock.time }}</b>
          <span>{{ clock.date }}</span>
        </div>
        <button class="bar__icon" title="全屏" @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
        </button>
        <button class="bar__icon" title="返回控制台" @click="goBack">
          <el-icon><Back /></el-icon>
        </button>
      </div>
    </header>

    <transition name="banner">
      <div v-if="banner.show" class="banner" :class="`banner--${banner.type}`">{{ banner.text }}</div>
    </transition>

    <div class="body">
      <!-- 左：在场车辆 -->
      <aside class="lane">
        <div class="lane__head">
          <span>在场车辆</span>
          <b>{{ tickets.length }}<em>/{{ maxActive }}</em></b>
        </div>

        <div class="lane__list">
          <button
            v-for="t in tickets"
            :key="t.trip_id"
            type="button"
            class="vcard"
            :class="{ 'is-active': t.trip_id === tripId }"
            @click="selectTrip(t)"
          >
            <div class="vcard__top">
              <span class="vcard__plate">{{ t.plate_no || '无牌车' }}</span>
              <span v-if="t.pending_price" class="tag tag--warn">{{ t.pending_price }} 待核价</span>
              <span v-else-if="t.status === 1" class="tag tag--done">待结算</span>
              <span v-else class="tag tag--run">在办</span>
            </div>
            <div class="vcard__name">{{ t.customer_name }}</div>
            <div class="vcard__bar"><i :style="{ width: t.progress + '%' }"></i></div>
            <div class="vcard__foot">
              <span>{{ t.item_count }} 批 · {{ w2(t.total_settle_weight) }} 吨</span>
              <em>{{ elapsedText(t.elapsed_minutes) }}</em>
            </div>
          </button>

          <button
            type="button"
            class="vcard vcard--new"
            :disabled="tickets.length >= maxActive"
            @click="openNewTrip"
          >
            <el-icon><Plus /></el-icon>
            <b>新车辆</b>
            <span>{{ tickets.length >= maxActive ? '已达上限' : '登记来车' }}</span>
          </button>
        </div>
      </aside>

      <!-- 右：操作台 -->
      <main class="stage">
        <!-- ① 登记来车 -->
        <section v-if="panel === 'newTrip'" class="pane">
          <header class="pane__head">
            <div>
              <h2>登记来车</h2>
              <p>全程点选，不需要键盘</p>
            </div>
            <div class="pane__badge">{{ stationName }}</div>
          </header>

          <div class="fld">
            <div class="fld__label">1 · 业务类型</div>
            <div class="pick2">
              <button
                type="button"
                class="pick"
                :class="{ on: newTrip.biz_type === 1 }"
                @click="newTrip.biz_type = 1"
              >
                <b>收货</b>
                <span>客户送货来 · 我方付款</span>
              </button>
              <button
                type="button"
                class="pick"
                :class="{ on: newTrip.biz_type === 2 }"
                @click="newTrip.biz_type = 2"
              >
                <b>发货</b>
                <span>客户拉货走 · 我方收款</span>
              </button>
            </div>
          </div>

          <div class="fld fld--grow">
            <div class="fld__label">
              2 · 选择客户
              <em v-if="newTrip.customer_id || newTrip.customer_name">{{ newTrip.customer_name }}</em>
              <button v-if="customerKeyword" class="fld__reset" @click="customerKeyword = ''">显示全部</button>
            </div>
            <div class="cust-grid">
              <button
                v-for="c in visibleCustomers"
                :key="c.customer_id"
                type="button"
                class="cust"
                :class="{ on: newTrip.customer_id === c.customer_id }"
                @click="pickCustomer(c)"
              >
                <b>{{ c.customer_name }}</b>
                <span>{{ c.phone || '无手机号' }}</span>
              </button>

              <button type="button" class="cust cust--act" @click="openPhoneSheet('search')">
                <el-icon><Iphone /></el-icon>
                <b>按手机号找</b>
                <span>触摸数字键盘</span>
              </button>
              <button type="button" class="cust cust--act" @click="openPhoneSheet('new')">
                <el-icon><Plus /></el-icon>
                <b>新客户登记</b>
                <span>手机号即可</span>
              </button>

              <div v-if="!visibleCustomers.length" class="blank blank--inline">
                没有匹配的客户，可点右侧「登记新客户」
              </div>
            </div>
          </div>

          <div class="fld">
            <div class="fld__label">3 · 车牌（可不填）</div>
            <button type="button" class="plate-btn" @click="openPlateSheet">
              <span class="mono">{{ newTrip.plate_no || '点击输入车牌' }}</span>
              <em>触摸车牌键盘</em>
            </button>
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost" @click="cancelNewTrip">取消</button>
            <button
              class="big big--primary"
              :disabled="!canCreate || busy"
              @click="doCreateTrip"
            >
              开单 · 开始过磅
            </button>
          </footer>
        </section>

        <!-- ② 本车工作台 -->
        <section v-else-if="panel === 'trip' && trip" class="pane">
          <header class="vhead">
            <div class="vhead__plate">{{ trip.plate_no || '无牌车' }}</div>
            <div class="vhead__meta">
              <b>{{ trip.customer_name }}</b>
              <span>
                {{ trip.biz_type === 1 ? '收货 · 我方付款' : '发货 · 我方收款' }} · {{ trip.trip_no }}
              </span>
            </div>
            <div class="vhead__stats">
              <div><span>批次</span><b>{{ liveItems.length }}</b></div>
              <div><span>待核价</span><b class="text-warning">{{ pendingPrice.length }}</b></div>
              <div><span>待皮重</span><b class="text-cyan">{{ needTare.length }}</b></div>
              <div><span>净重合计</span><b class="text-success">{{ w2(tripWeight) }}</b></div>
            </div>
          </header>

          <div class="ilist">
            <button
              v-for="it in items"
              :key="it.item_id"
              type="button"
              class="icard"
              :class="[`s${it.status}`, { 'is-act': it.status === 0 || it.status === 1 }]"
              @click="tapItem(it)"
            >
              <span class="icard__no mono">{{ String(it.seq).padStart(2, '0') }}</span>
              <span class="icard__mat">
                <b>{{ it.material_name }}</b>
                <em class="mono">{{ it.ticket_no }}</em>
              </span>
              <span class="icard__nums">
                <i><em>毛重</em><b>{{ w2(it.start_weight) }}</b></i>
                <i><em>皮重</em><b :class="{ dim: it.end_weight == null }">{{ w2(it.end_weight) }}</b></i>
                <i><em>净重</em><b>{{ w2(it.net_weight) }}</b></i>
                <i><em>扣杂</em><b class="text-warning">{{ w2(it.deduct_weight) }}</b></i>
                <i><em>结算</em><b class="text-cyan">{{ w2(it.settle_weight) }}</b></i>
              </span>
              <span class="icard__state" :class="`t${it.status}`">{{ itemStatus(it.status) }}</span>
              <span class="icard__cta" :class="{ idle: it.status >= 2 }">{{ ctaText(it) }}</span>
            </button>

            <div v-if="!items.length" class="blank">
              <el-icon><Box /></el-icon>
              <b>本车还没有货物</b>
              <span>点击下方「加一批货」开始过磅</span>
            </div>
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost-danger" @click="askCancelTrip">作废本车</button>
            <button class="big big--primary" @click="startAdd">
              <el-icon><Plus /></el-icon> 加一批货
            </button>
          </footer>
        </section>

        <!-- ③ 选物料 -->
        <section v-else-if="panel === 'material' && trip" class="pane">
          <header class="pane__head">
            <div>
              <h2>选择物料</h2>
              <p>{{ trip.plate_no || trip.customer_name }} · 第 {{ liveItems.length + 1 }} 批</p>
            </div>
            <div class="pane__badge">触摸点选</div>
          </header>

          <div class="chips">
            <button
              v-for="c in categories"
              :key="c.name"
              type="button"
              class="chipbtn"
              :class="{ on: categoryFilter === c.name }"
              @click="categoryFilter = c.name"
            >
              {{ c.name }}<em>{{ c.count }}</em>
            </button>
          </div>

          <div class="mgrid">
            <button
              v-for="m in filteredMaterials"
              :key="m.material_id"
              type="button"
              class="mtile"
              @click="pickMaterial(m)"
            >
              <b>{{ m.material_name }}</b>
              <span class="mtile__cat">{{ m.category_name || '未分类' }}</span>
              <em class="mtile__price">
                ¥{{ m.default_price ? Number(m.default_price).toFixed(0) : '—' }}<i>/吨</i>
              </em>
            </button>
            <div v-if="!filteredMaterials.length" class="blank blank--inline">该分类下暂无可用物料</div>
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost" @click="panel = 'trip'">返回本车</button>
          </footer>
        </section>

        <!-- ④ 录毛重 -->
        <section v-else-if="panel === 'weight' && trip" class="pane pane--pad">
          <header class="pad__head">
            <div class="pad__title">
              <h2>{{ selectedMaterial?.material_name || '过磅' }}</h2>
              <p>{{ trip.plate_no || trip.customer_name }} · 第 {{ liveItems.length + 1 }} 批</p>
            </div>
            <div class="modes">
              <button type="button" :class="{ on: wDraft.weigh_mode === 1 }" @click="setWeighMode(1)">
                <b>两次过磅</b><span>先毛重，回空再称皮重</span>
              </button>
              <button type="button" :class="{ on: wDraft.weigh_mode === 2 }" @click="setWeighMode(2)">
                <b>单次过磅</b><span>本次读数即为净重</span>
              </button>
            </div>
          </header>

          <div class="screen" :class="{ 'is-reuse': wDraft.reuse }">
            <span class="screen__label">{{ wDraft.reuse ? '沿用上件皮重读数' : '地磅读数' }}</span>
            <div class="screen__value mono">
              {{ wDraft.reuse ? w2(reuseReading?.weight) : (wDraft.value || '0') }}<em>吨</em>
            </div>
            <span class="screen__hint" v-if="wDraft.reuse">引用读数 #{{ reuseReading?.seq }}</span>
            <span class="screen__hint" v-else>点击下方数字键盘输入</span>
          </div>

          <button
            v-if="canReuse"
            type="button"
            class="reuse"
            :class="{ on: wDraft.reuse }"
            @click="wDraft.reuse = !wDraft.reuse"
          >
            <span class="reuse__ico">↺</span>
            <span class="reuse__txt">
              <b>沿用上件皮重</b>
              <em>#{{ reuseReading?.seq }} · {{ w2(reuseReading?.weight) }} 吨（同车多货共用一次读数）</em>
            </span>
            <span class="reuse__state">{{ wDraft.reuse ? '已启用' : '点击启用' }}</span>
          </button>

          <div class="kpad" :class="{ 'is-off': wDraft.reuse }">
            <TouchKeypad
              v-model="wDraft.value"
              mode="decimal"
              :max-int="4"
              confirm-text="下一步 · 核价"
              @confirm="submitWeight"
            />
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost" @click="panel = 'material'">上一步</button>
            <button v-if="wDraft.reuse" class="big big--primary" @click="submitWeight">
              使用该皮重 · 下一步
            </button>
          </footer>
        </section>

        <!-- ⑤ 核价 -->
        <section v-else-if="panel === 'price' && priceItem" class="pane pane--pad">
          <header class="pad__head">
            <div class="pad__title">
              <h2>核价 · {{ priceItem.material_name }}</h2>
              <p>
                毛重 {{ w2(priceItem.start_weight) }} 吨 ·
                {{ priceItem.weigh_mode === 2 ? '单次过磅' : '两次过磅' }}
              </p>
            </div>
            <div class="basis">
              <span>扣重基数</span>
              <button type="button" :class="{ on: pDraft.calc_base === 2 }" @click="pDraft.calc_base = 2">净重</button>
              <button type="button" :class="{ on: pDraft.calc_base === 1 }" @click="pDraft.calc_base = 1">毛重</button>
            </div>
          </header>

          <div class="fields">
            <button
              type="button"
              class="kfield"
              :class="{ on: pDraft.field === 'price' }"
              @click="pDraft.field = 'price'"
            >
              <span>单价（元 / 吨）</span>
              <b class="mono">{{ pDraft.price || '0' }}</b>
            </button>
            <button
              type="button"
              class="kfield"
              :class="{ on: pDraft.field === 'deduct', muted: pDraft.deductMode === 'none' }"
              @click="focusDeduct"
            >
              <span>扣杂</span>
              <b v-if="pDraft.deductMode === 'none'">不扣</b>
              <b v-else-if="pDraft.deductMode === 'ratio'" class="mono">{{ pDraft.ratio || '0' }}<i>%</i></b>
              <b v-else class="mono">{{ pDraft.fixed || '0' }}<i>吨</i></b>
            </button>
          </div>

          <div class="drow">
            <button
              type="button"
              class="dbtn"
              :class="{ on: pDraft.deductMode === 'none' }"
              @click="setDeduct('none')"
            >不扣杂</button>
            <button
              type="button"
              class="dbtn"
              :class="{ on: pDraft.deductMode === 'ratio' }"
              @click="setDeduct('ratio')"
            >按比例扣重</button>
            <button
              type="button"
              class="dbtn"
              :class="{ on: pDraft.deductMode === 'fixed' }"
              @click="setDeduct('fixed')"
            >固定扣重</button>
            <button
              v-if="defaultPrice"
              type="button"
              class="dbtn dbtn--quick"
              @click="pDraft.price = String(defaultPrice)"
            >默认价 ¥{{ defaultPrice }}</button>
          </div>

          <div class="calc">
            <div><span>净重</span><b class="mono">{{ w2(priceNet) }}</b></div>
            <div><span>扣杂</span><b class="mono text-warning">{{ w2(previewDeduct) }}</b></div>
            <div><span>结算净重</span><b class="mono text-cyan">{{ w2(estimateSettle) }}</b></div>
            <div class="calc__amt">
              <span>预估金额{{ priceNetUnknown ? '（皮重未称）' : '' }}</span>
              <b class="text-success">¥ {{ money(previewAmount) }}</b>
            </div>
          </div>

          <div class="kpad">
            <TouchKeypad
              v-model="activeLiteral"
              :mode="pDraft.field === 'price' ? 'int' : 'decimal'"
              :max-int="7"
              confirm-text="确认核价"
              @confirm="submitPrice"
            />
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost" @click="abandonPrice">返回本车</button>
          </footer>
        </section>

        <!-- ⑥ 录皮重 -->
        <section v-else-if="panel === 'tare' && tareItem" class="pane pane--pad">
          <header class="pad__head">
            <div class="pad__title">
              <h2>录入皮重 · {{ tareItem.material_name }}</h2>
              <p>毛重 {{ w2(tareItem.start_weight) }} 吨 · {{ tareItem.ticket_no }}</p>
            </div>
            <div class="basis basis--single">
              <span>单价</span>
              <b class="mono">¥{{ Number(tareItem.unit_price || 0).toFixed(2) }}</b>
            </div>
          </header>

          <div class="screen">
            <span class="screen__label">皮重读数</span>
            <div class="screen__value mono">{{ tDraft.value || '0' }}<em>吨</em></div>
            <span class="screen__hint">车辆回空后称重，确认即完成本批</span>
          </div>

          <div class="calc">
            <div><span>净重</span><b class="mono text-cyan">{{ w2(tarePreview.net) }}</b></div>
            <div><span>扣杂</span><b class="mono text-warning">{{ w2(tarePreview.deduct) }}</b></div>
            <div><span>结算净重</span><b class="mono text-cyan">{{ w2(tarePreview.settle) }}</b></div>
            <div class="calc__amt">
              <span>本批金额</span>
              <b class="text-success">¥ {{ money(tarePreview.settle * Number(tareItem.unit_price || 0)) }}</b>
            </div>
          </div>

          <div class="kpad">
            <TouchKeypad
              v-model="tDraft.value"
              mode="decimal"
              :max-int="3"
              confirm-text="确认完成"
              @confirm="submitTare"
            />
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost" @click="panel = 'trip'">返回本车</button>
          </footer>
        </section>

        <!-- ⑦ 完成结果 -->
        <section v-else-if="panel === 'receipt' && lastResult" class="pane pane--receipt">
          <div class="ok">
            <div class="ok__ring"><el-icon><Check /></el-icon></div>
            <h2>本批称重完成</h2>
            <p>{{ lastResult.material_name }} · {{ lastResult.ticket_no }}</p>
          </div>

          <div class="rgrid">
            <div><span>毛重</span><b class="mono">{{ w2(lastResult.start_weight) }}</b><em>吨</em></div>
            <div><span>皮重</span><b class="mono">{{ w2(lastResult.end_weight) }}</b><em>吨</em></div>
            <div><span>净重</span><b class="mono">{{ w2(lastResult.net_weight) }}</b><em>吨</em></div>
            <div><span>扣杂</span><b class="mono text-warning">{{ w2(lastResult.deduct_weight) }}</b><em>吨</em></div>
            <div class="rgrid__hi"><span>结算净重</span><b class="mono text-cyan">{{ w2(lastResult.settle_weight) }}</b><em>吨</em></div>
            <div class="rgrid__hi">
              <span>金额</span>
              <b class="text-success">¥ {{ money(receiptAmount) }}</b>
            </div>
          </div>

          <div class="rtotal">
            本车已完成 <b>{{ finished.length }}</b> 批 · 净重 <b class="text-cyan">{{ w2(tripWeight) }}</b> 吨 ·
            合计 <b class="text-success">¥ {{ money(tripAmount) }}</b>
          </div>

          <footer class="pane__foot">
            <button class="big big--ghost" @click="panel = 'trip'">返回本车</button>
            <button class="big big--primary" @click="startAdd">继续加货</button>
          </footer>
        </section>

        <!-- 空态 -->
        <section v-else class="pane pane--empty">
          <el-icon class="empty__ico"><Van /></el-icon>
          <h2>当前没有在场车辆</h2>
          <p>点击左侧「新车辆」登记来车，开单后即可开始过磅</p>
          <button class="big big--primary" @click="openNewTrip">登记来车</button>
        </section>
      </main>
    </div>

    <!-- 手机号键盘 -->
    <TouchSheet
      v-model="phoneSheet.open"
      title="手机号"
      :subtitle="phoneSheet.intent === 'new' ? '输入手机号即可登记新客户' : '输入手机号查找客户'"
    >
      <div class="sheet-screen mono">{{ phoneSheet.value || '输入 11 位手机号' }}</div>
      <div class="kpad kpad--sheet">
        <TouchKeypad
          v-model="phoneSheet.value"
          mode="phone"
          confirm-text="查找客户"
          @confirm="doFindCustomer"
        />
      </div>
      <template #footer>
        <button class="big big--ghost" @click="phoneSheet.open = false">关闭</button>
        <button class="big big--soft" @click="registerAsNew">登记为新客户</button>
      </template>
    </TouchSheet>

    <!-- 车牌键盘 -->
    <TouchSheet v-model="plateSheet.open" title="车牌号" subtitle="先点省份，再输入字母与数字" size="wide">
      <div class="provs">
        <button
          v-for="p in PROVINCES"
          :key="p"
          type="button"
          class="prov"
          :class="{ on: plateSheet.value.startsWith(p) }"
          @click="pickProvince(p)"
        >{{ p }}</button>
      </div>
      <div class="sheet-screen mono">{{ plateSheet.value || '粤B12345' }}</div>
      <div class="kpad kpad--sheet">
        <TouchKeypad v-model="plateSheet.value" mode="plate" confirm-text="确定" @confirm="confirmPlate" />
      </div>
      <template #footer>
        <button class="big big--ghost" @click="plateSheet.open = false">取消</button>
        <button class="big big--soft" @click="plateSheet.value = ''">清空</button>
      </template>
    </TouchSheet>

    <!-- 确认框 -->
    <TouchSheet v-model="confirmBox.open" :title="confirmBox.title" :subtitle="confirmBox.text">
      <div class="confirm-actions">
        <button class="big big--ghost" @click="confirmBox.open = false">先不处理</button>
        <button class="big big--danger" @click="runConfirm">确认执行</button>
      </div>
    </TouchSheet>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { basicApi, weighApi } from '../api'
import { itemStatus, money } from '../utils/status'
import TouchKeypad from '../components/touch/TouchKeypad.vue'
import TouchSheet from '../components/touch/TouchSheet.vue'

const router = useRouter()
const POLL_INTERVAL = 15000
const PROVINCES = [
  '京', '津', '沪', '渝', '冀', '豫', '云', '辽', '黑', '湘', '皖', '鲁', '新', '苏', '浙', '赣',
  '鄂', '桂', '甘', '晋', '蒙', '陕', '吉', '闽', '贵', '粤', '青', '藏', '川', '宁', '琼'
]

/* ---------------- 基础数据 ---------------- */
const stations = ref([])
const materials = ref([])
const customers = ref([])
const tickets = ref([])
const maxActive = ref(12)
const stationId = ref(null)

const stationName = computed(
  () => stations.value.find((s) => s.station_id === stationId.value)?.station_name || '本站点'
)

/* ---------------- 当前车辆 ---------------- */
const tripId = ref(null)
const detail = ref(null)
const panel = ref('newTrip')
const busy = ref(false)

const trip = computed(() => detail.value?.trip || null)
const items = computed(() => detail.value?.items || [])
const readings = computed(() => detail.value?.readings || [])
const liveItems = computed(() => items.value.filter((i) => i.status !== 4))
const pendingPrice = computed(() => liveItems.value.filter((i) => i.status === 0))
const needTare = computed(() => liveItems.value.filter((i) => i.status === 1 && i.weigh_mode === 1))
const finished = computed(() => liveItems.value.filter((i) => i.status === 2 || i.status === 3))
const tripWeight = computed(() =>
  round2(finished.value.reduce((n, i) => n + Number(i.settle_weight || 0), 0))
)
const tripAmount = computed(() =>
  round2(
    finished.value.reduce(
      (n, i) => n + Number(i.settle_weight || 0) * Number(i.unit_price || 0),
      0
    )
  )
)

const totalPending = computed(() => tickets.value.reduce((n, t) => n + t.pending_price, 0))
const totalTare = computed(() =>
  tickets.value.reduce((n, t) => n + Math.max(t.priced - t.completed - t.settled, 0), 0)
)
const totalDoneWeight = computed(() =>
  round2(tickets.value.reduce((n, t) => n + Number(t.total_settle_weight || 0), 0))
)

/* ---------------- 登记来车 ---------------- */
const newTrip = reactive({
  biz_type: 1,
  customer_id: null,
  customer_name: '',
  customer_phone: '',
  plate_no: ''
})
const customerKeyword = ref('')

const visibleCustomers = computed(() => {
  const kw = customerKeyword.value.trim()
  if (!kw) return customers.value
  return customers.value.filter(
    (c) => (c.phone || '').includes(kw) || (c.customer_name || '').includes(kw)
  )
})

const canCreate = computed(
  () => Boolean(newTrip.customer_id || newTrip.customer_name) && Boolean(stationId.value)
)

/* ---------------- 加货草稿 ---------------- */
const wDraft = reactive({ material_id: null, weigh_mode: 1, value: '', reuse: false })
const pDraft = reactive({
  price: '',
  deductMode: 'none',
  ratio: '',
  fixed: '',
  calc_base: 2,
  field: 'price'
})
const tDraft = reactive({ value: '' })

const priceItem = ref(null)
const tareItem = ref(null)
const lastResult = ref(null)
const categoryFilter = ref('全部')

const selectedMaterial = computed(
  () => materials.value.find((m) => m.material_id === wDraft.material_id) || null
)
const defaultPrice = computed(() => {
  const p = Number(selectedMaterial.value?.default_price || 0)
  return p > 0 ? p.toFixed(0) : ''
})

const categories = computed(() => {
  const map = new Map()
  materials.value.forEach((m) => {
    const key = m.category_name || '未分类'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return [
    { name: '全部', count: materials.value.length },
    ...[...map.entries()].map(([name, count]) => ({ name, count }))
  ]
})

const filteredMaterials = computed(() => {
  if (categoryFilter.value === '全部') return materials.value
  return materials.value.filter((m) => (m.category_name || '未分类') === categoryFilter.value)
})

const reuseReading = computed(() => {
  const arr = [...items.value].reverse()
  const it = arr.find((i) => i.end_reading_id)
  if (!it) return null
  return readings.value.find((r) => r.reading_id === it.end_reading_id) || null
})
const canReuse = computed(() => wDraft.weigh_mode === 1 && Boolean(reuseReading.value))

/* ---------------- 核价测算 ---------------- */
const priceNet = computed(() => {
  const it = priceItem.value
  if (!it) return 0
  return it.net_weight != null ? Number(it.net_weight) : Number(it.start_weight || 0)
})
const priceNetUnknown = computed(() => priceItem.value?.net_weight == null)

const previewDeduct = computed(() => {
  const it = priceItem.value
  if (!it) return 0
  const gross = Number(it.start_weight || 0)
  const net = it.net_weight != null ? Number(it.net_weight) : null
  const base = pDraft.calc_base === 1 ? gross : net ?? gross
  let value = 0
  if (pDraft.deductMode === 'ratio') value = (base * Number(pDraft.ratio || 0)) / 100
  else if (pDraft.deductMode === 'fixed') value = Number(pDraft.fixed || 0)
  return Math.min(round2(value), base)
})

const estimateSettle = computed(() => Math.max(0, round2(priceNet.value - previewDeduct.value)))
const previewAmount = computed(() => round2(estimateSettle.value * Number(pDraft.price || 0)))

const activeLiteral = computed({
  get() {
    if (pDraft.field === 'price') return pDraft.price
    return pDraft.deductMode === 'fixed' ? pDraft.fixed : pDraft.ratio
  },
  set(v) {
    if (pDraft.field === 'price') pDraft.price = v
    else if (pDraft.deductMode === 'fixed') pDraft.fixed = v
    else pDraft.ratio = v
  }
})

/* ---------------- 皮重测算 ---------------- */
const tarePreview = computed(() => {
  const it = tareItem.value
  const tare = Number(tDraft.value || 0)
  if (!it || !tare) return { net: 0, deduct: 0, settle: 0 }
  const gross = Number(it.start_weight || 0)
  const net = Math.max(0, round2(gross - tare))
  const snap = it.deduct_rule_snapshot || {}
  const base = Number(snap.calc_base) === 1 ? gross : net
  let deduct = 0
  if (Number(snap.deduct_type) === 2) deduct = Number(snap.fixed_value || 0)
  else if (Number(snap.deduct_type) === 1) deduct = base * Number(snap.ratio || 0)
  deduct = Math.min(round2(deduct), net)
  return { net, deduct, settle: round2(net - deduct) }
})

const receiptAmount = computed(
  () => round2(Number(lastResult.value?.settle_weight || 0) * Number(lastResult.value?.unit_price || 0))
)

/* ---------------- 提示条 / 时钟 ---------------- */
const banner = reactive({ show: false, text: '', type: 'ok' })
let bannerTimer = null
function flash(text, type = 'ok') {
  banner.text = text
  banner.type = type
  banner.show = true
  clearTimeout(bannerTimer)
  bannerTimer = setTimeout(() => (banner.show = false), 2400)
}

const clock = reactive({ time: '--:--:--', date: '' })
let clockTimer = null
function tickClock() {
  const now = new Date()
  clock.time = now.toLocaleTimeString('zh-CN', { hour12: false })
  clock.date = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short'
  })
}

/* ---------------- 弹窗 ---------------- */
const phoneSheet = reactive({ open: false, value: '', intent: 'search' })
const plateSheet = reactive({ open: false, value: '' })
const confirmBox = reactive({ open: false, title: '', text: '', run: null })

function askConfirm(title, text, run) {
  confirmBox.title = title
  confirmBox.text = text
  confirmBox.run = run
  confirmBox.open = true
}
function runConfirm() {
  const fn = confirmBox.run
  confirmBox.open = false
  confirmBox.run = null
  fn?.()
}

/* ---------------- 工具 ---------------- */
function round2(v) {
  return Math.round((Number(v) || 0) * 100) / 100
}
function w2(v) {
  if (v === null || v === undefined || v === '') return '--'
  return Number(v).toFixed(2)
}
function elapsedText(min) {
  const m = Number(min || 0)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m} 分`
  return `${Math.floor(m / 60)} 时 ${m % 60} 分`
}
function ctaText(it) {
  if (it.status === 0) return '核价 ›'
  if (it.status === 1) return it.weigh_mode === 1 ? '称皮重 ›' : '完成称重 ›'
  if (it.status === 2) return '待结算'
  if (it.status === 3) return '已结算'
  return '已作废'
}

/* ---------------- 加载 ---------------- */
async function loadRefs() {
  const [st, mt, cs] = await Promise.all([
    basicApi.stations(),
    basicApi.materials({ status: 1 }),
    basicApi.searchCustomers({})
  ])
  stations.value = st || []
  materials.value = mt || []
  customers.value = cs || []
  if (!stationId.value && stations.value.length) stationId.value = stations.value[0].station_id
}

async function refreshTickets() {
  const data = await weighApi.activeTrips()
  tickets.value = data.trips || []
  maxActive.value = data.max_active || 12

  if (tripId.value && !tickets.value.some((t) => t.trip_id === tripId.value)) {
    tripId.value = null
    detail.value = null
    if (panel.value !== 'newTrip') {
      panel.value = 'newTrip'
      flash('本车已离场（结算或作废），请登记下一辆车', 'info')
    }
  }
}

async function refreshDetail() {
  if (!tripId.value) return
  detail.value = await weighApi.tripDetail(tripId.value)
}

async function selectTrip(t) {
  if (busy.value) return
  tripId.value = t.trip_id
  panel.value = 'trip'
  try {
    await refreshDetail()
  } catch {
    /* 错误提示已由请求层统一处理 */
  }
}

/* ---------------- 登记来车 ---------------- */
function openNewTrip() {
  if (tickets.value.length >= maxActive.value) {
    return flash(`在场车辆已达上限 ${maxActive.value} 辆，请先完成部分工单`, 'warn')
  }
  newTrip.biz_type = trip.value?.biz_type || 1
  newTrip.customer_id = null
  newTrip.customer_name = ''
  newTrip.customer_phone = ''
  newTrip.plate_no = ''
  customerKeyword.value = ''
  panel.value = 'newTrip'
}

function cancelNewTrip() {
  panel.value = tripId.value ? 'trip' : 'newTrip'
}

function pickCustomer(c) {
  newTrip.customer_id = c.customer_id
  newTrip.customer_name = c.customer_name
  newTrip.customer_phone = c.phone || ''
}

function openPhoneSheet(intent = 'search') {
  phoneSheet.value = ''
  phoneSheet.intent = intent
  phoneSheet.open = true
}

async function doFindCustomer() {
  const phone = (phoneSheet.value || '').trim()
  if (phone.length < 4) return flash('请至少输入手机号后 4 位', 'warn')
  customerKeyword.value = phone
  const hit = customers.value.filter((c) => (c.phone || '').includes(phone))
  if (hit.length) {
    phoneSheet.open = false
    if (hit.length === 1) pickCustomer(hit[0])
    flash(hit.length === 1 ? `已选中 ${hit[0].customer_name}` : `找到 ${hit.length} 位客户，请点选`)
  } else {
    flash('没有匹配的客户，可点「登记为新客户」', 'warn')
  }
}

function registerAsNew() {
  const phone = (phoneSheet.value || '').trim()
  if (phone.length < 7) return flash('请先输入完整手机号，再登记新客户', 'warn')
  const name = `散客${phone.slice(-4)}`
  newTrip.customer_id = null
  newTrip.customer_name = name
  newTrip.customer_phone = phone
  customerKeyword.value = ''
  phoneSheet.open = false
  flash(`已登记 ${name}，可继续输入车牌`)
}

function openPlateSheet() {
  plateSheet.value = newTrip.plate_no || '粤'
  plateSheet.open = true
}
function pickProvince(p) {
  const rest = PROVINCES.includes(plateSheet.value[0]) ? plateSheet.value.slice(1) : plateSheet.value
  plateSheet.value = (p + rest).slice(0, 8)
}
function confirmPlate() {
  newTrip.plate_no = (plateSheet.value || '').toUpperCase()
  plateSheet.open = false
}

async function doCreateTrip() {
  if (!canCreate.value || busy.value) return
  busy.value = true
  try {
    const data = await weighApi.createTrip({
      station_id: stationId.value,
      biz_type: newTrip.biz_type,
      customer_id: newTrip.customer_id || null,
      customer_name: newTrip.customer_id ? null : newTrip.customer_name,
      customer_phone: newTrip.customer_id ? null : newTrip.customer_phone || null,
      plate_no: newTrip.plate_no || null
    })
    detail.value = data
    tripId.value = data.trip.trip_id
    await refreshTickets()
    startAdd()
    flash(`已开单 ${data.trip.trip_no}`)
  } catch {
    /* 统一错误提示 */
  } finally {
    busy.value = false
  }
}

/* ---------------- 加货 ---------------- */
function startAdd() {
  wDraft.material_id = null
  wDraft.weigh_mode = 1
  wDraft.value = ''
  wDraft.reuse = false
  categoryFilter.value = '全部'
  panel.value = 'material'
}

function pickMaterial(m) {
  wDraft.material_id = m.material_id
  wDraft.value = ''
  wDraft.reuse = false
  panel.value = 'weight'
}

function setWeighMode(mode) {
  wDraft.weigh_mode = mode
  if (mode === 2) wDraft.reuse = false
}

async function submitWeight() {
  if (!trip.value) return
  if (!wDraft.material_id) return flash('请先选择物料', 'warn')
  if (!wDraft.reuse && !(Number(wDraft.value) > 0)) return flash('请输入地磅读数', 'warn')
  if (wDraft.reuse && !reuseReading.value) return flash('没有可沿用的上件皮重读数', 'warn')

  busy.value = true
  try {
    const data = await weighApi.addItem(trip.value.trip_id, {
      material_id: wDraft.material_id,
      weight: wDraft.reuse ? null : Number(wDraft.value),
      weigh_mode: wDraft.weigh_mode,
      reuse_reading_id: wDraft.reuse ? reuseReading.value.reading_id : null
    })
    detail.value = data
    const added = data.items[data.items.length - 1]
    openPrice(added)
    await refreshTickets()
  } catch {
    /* 统一错误提示 */
  } finally {
    busy.value = false
  }
}

/* ---------------- 核价 ---------------- */
function openPrice(it) {
  priceItem.value = it
  const m = materials.value.find((x) => x.material_id === it.material_id)
  const p = Number(m?.default_price || 0)
  pDraft.price = p > 0 ? String(p) : ''
  pDraft.deductMode = 'none'
  pDraft.ratio = ''
  pDraft.fixed = ''
  pDraft.calc_base = 2
  pDraft.field = 'price'
  panel.value = 'price'
}

function setDeduct(mode) {
  pDraft.deductMode = mode
  pDraft.field = mode === 'none' ? 'price' : 'deduct'
  if (mode !== 'ratio') pDraft.ratio = ''
  if (mode !== 'fixed') pDraft.fixed = ''
}
function focusDeduct() {
  if (pDraft.deductMode === 'none') setDeduct('ratio')
  else pDraft.field = 'deduct'
}

function abandonPrice() {
  panel.value = 'trip'
}

async function submitPrice() {
  const it = priceItem.value
  if (!it) return
  if (!(Number(pDraft.price) > 0)) return flash('请输入单价', 'warn')
  if (pDraft.deductMode === 'ratio' && !(Number(pDraft.ratio) > 0)) {
    return flash('请输入扣重比例，例如 3 表示 3%', 'warn')
  }
  if (pDraft.deductMode === 'fixed' && !(Number(pDraft.fixed) > 0)) {
    return flash('请输入固定扣重吨数', 'warn')
  }

  const payload = {
    unit_price: Number(pDraft.price),
    price_type: 1,
    deduct_type: pDraft.deductMode === 'fixed' ? 2 : 1,
    calc_base: pDraft.calc_base
  }
  if (pDraft.deductMode === 'ratio') payload.deduct_ratio = Number(pDraft.ratio) / 100
  else if (pDraft.deductMode === 'fixed') payload.deduct_fixed = Number(pDraft.fixed)
  else payload.deduct_ratio = 0

  busy.value = true
  try {
    await weighApi.price(it.item_id, payload)

    if (it.weigh_mode === 2) {
      // 单次过磅：读数即净重，核价后可直接完成
      await weighApi.complete(it.item_id, { end_weight: null })
      await refreshDetail()
      lastResult.value = detail.value.items.find((x) => x.item_id === it.item_id) || it
      panel.value = 'receipt'
      flash('单次过磅已完成')
    } else {
      await refreshDetail()
      panel.value = 'trip'
      flash('已核价，待车辆回空后称皮重')
    }
    await refreshTickets()
  } catch {
    /* 统一错误提示 */
  } finally {
    busy.value = false
  }
}

/* ---------------- 皮重 ---------------- */
function openTare(it) {
  tareItem.value = it
  tDraft.value = ''
  panel.value = 'tare'
}

async function submitTare() {
  const it = tareItem.value
  if (!it) return
  const tare = Number(tDraft.value)
  if (!(tare > 0)) return flash('请输入皮重读数', 'warn')
  if (tare >= Number(it.start_weight)) return flash('皮重必须小于毛重', 'warn')

  busy.value = true
  try {
    await weighApi.complete(it.item_id, { end_weight: tare })
    await refreshDetail()
    lastResult.value = detail.value.items.find((x) => x.item_id === it.item_id) || it
    panel.value = 'receipt'
    await refreshTickets()
    flash('称重完成')
  } catch {
    /* 统一错误提示 */
  } finally {
    busy.value = false
  }
}

/* ---------------- 批次点击 / 作废 ---------------- */
function tapItem(it) {
  if (busy.value) return
  if (it.status === 0) return openPrice(it)
  if (it.status === 1) {
    if (it.weigh_mode === 1) return openTare(it)
    return askConfirm('完成称重', `批次 ${it.ticket_no} 为单次过磅，确认完成？`, async () => {
      busy.value = true
      try {
        await weighApi.complete(it.item_id, { end_weight: null })
        await refreshDetail()
        lastResult.value = detail.value.items.find((x) => x.item_id === it.item_id) || it
        panel.value = 'receipt'
        await refreshTickets()
      } finally {
        busy.value = false
      }
    })
  }
  if (it.status === 2) return flash('该批次已称重完成，等待财务结算', 'info')
  if (it.status === 3) return flash('该批次已结算', 'info')
  flash('该批次已作废', 'info')
}

function askCancelTrip() {
  if (!trip.value) return
  askConfirm(
    '作废整张工单',
    `仅当本车没有有效批次时才能作废。确认真要作废 ${trip.value.trip_no}？`,
    async () => {
      busy.value = true
      try {
        await weighApi.cancelTrip(trip.value.trip_id)
        flash('工单已作废')
        tripId.value = null
        detail.value = null
        await refreshTickets()
        panel.value = tickets.value.length ? 'trip' : 'newTrip'
        if (panel.value === 'trip') await selectTrip(tickets.value[0])
      } catch {
        /* 统一错误提示 */
      } finally {
        busy.value = false
      }
    }
  )
}

/* ---------------- 终端能力 ---------------- */
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen()
    else await document.documentElement.requestFullscreen()
  } catch {
    flash('当前浏览器不支持全屏', 'warn')
  }
}

function goBack() {
  router.push('/dashboard')
}

/* ---------------- 轮询 ---------------- */
let pollTimer = null
function startPoll() {
  stopPoll()
  pollTimer = setInterval(async () => {
    if (busy.value || phoneSheet.open || plateSheet.open || confirmBox.open) return
    if (panel.value !== 'trip') return
    try {
      await refreshTickets()
      if (tripId.value) await refreshDetail()
    } catch {
      /* 轮询失败静默 */
    }
  }, POLL_INTERVAL)
}
function stopPoll() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
}

onMounted(async () => {
  tickClock()
  clockTimer = setInterval(tickClock, 1000)
  try {
    await loadRefs()
    await refreshTickets()
    const first = tickets.value[0]
    if (first) await selectTrip(first)
    else panel.value = 'newTrip'
  } catch {
    panel.value = 'newTrip'
  }
  startPoll()
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
  clearTimeout(bannerTimer)
  stopPoll()
})
</script>

<style scoped>
.touch {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  user-select: none;
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
}

/* ---------------- 顶部状态条 ---------------- */
.bar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: clamp(12px, 1.4vw, 26px);
  height: clamp(64px, 7vh, 84px);
  padding: 0 clamp(12px, 1.2vw, 22px);
  border-bottom: 1px solid rgba(64, 153, 255, 0.16);
  background: linear-gradient(180deg, rgba(9, 28, 54, 0.92), rgba(4, 14, 28, 0.72));
  backdrop-filter: blur(14px);
  z-index: 6;
}
.bar__brand { display: flex; align-items: center; gap: 12px; }
.bar__mark {
  width: clamp(38px, 3.2vw, 46px);
  height: clamp(38px, 3.2vw, 46px);
  display: grid;
  place-items: center;
  border-radius: 13px;
  color: #fff;
  font-size: clamp(18px, 1.5vw, 22px);
  background: linear-gradient(145deg, #2f7bff, #12c9f5);
  box-shadow: 0 0 26px rgba(47, 123, 255, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.bar__name { display: flex; flex-direction: column; line-height: 1.2; }
.bar__name b { font-size: clamp(15px, 1.25vw, 19px); letter-spacing: 2px; color: #eaf4ff; }
.bar__name span { font-size: clamp(8px, 0.6vw, 10px); letter-spacing: 2.4px; color: #5b86b8; margin-top: 3px; }

.bar__stats { display: flex; align-items: center; gap: clamp(14px, 2vw, 38px); margin-left: clamp(4px, 1vw, 20px); }
.stat { display: flex; align-items: baseline; gap: 6px; }
.stat span { font-size: clamp(11px, 0.85vw, 13px); color: #6f8bb0; letter-spacing: 0.5px; }
.stat b { font-size: clamp(17px, 1.5vw, 23px); font-family: 'JetBrains Mono', Consolas, monospace; color: #dbeafe; }
.stat em { font-style: normal; font-size: 11px; color: #5f7f9f; }

.bar__right { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.bar__clock { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.2; margin-right: 6px; }
.bar__clock b { font-size: clamp(16px, 1.4vw, 21px); font-family: 'JetBrains Mono', Consolas, monospace; color: #bfe4ff; letter-spacing: 1px; }
.bar__clock span { font-size: clamp(9px, 0.7vw, 11px); color: #56759a; }
.bar__icon {
  width: clamp(46px, 3.8vw, 56px);
  height: clamp(46px, 3.8vw, 56px);
  display: grid;
  place-items: center;
  border-radius: 13px;
  cursor: pointer;
  font-size: clamp(18px, 1.5vw, 22px);
  color: #9dc0e8;
  background: rgba(16, 40, 72, 0.7);
  border: 1px solid rgba(79, 155, 255, 0.24);
}
.bar__icon:active { transform: scale(0.95); color: #4fd8ff; }

/* ---------------- 操作结果提示 ---------------- */
.banner {
  position: fixed;
  top: clamp(6px, 0.9vh, 12px);
  left: 50%;
  transform: translateX(-50%);
  z-index: 400;
  padding: 11px 34px;
  border-radius: 40px;
  font-size: clamp(15px, 1.2vw, 19px);
  letter-spacing: 1px;
  color: #f2f9ff;
  background: rgba(8, 28, 55, 0.97);
  border: 1px solid rgba(79, 155, 255, 0.5);
  box-shadow: 0 14px 44px rgba(0, 0, 0, 0.6);
  pointer-events: none;
}
.banner--ok { border-color: rgba(34, 224, 161, 0.75); box-shadow: 0 0 30px rgba(34, 224, 161, 0.3), 0 14px 44px rgba(0, 0, 0, 0.6); }
.banner--warn { border-color: rgba(255, 184, 77, 0.85); box-shadow: 0 0 30px rgba(255, 184, 77, 0.3), 0 14px 44px rgba(0, 0, 0, 0.6); }
.banner--info { border-color: rgba(79, 155, 255, 0.7); }
.banner-enter-active, .banner-leave-active { transition: all 0.2s ease; }
.banner-enter-from, .banner-leave-to { opacity: 0; transform: translate(-50%, -8px); }

/* ---------------- 主体 ---------------- */
.body {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: clamp(196px, 15vw, 268px) minmax(0, 1fr);
  gap: clamp(10px, 0.9vw, 16px);
  padding: clamp(10px, 0.9vw, 16px);
}

/* 左：在场车辆 */
.lane {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 16px;
  padding: 12px;
  background: linear-gradient(170deg, rgba(12, 32, 60, 0.8), rgba(6, 16, 32, 0.7));
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.lane__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 4px 10px;
  font-size: clamp(12px, 0.95vw, 14px);
  color: #8fb0d4;
  letter-spacing: 1px;
}
.lane__head b { font-family: 'JetBrains Mono', Consolas, monospace; font-size: clamp(14px, 1.1vw, 17px); color: var(--cyan); }
.lane__head b em { font-style: normal; font-size: 11px; color: #5f7f9f; }
.lane__list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 2px;
}

.vcard {
  position: relative;
  flex: 0 0 auto;
  text-align: left;
  padding: 12px 12px 10px;
  border-radius: 14px;
  cursor: pointer;
  color: inherit;
  font-family: inherit;
  background: linear-gradient(155deg, rgba(15, 40, 74, 0.9), rgba(7, 20, 38, 0.86));
  border: 1px solid rgba(70, 150, 255, 0.18);
  transition: transform 0.1s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}
.vcard:active { transform: scale(0.985); }
.vcard.is-active {
  border-color: rgba(31, 209, 249, 0.65);
  background: linear-gradient(155deg, rgba(22, 62, 112, 0.95), rgba(9, 28, 54, 0.92));
  box-shadow: 0 0 0 1px rgba(31, 209, 249, 0.3), 0 10px 30px rgba(31, 129, 255, 0.3);
}
.vcard__top { display: flex; align-items: center; gap: 8px; }
.vcard__plate {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(15px, 1.2vw, 18px);
  letter-spacing: 1px;
  color: #eaf4ff;
}
.tag {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 10.5px;
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.tag--warn { color: #1a1000; background: rgba(255, 184, 77, 0.92); }
.tag--done { color: #03140e; background: rgba(34, 224, 161, 0.9); }
.tag--run { color: #cfe2fa; background: rgba(47, 123, 255, 0.35); }
.vcard__name {
  margin-top: 5px;
  font-size: clamp(12px, 0.95vw, 14px);
  color: var(--text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vcard__bar { height: 3px; margin-top: 9px; border-radius: 3px; background: rgba(60, 120, 200, 0.24); overflow: hidden; }
.vcard__bar i { display: block; height: 100%; border-radius: 3px; background: linear-gradient(90deg, var(--brand), var(--cyan)); box-shadow: 0 0 8px rgba(31, 209, 249, 0.6); }
.vcard__foot { display: flex; justify-content: space-between; gap: 6px; margin-top: 6px; font-size: 10.5px; color: #6f8bb0; }
.vcard__foot em { font-style: normal; color: #56759a; }

.vcard--new {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 96px;
  border-style: dashed;
  color: #7f9ec2;
  text-align: center;
}
.vcard--new b { font-size: clamp(13px, 1.05vw, 15px); color: var(--brand-light); }
.vcard--new span { font-size: 10.5px; color: #5f7f9f; }
.vcard--new .el-icon { font-size: 22px; color: var(--brand-light); }
.vcard--new:disabled { opacity: 0.4; }

/* ---------------- 操作台 ---------------- */
.stage { min-height: 0; display: flex; }
.pane {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: clamp(10px, 0.9vw, 14px);
  padding: clamp(14px, 1.2vw, 20px);
  border-radius: 18px;
  background: linear-gradient(160deg, rgba(13, 36, 68, 0.82), rgba(6, 17, 34, 0.76));
  border: 1px solid rgba(70, 150, 255, 0.18);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(120, 190, 255, 0.08);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.pane__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.pane__head h2 { margin: 0; font-size: clamp(19px, 1.55vw, 25px); letter-spacing: 1px; color: var(--text-1); }
.pane__head p { margin: 5px 0 0; font-size: clamp(11px, 0.9vw, 13.5px); color: var(--text-3); }
.pane__badge {
  padding: 7px 16px;
  border-radius: 30px;
  font-size: clamp(11px, 0.85vw, 13px);
  color: #9fe3ff;
  background: rgba(31, 129, 255, 0.12);
  border: 1px solid rgba(79, 155, 255, 0.32);
}

/* 登记来车 */
.fld { display: flex; flex-direction: column; gap: 10px; }
.fld--grow { flex: 1; min-height: 0; }
.fld__label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: clamp(11.5px, 0.95vw, 14px);
  letter-spacing: 1px;
  color: #8fb0d4;
}
.fld__label em { font-style: normal; color: var(--cyan); font-size: clamp(12px, 1vw, 15px); }
.fld__reset {
  margin-left: auto;
  padding: 4px 12px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 11.5px;
  color: #9dc0e8;
  background: rgba(31, 129, 255, 0.14);
  border: 1px solid rgba(79, 155, 255, 0.3);
}

.pick2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pick {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 18px;
  text-align: left;
  border-radius: 14px;
  cursor: pointer;
  color: var(--text-2);
  font-family: inherit;
  background: linear-gradient(160deg, rgba(18, 44, 80, 0.85), rgba(8, 22, 42, 0.8));
  border: 1px solid rgba(70, 150, 255, 0.2);
  transition: all 0.14s ease;
}
.pick b { font-size: clamp(17px, 1.4vw, 22px); letter-spacing: 2px; color: var(--text-1); }
.pick span { font-size: clamp(11px, 0.85vw, 13px); color: #6f8bb0; }
.pick.on {
  border-color: rgba(31, 209, 249, 0.7);
  background: linear-gradient(160deg, rgba(28, 80, 140, 0.95), rgba(12, 36, 68, 0.92));
  box-shadow: 0 0 0 1px rgba(31, 209, 249, 0.28), 0 10px 26px rgba(31, 129, 255, 0.28);
}
.pick.on b { color: #fff; }

.cust-grid {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
  align-content: start;
  padding: 2px;
}
.cust {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-height: 72px;
  padding: 12px 14px;
  text-align: left;
  border-radius: 13px;
  cursor: pointer;
  color: inherit;
  font-family: inherit;
  background: linear-gradient(160deg, rgba(17, 42, 76, 0.9), rgba(8, 22, 42, 0.85));
  border: 1px solid rgba(70, 150, 255, 0.18);
  transition: all 0.12s ease;
}
.cust:active { transform: scale(0.98); }
.cust b { font-size: clamp(14px, 1.1vw, 17px); color: var(--text-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cust span { font-size: clamp(10.5px, 0.8vw, 12px); color: #6f8bb0; font-family: 'JetBrains Mono', Consolas, monospace; }
.cust.on {
  border-color: rgba(31, 209, 249, 0.7);
  background: linear-gradient(160deg, rgba(28, 80, 140, 0.95), rgba(12, 36, 68, 0.92));
  box-shadow: 0 0 0 1px rgba(31, 209, 249, 0.3), 0 8px 24px rgba(31, 129, 255, 0.26);
}
.cust--act {
  align-items: flex-start;
  justify-content: center;
  border-style: dashed;
  color: var(--brand-light);
  border-color: rgba(79, 155, 255, 0.38);
}
.cust--act .el-icon { font-size: 20px; color: var(--brand-light); }
.cust--act b { color: var(--brand-light); }

.plate-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-radius: 14px;
  cursor: pointer;
  color: var(--text-1);
  font-family: inherit;
  background: linear-gradient(160deg, rgba(17, 42, 76, 0.8), rgba(8, 22, 42, 0.75));
  border: 1px dashed rgba(79, 155, 255, 0.42);
}
.plate-btn span { font-size: clamp(17px, 1.4vw, 22px); letter-spacing: 2px; }
.plate-btn em { font-style: normal; font-size: clamp(10.5px, 0.8vw, 12px); color: #6f8bb0; }

/* 本车工作台 */
.vhead {
  display: flex;
  align-items: center;
  gap: clamp(12px, 1.4vw, 24px);
  padding: 12px 16px;
  border-radius: 14px;
  background: linear-gradient(100deg, rgba(20, 54, 98, 0.75), rgba(8, 24, 46, 0.55));
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.vhead__plate {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(22px, 2vw, 38px);
  letter-spacing: 2px;
  color: #fff;
  text-shadow: 0 0 22px rgba(31, 209, 249, 0.45);
}
.vhead__meta { display: flex; flex-direction: column; gap: 3px; }
.vhead__meta b { font-size: clamp(14px, 1.1vw, 17px); color: var(--text-1); }
.vhead__meta span { font-size: clamp(10.5px, 0.8vw, 12px); color: #6f8bb0; }
.vhead__stats { margin-left: auto; display: flex; gap: clamp(14px, 1.6vw, 30px); }
.vhead__stats div { display: flex; flex-direction: column; gap: 2px; align-items: flex-end; }
.vhead__stats span { font-size: clamp(10px, 0.78vw, 12px); color: #6f8bb0; }
.vhead__stats b { font-family: 'JetBrains Mono', Consolas, monospace; font-size: clamp(16px, 1.35vw, 25px); color: var(--text-1); }

.ilist {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 2px;
}
.icard {
  display: grid;
  grid-template-columns: 46px minmax(0, 1.15fr) minmax(0, 2.3fr) 96px 112px;
  align-items: center;
  gap: clamp(8px, 0.9vw, 16px);
  flex: 0 0 auto;
  min-height: clamp(70px, 8.4vh, 92px);
  padding: 12px 16px;
  border-radius: 14px;
  cursor: pointer;
  text-align: left;
  color: inherit;
  font-family: inherit;
  background: linear-gradient(160deg, rgba(16, 42, 78, 0.85), rgba(8, 22, 42, 0.8));
  border: 1px solid rgba(70, 150, 255, 0.16);
  transition: all 0.12s ease;
}
.icard:active { transform: scale(0.995); }
.icard.is-act { border-color: rgba(79, 155, 255, 0.4); }
.icard.is-act:hover { border-color: rgba(31, 209, 249, 0.6); box-shadow: 0 8px 26px rgba(31, 129, 255, 0.2); }
.icard.s2, .icard.s3, .icard.s4 { opacity: 0.66; }
.icard__no {
  font-size: clamp(13px, 1.05vw, 16px);
  color: #5f86b8;
  text-align: center;
}
.icard__mat { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.icard__mat b {
  font-size: clamp(14px, 1.15vw, 21px);
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.icard__mat em { font-style: normal; font-size: 10px; color: #5f86b8; letter-spacing: -0.2px; }
.icard__nums { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 6px; }
.icard__nums i { display: flex; flex-direction: column; gap: 2px; font-style: normal; }
.icard__nums em { font-style: normal; font-size: clamp(9.5px, 0.75vw, 11px); color: #6f8bb0; }
.icard__nums b {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(13px, 1.05vw, 19px);
  color: var(--text-2);
}
.icard__nums b.dim { color: #46607f; }
.icard__state {
  justify-self: center;
  padding: 5px 12px;
  border-radius: 20px;
  font-size: clamp(10.5px, 0.8vw, 12px);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
.icard__state.t0 { color: #cfe2fa; background: rgba(47, 123, 255, 0.3); }
.icard__state.t1 { color: #1a1000; background: rgba(255, 184, 77, 0.92); }
.icard__state.t2 { color: #03140e; background: rgba(34, 224, 161, 0.9); }
.icard__state.t3 { color: #03140e; background: rgba(34, 224, 161, 0.7); }
.icard__state.t4 { color: #ffd7de; background: rgba(255, 92, 122, 0.35); }
.icard__cta {
  justify-self: end;
  padding: 9px 16px;
  border-radius: 10px;
  font-size: clamp(12px, 0.95vw, 14px);
  white-space: nowrap;
  color: #fff;
  background: linear-gradient(96deg, rgba(47, 123, 255, 0.9), rgba(31, 168, 249, 0.9));
  box-shadow: 0 6px 18px rgba(47, 123, 255, 0.3);
}
.icard__cta.idle { color: #6f8bb0; background: rgba(70, 110, 160, 0.18); box-shadow: none; }

/* 物料选择 */
.chips { display: flex; gap: 10px; overflow-x: auto; padding: 2px 2px 8px; flex: 0 0 auto; }
.chipbtn {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 18px;
  border-radius: 30px;
  cursor: pointer;
  font-family: inherit;
  font-size: clamp(12px, 0.95vw, 14.5px);
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.7);
  border: 1px solid rgba(70, 150, 255, 0.2);
  white-space: nowrap;
}
.chipbtn em { font-style: normal; font-size: 10.5px; color: #5f7f9f; }
.chipbtn.on {
  color: #06131f;
  background: linear-gradient(96deg, #4fd8ff, #2f7bff);
  border-color: transparent;
  box-shadow: 0 8px 22px rgba(47, 123, 255, 0.35);
}
.chipbtn.on em { color: rgba(6, 19, 31, 0.7); }

.mgrid {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(clamp(140px, 13vw, 190px), 1fr));
  gap: 12px;
  align-content: start;
  padding: 2px;
}
.mtile {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 6px;
  min-height: clamp(96px, 12vh, 128px);
  padding: 14px 16px;
  text-align: left;
  border-radius: 15px;
  cursor: pointer;
  color: inherit;
  font-family: inherit;
  background: linear-gradient(160deg, rgba(19, 48, 86, 0.9), rgba(8, 24, 44, 0.85));
  border: 1px solid rgba(70, 150, 255, 0.18);
  transition: all 0.12s ease;
}
.mtile:active {
  transform: scale(0.98);
  border-color: rgba(31, 209, 249, 0.7);
  box-shadow: 0 0 0 1px rgba(31, 209, 249, 0.3), 0 12px 30px rgba(31, 129, 255, 0.28);
}
.mtile b {
  font-size: clamp(15px, 1.2vw, 22px);
  color: var(--text-1);
  line-height: 1.25;
}
.mtile__cat { font-size: clamp(10px, 0.78vw, 11.5px); color: #6f8bb0; }
.mtile__price {
  font-style: normal;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(15px, 1.15vw, 18px);
  color: var(--success);
}
.mtile__price i { font-style: normal; font-size: 10.5px; color: #5f7f9f; margin-left: 2px; }

/* 数字输入页 */
.pane--pad { gap: clamp(8px, 0.7vw, 12px); }
.pad__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.pad__title h2 { margin: 0; font-size: clamp(18px, 1.45vw, 23px); color: var(--text-1); letter-spacing: 0.5px; }
.pad__title p { margin: 5px 0 0; font-size: clamp(11px, 0.85vw, 13px); color: #6f8bb0; }

.modes { display: flex; gap: 10px; }
.modes button {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 9px 16px;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.7);
  border: 1px solid rgba(70, 150, 255, 0.2);
}
.modes button b { font-size: clamp(12.5px, 1vw, 15px); }
.modes button span { font-size: clamp(9.5px, 0.72vw, 11px); color: #5f7f9f; }
.modes button.on {
  color: #fff;
  background: linear-gradient(140deg, rgba(47, 123, 255, 0.85), rgba(20, 100, 180, 0.85));
  border-color: rgba(120, 210, 255, 0.55);
  box-shadow: 0 8px 24px rgba(47, 123, 255, 0.32);
}
.modes button.on span { color: rgba(255, 255, 255, 0.72); }

.screen {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: clamp(10px, 1.1vh, 18px);
  border-radius: 16px;
  background: radial-gradient(120% 160% at 50% 0%, rgba(31, 129, 255, 0.18), rgba(6, 18, 34, 0.9));
  border: 1px solid rgba(79, 155, 255, 0.32);
  box-shadow: inset 0 0 40px rgba(31, 129, 255, 0.12);
}
.screen__label { font-size: clamp(10.5px, 0.8vw, 12.5px); letter-spacing: 2px; color: #7f9ec2; }
.screen__value {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: clamp(44px, 5.2vw, 82px);
  font-weight: 700;
  line-height: 1.05;
  color: #ffffff;
  text-shadow: 0 0 36px rgba(31, 209, 249, 0.55);
}
.screen__value em { font-style: normal; font-size: clamp(15px, 1.2vw, 20px); color: #7f9ec2; text-shadow: none; }
.screen__hint { font-size: clamp(10px, 0.78vw, 12px); color: #5f7f9f; }
.screen.is-reuse { border-color: rgba(255, 184, 77, 0.5); box-shadow: inset 0 0 40px rgba(255, 184, 77, 0.12); }

.reuse {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 14px;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.6);
  border: 1px dashed rgba(79, 155, 255, 0.4);
}
.reuse__ico { font-size: 22px; color: var(--brand-light); }
.reuse__txt { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.reuse__txt b { font-size: clamp(12.5px, 1vw, 15px); color: var(--text-1); }
.reuse__txt em { font-style: normal; font-size: clamp(10px, 0.78vw, 12px); color: #6f8bb0; }
.reuse__state { margin-left: auto; font-size: clamp(11px, 0.85vw, 13px); color: #6f8bb0; white-space: nowrap; }
.reuse.on {
  border-style: solid;
  border-color: rgba(255, 184, 77, 0.7);
  background: rgba(255, 184, 77, 0.12);
}
.reuse.on .reuse__state { color: var(--warning); }

.kpad {
  flex: 1 1 auto;
  min-height: clamp(220px, 26vh, 320px);
  max-height: 540px;
}
.kpad.is-off { opacity: 0.42; }
/* 沿用读数时只禁用数字键，退格/确定仍可操作 */
.kpad.is-off :deep(.pad__keys) { pointer-events: none; }

/* 核价 */
.basis { display: flex; align-items: center; gap: 8px; }
.basis span { font-size: clamp(10.5px, 0.8vw, 12px); color: #6f8bb0; }
.basis button {
  padding: 10px 18px;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  font-size: clamp(12px, 0.95vw, 14px);
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.7);
  border: 1px solid rgba(70, 150, 255, 0.2);
}
.basis button.on {
  color: #06131f;
  background: linear-gradient(96deg, #4fd8ff, #2f7bff);
  border-color: transparent;
}
.basis--single b { font-size: clamp(15px, 1.2vw, 19px); color: var(--success); }

.fields { display: grid; grid-template-columns: 1.15fr 1fr; gap: 12px; }
.kfield {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 18px;
  border-radius: 14px;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  color: var(--text-2);
  background: linear-gradient(160deg, rgba(16, 42, 78, 0.85), rgba(8, 22, 42, 0.8));
  border: 1px solid rgba(70, 150, 255, 0.2);
}
.kfield span { font-size: clamp(10.5px, 0.8vw, 12px); color: #6f8bb0; }
.kfield b {
  font-size: clamp(26px, 2.4vw, 40px);
  font-weight: 700;
  color: #fff;
  text-shadow: 0 0 26px rgba(31, 209, 249, 0.4);
}
.kfield b i { font-style: normal; font-size: 15px; color: #7f9ec2; margin-left: 3px; }
.kfield.muted b { color: #7f9ec2; text-shadow: none; }
.kfield.on {
  border-color: rgba(31, 209, 249, 0.8);
  box-shadow: 0 0 0 1px rgba(31, 209, 249, 0.35), 0 0 30px rgba(31, 129, 255, 0.28);
  background: linear-gradient(160deg, rgba(28, 74, 128, 0.95), rgba(10, 30, 58, 0.9));
}

.drow { display: flex; gap: 10px; flex-wrap: wrap; }
.dbtn {
  flex: 1 1 0;
  min-width: 110px;
  padding: 12px 10px;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: clamp(12px, 0.95vw, 14.5px);
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.7);
  border: 1px solid rgba(70, 150, 255, 0.2);
  white-space: nowrap;
}
.dbtn.on {
  color: #fff;
  background: linear-gradient(140deg, rgba(47, 123, 255, 0.85), rgba(20, 100, 180, 0.85));
  border-color: rgba(120, 210, 255, 0.55);
}
.dbtn--quick { flex: 0 0 auto; color: var(--success); border-color: rgba(34, 224, 161, 0.4); }

.calc {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 16px;
  border-radius: 14px;
  background: linear-gradient(100deg, rgba(10, 30, 58, 0.85), rgba(6, 18, 36, 0.65));
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.calc div { display: flex; flex-direction: column; gap: 3px; }
.calc span { font-size: clamp(10px, 0.78vw, 12px); color: #6f8bb0; }
.calc b { font-family: 'JetBrains Mono', Consolas, monospace; font-size: clamp(16px, 1.35vw, 22px); color: var(--text-1); }
.calc__amt { align-items: flex-end; }
.calc__amt b { font-size: clamp(19px, 1.6vw, 26px); }

/* 完成结果 */
.pane--receipt { justify-content: center; align-items: center; gap: clamp(14px, 1.5vh, 24px); }
.pane--receipt .pane__foot { width: min(880px, 100%); }
.ok { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.ok__ring {
  width: clamp(64px, 6vw, 88px);
  height: clamp(64px, 6vw, 88px);
  display: grid;
  place-items: center;
  border-radius: 50%;
  font-size: clamp(30px, 2.8vw, 42px);
  color: #04140f;
  background: linear-gradient(145deg, #3cf0b4, #16c98d);
  box-shadow: 0 0 40px rgba(34, 224, 161, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.5);
  animation: pop 0.35s ease;
}
@keyframes pop {
  from { transform: scale(0.7); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.ok h2 { margin: 8px 0 0; font-size: clamp(22px, 1.9vw, 30px); letter-spacing: 2px; color: var(--text-1); }
.ok p { margin: 0; font-size: clamp(11.5px, 0.9vw, 13.5px); color: #6f8bb0; font-family: 'JetBrains Mono', Consolas, monospace; }

.rgrid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  width: min(880px, 100%);
}
.rgrid > div {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 14px 18px;
  border-radius: 14px;
  background: rgba(14, 36, 66, 0.75);
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.rgrid span { font-size: clamp(10.5px, 0.8vw, 12px); color: #6f8bb0; }
.rgrid b { margin-left: auto; font-size: clamp(20px, 1.75vw, 28px); color: var(--text-1); }
.rgrid em { font-style: normal; font-size: 11px; color: #5f7f9f; }
.rgrid__hi { background: linear-gradient(160deg, rgba(24, 62, 108, 0.9), rgba(10, 28, 52, 0.8)); border-color: rgba(31, 209, 249, 0.35) !important; }

.rtotal { font-size: clamp(11.5px, 0.9vw, 13.5px); color: #7f9ec2; }
.rtotal b { font-family: 'JetBrains Mono', Consolas, monospace; color: var(--text-1); }

/* 空态 */
.pane--empty { justify-content: center; align-items: center; gap: 10px; text-align: center; }
.empty__ico { font-size: clamp(44px, 4vw, 64px); color: rgba(79, 155, 255, 0.5); }
.pane--empty h2 { margin: 0; font-size: clamp(19px, 1.5vw, 24px); color: var(--text-1); letter-spacing: 1px; }
.pane--empty p { margin: 0 0 8px; font-size: clamp(11.5px, 0.9vw, 13.5px); color: var(--text-3); }

.blank {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: clamp(30px, 6vh, 60px) 20px;
  color: #5f7f9f;
  font-size: 13px;
}
.blank b { font-size: clamp(14px, 1.1vw, 17px); color: var(--text-2); }
.blank .el-icon { font-size: 38px; color: rgba(79, 155, 255, 0.45); }
.blank--inline { grid-column: 1 / -1; padding: 20px; font-size: 12px; }

/* 底部大按钮 */
.pane__foot { flex: 0 0 auto; display: flex; gap: 12px; }
.big {
  flex: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: clamp(52px, 6vh, 66px);
  padding: 0 22px;
  border-radius: 14px;
  cursor: pointer;
  font-family: inherit;
  font-size: clamp(15px, 1.2vw, 22px);
  letter-spacing: 1.5px;
  white-space: nowrap;
  color: #eaf4ff;
  border: 1px solid rgba(79, 155, 255, 0.3);
  background: rgba(16, 40, 72, 0.8);
  transition: transform 0.1s ease, filter 0.12s ease;
  -webkit-tap-highlight-color: transparent;
}
.big:active { transform: scale(0.985); }
.big--primary {
  flex: 1.5;
  color: #fff;
  border-color: transparent;
  background: linear-gradient(96deg, #2f7bff, #12c0ef);
  box-shadow: 0 10px 30px rgba(47, 123, 255, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}
.big--primary:disabled { opacity: 0.4; box-shadow: none; cursor: not-allowed; }
.big--soft { color: #9fe3ff; background: rgba(31, 129, 255, 0.16); border-color: rgba(79, 155, 255, 0.4); }
.big--danger { color: #fff; border-color: transparent; background: linear-gradient(96deg, #ff5c7a, #e0304f); box-shadow: 0 10px 30px rgba(255, 92, 122, 0.32); }
.big--ghost-danger { flex: 0.8; color: #ff9fb0; border-color: rgba(255, 92, 122, 0.4); background: rgba(255, 92, 122, 0.1); }

/* 弹层内部 */
.sheet-screen {
  display: grid;
  place-items: center;
  padding: 14px;
  border-radius: 14px;
  font-size: clamp(30px, 3vw, 46px);
  letter-spacing: 6px;
  color: #fff;
  background: radial-gradient(120% 160% at 50% 0%, rgba(31, 129, 255, 0.2), rgba(6, 18, 34, 0.9));
  border: 1px solid rgba(79, 155, 255, 0.32);
  text-shadow: 0 0 30px rgba(31, 209, 249, 0.5);
}
.kpad--sheet { flex: 0 0 auto; height: clamp(300px, 34vh, 400px); }

.provs { display: flex; flex-wrap: wrap; gap: 6px; }
.prov {
  min-width: clamp(40px, 3.2vw, 50px);
  min-height: clamp(38px, 3.4vh, 46px);
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  font-size: clamp(14px, 1.1vw, 17px);
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.7);
  border: 1px solid rgba(70, 150, 255, 0.2);
}
.prov.on { color: #06131f; background: linear-gradient(96deg, #4fd8ff, #2f7bff); border-color: transparent; }

.confirm-actions { display: flex; gap: 12px; padding: 6px 0 4px; }
.confirm-actions .big { min-height: clamp(60px, 7vh, 76px); }
</style>
