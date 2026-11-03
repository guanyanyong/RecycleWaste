<template>
  <div class="layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <div class="logo__mark">
          <el-icon :size="22"><Refresh /></el-icon>
        </div>
        <div class="logo__text">
          <strong>再生资源</strong>
          <span>RECYCLE OS</span>
        </div>
      </div>

      <div class="sidebar__label">运营导航</div>
      <el-menu :default-active="route.path" router class="menu" background-color="transparent">
        <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar__label sidebar__label--term">现场终端</div>
      <button type="button" class="term-entry" @click="goTouch">
        <span class="term-entry__ico"><el-icon><Pointer /></el-icon></span>
        <span class="term-entry__txt">
          <b>过磅工作台-触摸</b>
          <em>大按钮 · 触摸键盘</em>
        </span>
        <el-icon class="term-entry__arrow"><ArrowRight /></el-icon>
      </button>

      <div class="sidebar__foot">
        <div class="tenant">
          <el-icon><OfficeBuilding /></el-icon>
          <div>
            <b>{{ auth.user?.tenant_name }}</b>
            <span>{{ auth.user?.roles?.join(' / ') }}</span>
          </div>
        </div>
        <div class="sys-status"><i></i> 服务在线</div>
      </div>
    </aside>

    <!-- 主区 -->
    <section class="main">
      <header class="header">
        <div class="header__left">
          <div class="crumb">
            <span>控制台</span>
            <el-icon><ArrowRight /></el-icon>
            <b>{{ route.meta.title }}</b>
          </div>
        </div>

        <div class="header__right">
          <div class="clock">
            <span class="clock__time mono">{{ clock.time }}</span>
            <span class="clock__date">{{ clock.date }}</span>
          </div>

          <el-tooltip content="刷新当前页" placement="bottom">
            <button class="icon-btn" @click="reload">
              <el-icon><RefreshRight /></el-icon>
            </button>
          </el-tooltip>

          <el-dropdown trigger="click" @command="onCommand">
            <div class="user">
              <div class="user__avatar">{{ initials }}</div>
              <div class="user__meta">
                <b>{{ auth.user?.real_name }}</b>
                <span>{{ auth.user?.username }}</span>
              </div>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <span class="muted">租户：{{ auth.user?.tenant_name }}</span>
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const menus = computed(() => {
  const root = router.options.routes.find((r) => r.path === '/')
  return (root?.children || [])
    .filter((c) => !c.meta?.perm || auth.hasPerm(c.meta.perm))
    .map((c) => ({ path: `/${c.path}`, title: c.meta.title, icon: c.meta.icon }))
})

const initials = computed(() => {
  const name = auth.user?.real_name || 'U'
  return name.slice(0, 1).toUpperCase()
})

const clock = reactive({ time: '--:--:--', date: '' })
let timer = null

function tick() {
  const now = new Date()
  clock.time = now.toLocaleTimeString('zh-CN', { hour12: false })
  clock.date = now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' })
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
})
onBeforeUnmount(() => clearInterval(timer))

function reload() {
  window.location.reload()
}

function goTouch() {
  router.push('/touch')
}

async function onCommand(cmd) {
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确认退出当前账号？', '退出登录', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await auth.logout()
      router.replace('/login')
    } catch {
      /* 用户取消 */
    }
  }
}
</script>

<style scoped>
.layout { display: flex; height: 100vh; overflow: hidden; }

/* ---------- 侧边栏 ---------- */
.sidebar {
  width: 236px;
  flex: 0 0 236px;
  display: flex;
  flex-direction: column;
  padding: 20px 14px 16px;
  background: linear-gradient(180deg, rgba(8, 24, 46, 0.96), rgba(4, 14, 28, 0.94));
  border-right: 1px solid rgba(64, 153, 255, 0.16);
  box-shadow: 8px 0 40px rgba(0, 0, 0, 0.35);
  position: relative;
  z-index: 10;
}
.sidebar::after {
  content: '';
  position: absolute;
  top: 0; right: -1px;
  width: 1px; height: 180px;
  background: linear-gradient(180deg, rgba(31, 209, 249, 0.85), transparent);
}

