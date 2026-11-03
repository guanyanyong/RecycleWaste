<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="modelValue" class="mask" @click.self="close">
        <section class="sheet" :class="`sheet--${size}`">
          <header class="sheet__head">
            <div class="sheet__title">
              <h3>{{ title }}</h3>
              <p v-if="subtitle">{{ subtitle }}</p>
            </div>
            <button type="button" class="sheet__close" @click="close">✕</button>
          </header>

          <div class="sheet__body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="sheet__foot">
            <slot name="footer" />
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  size: { type: String, default: 'normal' } // normal | wide
})
const emit = defineEmits(['update:modelValue'])

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3vh 3vw;
  background: rgba(2, 8, 18, 0.74);
  backdrop-filter: blur(10px);
}

.sheet {
  display: flex;
  flex-direction: column;
  width: min(760px, 92vw);
  max-height: 94vh;
  padding: 20px 22px 18px;
  border-radius: 20px;
  background: linear-gradient(160deg, #0d2547, #071831);
  border: 1px solid rgba(79, 155, 255, 0.42);
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(31, 209, 249, 0.1),
    inset 0 1px 0 rgba(150, 205, 255, 0.14);
  animation: sheet-in 0.2s ease;
}
.sheet--wide { width: min(1180px, 95vw); }

@keyframes sheet-in {
  from { transform: translateY(14px) scale(0.985); opacity: 0; }
  to { transform: none; opacity: 1; }
}

.sheet__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}
.sheet__title h3 {
  margin: 0;
  font-size: clamp(19px, 1.5vw, 24px);
  letter-spacing: 1px;
  color: var(--text-1);
}
.sheet__title p {
  margin: 5px 0 0;
  font-size: clamp(12px, 0.95vw, 14px);
  color: var(--text-3);
}

.sheet__close {
  flex: 0 0 auto;
  width: 52px;
  height: 52px;
  border-radius: 14px;
  cursor: pointer;
  font-size: 20px;
  color: #a9c0e2;
  background: rgba(16, 40, 72, 0.8);
  border: 1px solid rgba(79, 155, 255, 0.26);
  -webkit-tap-highlight-color: transparent;
}
.sheet__close:active { transform: scale(0.95); color: #fff; }

.sheet__body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.sheet__foot {
  flex: 0 0 auto;
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.sheet-enter-active, .sheet-leave-active { transition: opacity 0.2s ease; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
</style>
