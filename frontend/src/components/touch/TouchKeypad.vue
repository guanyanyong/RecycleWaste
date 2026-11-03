<template>
  <div class="pad" :class="`pad--${mode}`">
    <div class="pad__keys">
      <button
        v-for="k in keyList"
        :key="k.v"
        type="button"
        class="key"
        :class="{ 'key--wide': k.wide }"
        @click="onKey(k.v)"
      >
        {{ k.label }}
      </button>
    </div>

    <div class="pad__side">
      <button type="button" class="side side--del" @click="onKey('back')">
        <span>⌫</span>
        <em>退格</em>
      </button>
      <button type="button" class="side side--clear" @click="onKey('clear')">
        <span>AC</span>
        <em>清空</em>
      </button>
      <button
        type="button"
        class="side side--ok"
        :disabled="confirmDisabled"
        @click="onConfirm"
      >
        <span>✓</span>
        <em>{{ confirmText }}</em>
      </button>
    </div>
  </div>
</template>

<script setup>
/**
 * 触摸数字键盘：无物理键盘的现场终端使用。
 * mode = decimal | int | phone | plate
 */
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  mode: { type: String, default: 'decimal' },
  maxInt: { type: Number, default: 4 },
  maxDec: { type: Number, default: 2 },
  confirmText: { type: String, default: '确定' },
  confirmDisabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

// 内部缓冲，避免连续快速点击时读到尚未更新的 props
const inner = ref(props.modelValue || '')
watch(
  () => props.modelValue,
  (v) => {
    if ((v || '') !== inner.value) inner.value = v || ''
  }
)

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')
const DIGITS = '0123456789'.split('')

const keyList = computed(() => {
  if (props.mode === 'plate') {
    return [...LETTERS, ...DIGITS].map((v) => ({ v, label: v }))
  }
  if (props.mode === 'phone') {
    return [
      ...['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((v) => ({ v, label: v })),
      { v: '0', label: '0', wide: true }
    ]
  }
  const base = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
  const tail = props.mode === 'decimal' ? ['.', '0', '00'] : ['0', '00']
  return [...base, ...tail].map((v) => ({ v, label: v }))
})

function valid(next) {
  if (props.mode === 'decimal') {
    return new RegExp(`^\\d{0,${props.maxInt}}(\\.\\d{0,${props.maxDec}})?$`).test(next)
  }
  if (props.mode === 'phone') return /^\d{0,11}$/.test(next)
  if (props.mode === 'int') return /^\d{0,7}$/.test(next)
  if (props.mode === 'plate') return /^[\u4e00-\u9fa5]?[A-Z0-9]{0,7}$/.test(next)
  return true
}

function buzz() {
  try {
    navigator.vibrate?.(8)
  } catch {
    /* 部分终端不支持震动 */
  }
}

function onKey(key) {
  buzz()
  let v = inner.value || ''
  if (key === 'back') {
    inner.value = v.slice(0, -1)
  } else if (key === 'clear') {
    inner.value = ''
  } else {
    for (const ch of String(key)) {
      const next = v + ch
      if (valid(next)) v = next
      else break
    }
    inner.value = v
  }
  emit('update:modelValue', inner.value)
}

function onConfirm() {
  if (props.confirmDisabled) return
  buzz()
  emit('confirm')
}

defineExpose({ clear: () => { inner.value = ''; emit('update:modelValue', '') } })
</script>

<style scoped>
.pad {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(104px, 8.4vw, 138px);
  gap: clamp(8px, 0.7vw, 13px);
  height: 100%;
  user-select: none;
  -webkit-user-select: none;
  touch-action: manipulation;
}

.pad__keys {
  display: grid;
  gap: clamp(8px, 0.7vw, 13px);
  grid-auto-rows: minmax(0, 1fr);
  min-height: 0;
}
.pad--decimal .pad__keys,
.pad--int .pad__keys,
.pad--phone .pad__keys {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.pad--plate .pad__keys {
  grid-template-columns: repeat(6, minmax(0, 1fr));
}

.key {
  display: grid;
  place-items: center;
  min-height: 58px;
  padding: 0;
  border-radius: 14px;
  cursor: pointer;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: clamp(24px, 2.3vw, 38px);
  font-weight: 600;
  color: #eaf4ff;
  background: linear-gradient(165deg, rgba(23, 55, 96, 0.96), rgba(9, 24, 45, 0.96));
  border: 1px solid rgba(79, 155, 255, 0.26);
  box-shadow: inset 0 1px 0 rgba(150, 205, 255, 0.16), 0 4px 14px rgba(0, 0, 0, 0.32);
  transition: transform 0.08s ease, background 0.12s ease, border-color 0.12s ease;
  -webkit-tap-highlight-color: transparent;
}
.key:active {
  transform: scale(0.96);
  background: linear-gradient(165deg, rgba(47, 123, 255, 0.55), rgba(20, 60, 116, 0.95));
  border-color: rgba(31, 209, 249, 0.7);
}
.key--wide { grid-column: span 3; }
.pad--plate .key {
  font-size: clamp(16px, 1.45vw, 23px);
  min-height: 48px;
  border-radius: 11px;
  font-family: 'JetBrains Mono', Consolas, monospace;
}

.pad__side {
  display: grid;
  grid-template-rows: 1fr 1fr 1.6fr;
  gap: clamp(8px, 0.7vw, 13px);
  min-height: 0;
}
.side {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 0;
  border-radius: 14px;
  cursor: pointer;
  color: #cfe2fa;
  border: 1px solid rgba(79, 155, 255, 0.26);
  background: linear-gradient(165deg, rgba(16, 40, 72, 0.95), rgba(8, 20, 38, 0.95));
  box-shadow: inset 0 1px 0 rgba(150, 205, 255, 0.12);
  transition: transform 0.08s ease, border-color 0.12s ease, color 0.12s ease;
  -webkit-tap-highlight-color: transparent;
}
.side span { font-size: clamp(20px, 1.9vw, 30px); line-height: 1; }
.side em {
  font-style: normal;
  font-size: clamp(11px, 0.85vw, 13px);
  letter-spacing: 1px;
  opacity: 0.72;
  white-space: nowrap;
}
.side:active { transform: scale(0.96); }
.side--del:active { color: var(--warning); border-color: rgba(255, 184, 77, 0.6); }
.side--clear:active { color: var(--danger); border-color: rgba(255, 92, 122, 0.6); }

.side--ok {
  color: #ffffff;
  border: 1px solid rgba(120, 220, 255, 0.55);
  background: linear-gradient(165deg, #2f7bff, #14a8e6);
  box-shadow: 0 8px 26px rgba(31, 129, 255, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.side--ok span { font-size: clamp(24px, 2.2vw, 34px); }
.side--ok em { font-size: clamp(12px, 1vw, 15px); opacity: 0.95; }
.side--ok:active { transform: scale(0.96); filter: brightness(1.1); }
.side--ok:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
</style>
