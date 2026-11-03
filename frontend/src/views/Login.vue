<template>
  <div class="login">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    <div class="scanline"></div>

    <div class="login__inner">
      <!-- 左侧品牌区 -->
      <section class="brand">
        <div class="brand__badge">
          <el-icon :size="30"><Refresh /></el-icon>
        </div>
        <p class="brand__kicker">RECYCLE RESOURCE · INTELLIGENT PLATFORM</p>
        <h1 class="brand__title">
          再生资源<br /><span>回收管理系统</span>
        </h1>
        <p class="brand__desc">
          从车辆进厂、过磅读数、质检核价到结算付款的全链路数字化平台，
          多租户隔离、数据快照留痕、账实可追溯。
        </p>

        <div class="brand__features">
          <div class="feature">
            <el-icon><Grid /></el-icon>
            <div>
              <b>多租户与多站点</b>
              <span>租户级数据隔离，站点范围授权</span>
            </div>
          </div>
          <div class="feature">
            <el-icon><Odometer /></el-icon>
            <div>
              <b>两种过磅模式</b>
              <span>毛皮两次过磅 / 单次读数即净重</span>
            </div>
          </div>
          <div class="feature">
            <el-icon><Money /></el-icon>
            <div>
              <b>结算快照</b>
              <span>重量金额留痕，历史不随配置漂移</span>
            </div>
          </div>
        </div>

        <div class="brand__stats">
          <div><strong>21</strong><span>数据表</span></div>
          <div><strong>19</strong><span>权限点</span></div>
          <div><strong>5</strong><span>内置角色</span></div>
        </div>
      </section>

      <!-- 右侧登录卡 -->
      <section class="panel">
        <div class="panel__head">
          <div class="panel__status"><i></i> 系统运行正常</div>
          <span class="panel__ver">v1.0</span>
        </div>
        <h2>欢迎登录</h2>
        <p class="panel__sub">请使用分配给您的账号进入控制台</p>

        <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @submit.prevent>
          <el-form-item label="账号" prop="username">
            <el-input v-model="form.username" size="large" placeholder="请输入登录名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              placeholder="请输入密码"
              :prefix-icon="Lock"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button class="panel__submit" type="primary" size="large" :loading="loading" @click="submit">
            进入系统
            <el-icon class="el-icon--right"><Right /></el-icon>
          </el-button>
        </el-form>

        <div class="panel__hint">
          <span>演示账号</span>
          <code>admin / admin123</code>
        </div>
        <p class="panel__footer">© 2026 再生资源回收管理系统 · 数据实时同步</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })
