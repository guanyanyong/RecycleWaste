<template>
  <el-dialog v-model="visible" title="质检核价" width="560px" destroy-on-close @open="init">
    <div class="target" v-if="item">
      <div>
        <span class="muted">磅单号</span>
        <b class="mono text-brand">{{ item.ticket_no }}</b>
      </div>
      <div>
        <span class="muted">物料</span>
        <b>{{ item.material_name }}</b>
      </div>
      <div>
        <span class="muted">毛重</span>
        <b class="num-glow">{{ weight(item.start_weight) }} 吨</b>
      </div>
      <div>
        <span class="muted">净重</span>
        <b class="num-glow">{{ item.net_weight == null ? '待皮重' : weight(item.net_weight) + ' 吨' }}</b>
      </div>
    </div>

    <el-form :model="form" label-width="96px" class="price-form">
      <el-form-item label="核价单价">
        <el-input-number v-model="form.unit_price" :min="0.01" :precision="2" :step="10" controls-position="right" style="width: 220px" />
        <span class="unit">元 / 吨</span>
      </el-form-item>

      <el-form-item label="价格类型">
        <el-radio-group v-model="form.price_type">
          <el-radio-button :value="1">固定价</el-radio-button>
          <el-radio-button :value="2">浮动价</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.price_type === 2" label="价格来源">
        <el-input v-model="form.price_source" placeholder="如：11-03 长江有色现货价" maxlength="50" />
      </el-form-item>

      <el-form-item label="扣重方式">
        <el-radio-group v-model="form.deduct_type">
          <el-radio-button :value="1">比例扣重</el-radio-button>
          <el-radio-button :value="2">固定扣重</el-radio-button>
          <el-radio-button :value="3">比例扣款</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item v-if="form.deduct_type !== 2" label="扣重比例">
        <el-input-number v-model="form.ratioPercent" :min="0" :max="30" :precision="2" :step="0.5" controls-position="right" style="width: 180px" />
        <span class="unit">%</span>
      </el-form-item>

      <el-form-item v-else label="固定扣重">
        <el-input-number v-model="form.deduct_fixed" :min="0" :max="50" :precision="2" :step="0.05" controls-position="right" style="width: 180px" />
        <span class="unit">吨</span>
      </el-form-item>

      <el-form-item label="计算基数">
        <el-radio-group v-model="form.calc_base">
          <el-radio :value="1">按毛重</el-radio>
          <el-radio :value="2">按净重</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <div class="preview">
      <div><span>计算基数</span><b>{{ weight(baseWeight) }} 吨</b></div>
      <div><span>预计扣重</span><b class="text-warning">{{ weight(deductWeight) }} 吨</b></div>
      <div><span>预计结算净重</span><b class="text-cyan">{{ weight(settleWeight) }} 吨</b></div>
      <div><span>预计金额</span><b class="text-success">¥ {{ money(amount) }}</b></div>
    </div>
    <p v-if="item && item.weigh_mode === 1" class="tip">
      提示：该批次为两次过磅，净重需录入皮重后确定，此处金额为按毛重预估，最终以称重完成时快照为准。
    </p>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">确认核价</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { weighApi } from '../api'
import { money, weight } from '../utils/status'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  item: { type: Object, default: null }
})
const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const loading = ref(false)
const form = reactive({
  unit_price: 0,
  price_type: 1,
  price_source: '',
  deduct_type: 1,
  ratioPercent: 2,
  deduct_fixed: 0,
  calc_base: 2
})

function init() {
  if (!props.item) return
  form.unit_price = Number(props.item.unit_price || 2000)
  form.price_type = 1
  form.price_source = ''
  form.deduct_type = 1
  form.ratioPercent = 2
  form.deduct_fixed = 0
  form.calc_base = 2
}

const baseWeight = computed(() => {
  if (!props.item) return 0
  const net = props.item.net_weight
  if (form.calc_base === 1) return Number(props.item.start_weight || 0)
  return Number(net == null ? props.item.start_weight : net)
})

const deductWeight = computed(() => {
  if (form.deduct_type === 3) return 0
  if (form.deduct_type === 2) return Number(form.deduct_fixed || 0)
  return Math.round(baseWeight.value * (Number(form.ratioPercent || 0) / 100) * 100) / 100
})

const settleWeight = computed(() => {
  const net = props.item?.net_weight == null ? baseWeight.value : Number(props.item.net_weight)
  return Math.max(0, Math.round((net - deductWeight.value) * 100) / 100)
})

const amount = computed(() => Math.round(settleWeight.value * Number(form.unit_price || 0) * 100) / 100)

async function submit() {
  if (!form.unit_price || form.unit_price <= 0) {
    ElMessage.warning('请填写有效单价')
    return
  }
  if (form.price_type === 2 && !form.price_source) {
    ElMessage.warning('浮动价必须填写价格来源')
    return
  }
  loading.value = true
  try {
    await weighApi.price(props.item.item_id, {
      unit_price: form.unit_price,
      price_type: form.price_type,
      price_source: form.price_type === 2 ? form.price_source : null,
      deduct_type: form.deduct_type,
      deduct_ratio: form.deduct_type === 2 ? null : Number(form.ratioPercent || 0) / 100,
      deduct_fixed: form.deduct_type === 2 ? form.deduct_fixed : null,
      calc_base: form.calc_base
    })
    ElMessage.success('核价完成')
    visible.value = false
    emit('success')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.target {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px 18px;
  padding: 12px 14px;
  margin-bottom: 16px;
  border-radius: 10px;
  background: rgba(31, 129, 255, 0.07);
  border: 1px solid rgba(70, 150, 255, 0.16);
}
.target div { display: flex; flex-direction: column; gap: 3px; }
.target span { font-size: 11px; }
.target b { font-size: 13px; color: #dbeafe; }

.price-form :deep(.el-form-item) { margin-bottom: 14px; }
.unit { margin-left: 8px; font-size: 12px; color: #6f8bb0; }

.preview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  background: linear-gradient(120deg, rgba(31, 129, 255, 0.1), rgba(31, 209, 249, 0.05));
  border: 1px solid rgba(70, 150, 255, 0.18);
}
.preview div { display: flex; flex-direction: column; gap: 4px; }
.preview span { font-size: 10.5px; color: #7f9ec2; }
.preview b { font-size: 14px; }

.tip { margin: 12px 0 0; font-size: 11.5px; line-height: 1.7; color: #7f9ec2; }
</style>
