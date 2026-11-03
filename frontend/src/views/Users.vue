<template>
  <div class="page users">
    <div class="page-head">
      <div>
        <h1 class="page-title">用户与权限</h1>
        <p class="page-desc">账号归属租户，一个用户可拥有多个角色，权限取并集</p>
      </div>
      <div class="head-actions">
        <el-input v-model="keyword" placeholder="登录名 / 姓名 / 手机号" clearable style="width: 230px" :prefix-icon="Search" @keyup.enter="loadUsers" @clear="loadUsers" />
        <el-button @click="loadUsers">查询</el-button>
        <el-button type="primary" @click="openUser()"><el-icon><Plus /></el-icon> 新增用户</el-button>
      </div>
    </div>

    <div class="grid users-grid">
      <div class="tech-card">
        <div class="tech-card__head">
          <div class="tech-card__title">账号列表</div>
          <span class="tech-card__sub">共 {{ users.length }} 人</span>
        </div>
        <el-table :data="users" v-loading="loading" height="calc(100vh - 250px)">
          <el-table-column label="用户" min-width="170">
            <template #default="{ row }">
              <div class="user-cell">
                <div class="avatar">{{ (row.real_name || row.username).slice(0, 1) }}</div>
                <div>
                  <b>{{ row.real_name }}</b>
                  <span class="mono">{{ row.username }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="130">
            <template #default="{ row }">{{ row.phone || '-' }}</template>
          </el-table-column>
          <el-table-column label="角色" min-width="200">
            <template #default="{ row }">
              <el-tag v-for="r in row.roles" :key="r" size="small" effect="plain" class="role-tag">
                {{ roleName(r) }}
              </el-tag>
              <span v-if="!row.roles.length" class="muted">未分配</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'" effect="dark">
                {{ row.status === 1 ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" align="center">
            <template #default="{ row }">
              <el-button size="small" plain @click="openUser(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="right-col">
        <div class="tech-card">
          <div class="tech-card__head">
            <div class="tech-card__title">内置角色</div>
            <span class="tech-card__sub">{{ roles.length }} 个</span>
          </div>
          <div class="role-list">
            <div class="role-card" v-for="r in roles" :key="r.role_code">
              <div class="role-card__head">
                <b>{{ r.role_name }}</b>
                <el-tag v-if="r.is_builtin === 1" size="small" effect="plain" type="info">内置</el-tag>
              </div>
              <span class="mono">{{ r.role_code }}</span>
            </div>
          </div>
        </div>

        <div class="tech-card perms">
          <div class="tech-card__head">
            <div class="tech-card__title">权限点</div>
            <span class="tech-card__sub">{{ permissions.length }} 项</span>
          </div>
          <div class="perm-group" v-for="(items, group) in groupedPerms" :key="group">
            <div class="perm-group__name">{{ groupName(group) }}</div>
            <div class="perm-tags">
              <span class="perm-tag" v-for="p in items" :key="p.perm_id">{{ p.perm_name }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.user_id ? '编辑用户' : '新增用户'" width="520px">
      <el-form :model="form" label-width="88px">
        <el-form-item label="登录名">
          <el-input v-model="form.username" :disabled="!!form.user_id" maxlength="50" />
        </el-form-item>
        <el-form-item label="姓名"><el-input v-model="form.real_name" maxlength="50" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" maxlength="20" /></el-form-item>
        <el-form-item :label="form.user_id ? '重置密码' : '初始密码'">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.user_id ? '留空则不修改' : '至少 6 位'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_codes" multiple style="width: 100%" placeholder="选择角色">
            <el-option v-for="r in roles" :key="r.role_code" :label="r.role_name" :value="r.role_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="可见站点">
          <el-select v-model="form.station_scope" multiple style="width: 100%" placeholder="留空 = 全部站点">
            <el-option v-for="s in stations" :key="s.station_id" :label="s.station_name" :value="s.station_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" v-if="form.user_id">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { basicApi } from '../api'

const users = ref([])
const roles = ref([])
const permissions = ref([])
const stations = ref([])
const keyword = ref('')
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)

const form = reactive({
  user_id: null,
  username: '',
  real_name: '',
  phone: '',
  password: '',
  role_codes: [],
  station_scope: [],
  status: 1
})

const groupedPerms = computed(() => {
  const map = {}
  permissions.value.forEach((p) => {
    ;(map[p.perm_group] ||= []).push(p)
  })
  return map
})

const groupNameMap = { weigh: '过磅作业', deduct: '扣杂配置', settle: '结算管理', system: '系统管理', report: '报表分析' }
function groupName(g) {
  return groupNameMap[g] || g
}
function roleName(code) {
  return roles.value.find((r) => r.role_code === code)?.role_name || code
}

async function loadUsers() {
  loading.value = true
  try {
    users.value = await basicApi.users({ keyword: keyword.value || undefined })
  } finally {
    loading.value = false
  }
}

function openUser(row) {
  Object.assign(form, {
    user_id: row?.user_id || null,
    username: row?.username || '',
    real_name: row?.real_name || '',
    phone: row?.phone || '',
    password: '',
    role_codes: row?.roles ? [...row.roles] : [],
    station_scope: row?.station_scope ? String(row.station_scope).split(',').filter(Boolean).map(Number) : [],
    status: row?.status ?? 1
  })
  dialogVisible.value = true
}

async function save() {
  if (!form.username || !form.real_name) return ElMessage.warning('请填写登录名与姓名')
  if (!form.user_id && (!form.password || form.password.length < 6)) {
    return ElMessage.warning('初始密码至少 6 位')
  }
  saving.value = true
  try {
    if (form.user_id) {
      await basicApi.updateUser(form.user_id, {
        real_name: form.real_name,
        phone: form.phone || null,
        status: form.status,
        role_codes: form.role_codes,
        station_scope: form.station_scope,
        password: form.password || null
      })
    } else {
      await basicApi.createUser({
        username: form.username,
        password: form.password,
        real_name: form.real_name,
        phone: form.phone || null,
        role_codes: form.role_codes,
        station_scope: form.station_scope
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadUsers()
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const [r, p, s] = await Promise.all([basicApi.roles(), basicApi.permissions(), basicApi.stations()])
  roles.value = r
  permissions.value = p
  stations.value = s
  await loadUsers()
})
</script>

<style scoped>
.head-actions { display: flex; gap: 10px; }
.users-grid { grid-template-columns: minmax(0, 1.9fr) minmax(0, 1fr); align-items: start; }
.right-col { display: flex; flex-direction: column; gap: 16px; }

.user-cell { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 32px; height: 32px; border-radius: 9px;
  display: grid; place-items: center; font-size: 13px; font-weight: 700; color: #fff;
  background: linear-gradient(145deg, #2f7bff, #7c5cff);
}
.user-cell b { display: block; font-size: 12.5px; }
.user-cell span { font-size: 10.5px; color: #6483a8; }
.role-tag { margin: 2px 4px 2px 0; }

.role-list { display: grid; gap: 8px; }
.role-card {
  padding: 10px 12px; border-radius: 10px;
  background: rgba(31, 129, 255, 0.06);
  border: 1px solid rgba(70, 150, 255, 0.14);
}
.role-card__head { display: flex; align-items: center; justify-content: space-between; }
.role-card b { font-size: 12.5px; color: #dbeafe; }
.role-card span { font-size: 10.5px; color: #5f7f9f; }

.perms { max-height: 440px; overflow-y: auto; }
.perm-group { margin-bottom: 12px; }
.perm-group__name { font-size: 11px; color: #7f9ec2; margin-bottom: 6px; letter-spacing: 0.5px; }
.perm-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.perm-tag {
  font-size: 11px; padding: 3px 8px; border-radius: 5px;
  color: #9fc4ee; background: rgba(47, 123, 255, 0.1);
  border: 1px solid rgba(70, 150, 255, 0.16);
}

@media (max-width: 1200px) {
  .users-grid { grid-template-columns: 1fr; }
}
</style>