const rules = {
  username: [{ required: true, message: '请输入登录名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function submit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await auth.login(form.username, form.password)
    ElMessage.success(`欢迎回来，${auth.user.real_name}`)
    router.replace(route.query.redirect || '/dashboard')
  } catch (e) {
    // 错误提示由拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  position: relative;
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
  animation: float-slow 12s ease-in-out infinite;
}
.orb-1 { width: 520px; height: 520px; background: #1f6dff; top: -160px; left: -120px; }
.orb-2 { width: 420px; height: 420px; background: #12d3f5; bottom: -140px; right: -80px; animation-delay: -4s; }
.orb-3 { width: 360px; height: 360px; background: #7c5cff; top: 40%; left: 45%; opacity: 0.28; animation-delay: -7s; }

.scanline {
  position: absolute;
  left: 0; right: 0; top: 0;
  height: 140px;
  background: linear-gradient(180deg, transparent, rgba(31, 209, 249, 0.07), transparent);
  animation: scan 9s linear infinite;
  pointer-events: none;
}

.login__inner {
  position: relative;
  z-index: 2;
  width: min(1120px, 92vw);
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 56px;
  align-items: center;
}

/* 左侧 */
.brand__badge {
  width: 60px; height: 60px;
  display: grid; place-items: center;
  border-radius: 18px;
  color: #fff;
  background: linear-gradient(140deg, #2f7bff, #12c9f5);
  box-shadow: 0 0 36px rgba(47, 123, 255, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.4);
  margin-bottom: 22px;
}

.brand__kicker {
  margin: 0 0 12px;
  font-size: 11px;
  letter-spacing: 3.4px;
  color: #6fa9e8;
}

.brand__title {
  margin: 0;
  font-size: 46px;
  line-height: 1.18;
  font-weight: 800;
  letter-spacing: 2px;
  color: #f1f7ff;
  text-shadow: 0 0 40px rgba(47, 123, 255, 0.35);
}
.brand__title span {
  background: linear-gradient(94deg, #6fd6ff, #3f8bff 60%, #9d8bff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.brand__desc {
  margin: 18px 0 30px;
  max-width: 470px;
  font-size: 14px;
  line-height: 1.9;
  color: #9db8d9;
}

.brand__features { display: grid; gap: 12px; }
.feature {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(70, 150, 255, 0.14);
  background: rgba(10, 30, 58, 0.4);
  backdrop-filter: blur(8px);
}
.feature :deep(.el-icon) {
  color: #33d6ff;
  font-size: 20px;
  margin-top: 2px;
  filter: drop-shadow(0 0 8px rgba(51, 214, 255, 0.6));
}
.feature b { display: block; font-size: 13.5px; letter-spacing: 0.4px; }
.feature span { font-size: 12px; color: #7d9abc; }

.brand__stats {
  display: flex;
  gap: 34px;
  margin-top: 30px;
  padding-top: 22px;
  border-top: 1px solid rgba(70, 150, 255, 0.14);
}
.brand__stats div { display: flex; flex-direction: column; gap: 2px; }
.brand__stats strong {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 26px;
  color: #5fd8ff;
  text-shadow: 0 0 20px rgba(31, 209, 249, 0.5);
}
.brand__stats span { font-size: 11.5px; color: #6885a8; letter-spacing: 1px; }

/* 右侧 */
.panel {
  padding: 34px 34px 26px;
  border-radius: 20px;
  background: linear-gradient(160deg, rgba(14, 40, 78, 0.9), rgba(6, 18, 36, 0.86));
  border: 1px solid rgba(80, 170, 255, 0.22);
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.55), 0 0 60px rgba(31, 129, 255, 0.12),
    inset 0 1px 0 rgba(150, 210, 255, 0.12);
  backdrop-filter: blur(20px);
}

.panel__head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 24px;
}
.panel__status {
  display: flex; align-items: center; gap: 7px;
  font-size: 11.5px; color: #6fe3b8;
}
.panel__status i {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22e0a1;
  box-shadow: 0 0 10px #22e0a1;
  animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse { 50% { opacity: 0.35; } }
.panel__ver { font-size: 11px; color: #5b7699; letter-spacing: 1px; }

.panel h2 {
  margin: 0 0 6px;
  font-size: 25px;
  letter-spacing: 1.6px;
  color: #f0f7ff;
}
.panel__sub { margin: 0 0 26px; font-size: 12.5px; color: #7f9ec2; }

.panel :deep(.el-form-item__label) {
  font-size: 12px;
  letter-spacing: 0.8px;
  color: #8fb0d4;
  padding-bottom: 6px;
}

.panel__submit {
  width: 100%;
  margin-top: 8px;
  height: 46px;
  font-size: 15px;
  letter-spacing: 3px;
  border-radius: 10px;
}

.panel__hint {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 9px;
  background: rgba(31, 129, 255, 0.08);
  border: 1px dashed rgba(70, 150, 255, 0.25);
  font-size: 12px;
  color: #7f9ec2;
}
.panel__hint code {
  font-family: 'JetBrains Mono', Consolas, monospace;
  color: #6fd6ff;
}

.panel__footer {
  margin: 22px 0 0;
  text-align: center;
  font-size: 11px;
  color: #4f6a8c;
  letter-spacing: 0.4px;
}

@media (max-width: 980px) {
  .login__inner { grid-template-columns: 1fr; gap: 30px; }
  .brand__features, .brand__stats { display: none; }
  .brand__title { font-size: 32px; }
}
</style>