.logo { display: flex; align-items: center; gap: 12px; padding: 4px 6px 22px; }
.logo__mark {
  width: 42px; height: 42px;
  display: grid; place-items: center;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(145deg, #2f7bff, #12c9f5);
  box-shadow: 0 0 24px rgba(47, 123, 255, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.logo__text { display: flex; flex-direction: column; line-height: 1.2; }
.logo__text strong { font-size: 16px; letter-spacing: 2px; color: #eaf4ff; }
.logo__text span { font-size: 9px; letter-spacing: 2.6px; color: #5b86b8; margin-top: 3px; }

.sidebar__label {
  padding: 0 12px 8px;
  font-size: 10px;
  letter-spacing: 2px;
  color: #48658a;
}

.menu { border-right: none; flex: 1; }
.menu :deep(.el-menu-item) {
  height: 46px;
  margin: 4px 0;
  border-radius: 10px;
  color: #9cb6d8;
  font-size: 13.5px;
  letter-spacing: 0.5px;
  transition: all 0.18s ease;
}
.menu :deep(.el-menu-item:hover) {
  background: rgba(47, 123, 255, 0.12);
  color: #d9ecff;
}
.menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(96deg, rgba(47, 123, 255, 0.28), rgba(31, 209, 249, 0.08));
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(90, 180, 255, 0.25), 0 6px 20px rgba(31, 129, 255, 0.18);
}
.menu :deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0; top: 12px; bottom: 12px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #4fd8ff, #2f7bff);
  box-shadow: 0 0 12px #2f7bff;
}
.menu :deep(.el-icon) { font-size: 17px; }

/* 触摸终端入口 */
.sidebar__label--term { margin-top: 10px; }
.term-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 2px 12px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  color: #d8ecff;
  background: linear-gradient(100deg, rgba(31, 209, 249, 0.16), rgba(47, 123, 255, 0.08));
  border: 1px solid rgba(31, 209, 249, 0.42);
  box-shadow: 0 0 18px rgba(31, 209, 249, 0.14), inset 0 1px 0 rgba(160, 230, 255, 0.16);
  transition: all 0.16s ease;
}
.term-entry:hover {
  border-color: rgba(31, 209, 249, 0.8);
  box-shadow: 0 0 24px rgba(31, 209, 249, 0.3);
  transform: translateY(-1px);
}
.term-entry__ico {
  width: 32px; height: 32px;
  flex: 0 0 32px;
  display: grid; place-items: center;
  border-radius: 9px;
  color: #04121f;
  background: linear-gradient(145deg, #6fe2ff, #2f7bff);
  box-shadow: 0 0 14px rgba(31, 209, 249, 0.5);
}
.term-entry__txt { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.term-entry__txt b { font-size: 12.5px; letter-spacing: 0.4px; color: #eaf8ff; white-space: nowrap; }
.term-entry__txt em { font-style: normal; font-size: 10px; color: #7fbfe0; letter-spacing: 0.6px; }
.term-entry__arrow { margin-left: auto; font-size: 12px; color: #6fc8e8; }

.sidebar__foot {
  border-top: 1px solid rgba(64, 153, 255, 0.12);
  padding-top: 14px;
  display: grid;
  gap: 10px;
}
.tenant { display: flex; align-items: center; gap: 10px; padding: 8px 10px; border-radius: 10px; background: rgba(31, 129, 255, 0.07); }
.tenant :deep(.el-icon) { color: #4f9bff; font-size: 18px; }
.tenant b { display: block; font-size: 12.5px; color: #cfe2fa; }
.tenant span { font-size: 10.5px; color: #6483a8; }
.sys-status { display: flex; align-items: center; gap: 7px; font-size: 11px; color: #5f7f9f; padding-left: 4px; }
.sys-status i { width: 6px; height: 6px; border-radius: 50%; background: #22e0a1; box-shadow: 0 0 8px #22e0a1; }

/* ---------- 主区 ---------- */
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; }

.header {
  height: 66px;
  flex: 0 0 66px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  border-bottom: 1px solid rgba(64, 153, 255, 0.12);
  background: rgba(5, 16, 32, 0.55);
  backdrop-filter: blur(16px);
  z-index: 5;
}

.crumb { display: flex; align-items: center; gap: 8px; font-size: 12.5px; color: #5f7f9f; }
.crumb b { color: #cfe2fa; font-weight: 500; letter-spacing: 0.5px; }
.crumb :deep(.el-icon) { font-size: 11px; }

.header__right { display: flex; align-items: center; gap: 16px; }

.clock { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.2; }
.clock__time { font-size: 15px; color: #bfe4ff; letter-spacing: 1px; }
.clock__date { font-size: 10.5px; color: #56759a; }

.icon-btn {
  width: 34px; height: 34px;
  display: grid; place-items: center;
  border-radius: 9px;
  border: 1px solid rgba(64, 153, 255, 0.18);
  background: rgba(31, 129, 255, 0.06);
  color: #8fb6e0;
  cursor: pointer;
  transition: all 0.18s ease;
}
.icon-btn:hover { color: #4fd8ff; border-color: rgba(79, 216, 255, 0.5); box-shadow: 0 0 16px rgba(31, 209, 249, 0.2); }

.user { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 5px 8px; border-radius: 10px; transition: background 0.18s; }
.user:hover { background: rgba(31, 129, 255, 0.1); }
.user__avatar {
  width: 34px; height: 34px;
  border-radius: 10px;
  display: grid; place-items: center;
  font-size: 14px; font-weight: 700;
  color: #fff;
  background: linear-gradient(145deg, #2f7bff, #7c5cff);
  box-shadow: 0 0 16px rgba(47, 123, 255, 0.4);
}
.user__meta { display: flex; flex-direction: column; line-height: 1.25; }
.user__meta b { font-size: 12.5px; color: #dcebff; }
.user__meta span { font-size: 10.5px; color: #5f7f9f; }
.user :deep(.el-icon) { color: #6483a8; font-size: 12px; }

.content { flex: 1; min-height: 0; overflow: hidden; }
</style>
