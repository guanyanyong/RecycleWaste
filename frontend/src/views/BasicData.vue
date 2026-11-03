<template>
  <div class="page basic">
    <div class="page-head">
      <div>
        <h1 class="page-title">基础数据</h1>
        <p class="page-desc">维护物料、分类、站点、客户与扣杂规则，配置自动带入过磅流程</p>
      </div>
      <div class="head-actions">
        <el-button v-if="canManage && tab === 'material'" type="primary" @click="openMaterial()">
          <el-icon><Plus /></el-icon> 新增物料
        </el-button>
        <el-button v-if="canManage && tab === 'category'" type="primary" @click="openCategory()">
          <el-icon><Plus /></el-icon> 新增分类
        </el-button>
        <el-button v-if="canManage && tab === 'station'" type="primary" @click="openStation()">
          <el-icon><Plus /></el-icon> 新增站点
        </el-button>
        <el-button v-if="canManage && tab === 'customer'" type="primary" @click="openCustomer()">
          <el-icon><Plus /></el-icon> 新增客户
        </el-button>
        <el-button v-if="canManage && tab === 'deduct'" type="primary" @click="openRule()">
          <el-icon><Plus /></el-icon> 新增规则
        </el-button>
      </div>
    </div>

    <div class="tech-card">
      <el-tabs v-model="tab" class="basic-tabs">
        <!-- 物料 -->
        <el-tab-pane label="物料管理" name="material">
          <div class="filter-bar">
            <el-input v-model="materialKeyword" placeholder="物料名称 / 编码" clearable style="width: 220px" :prefix-icon="Search" @keyup.enter="loadMaterials" @clear="loadMaterials" />
            <el-select v-model="materialCategory" placeholder="全部分类" clearable style="width: 170px" @change="loadMaterials">
              <el-option v-for="c in flatCategories" :key="c.category_id" :label="c.label" :value="c.category_id" />
            </el-select>
            <el-button @click="loadMaterials">查询</el-button>
          </div>
          <el-table :data="materials" v-loading="loading" height="calc(100vh - 320px)">
            <el-table-column prop="material_code" label="编码" width="130">
              <template #default="{ row }"><span class="mono">{{ row.material_code }}</span></template>
            </el-table-column>
            <el-table-column prop="material_name" label="物料名称" min-width="130" />
            <el-table-column prop="category_name" label="所属分类" min-width="120">
              <template #default="{ row }">{{ row.category_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="80" align="center" />
            <el-table-column label="默认单价" width="120" align="right">
              <template #default="{ row }">¥ {{ Number(row.default_price || 0).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column label="价格类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">{{ row.price_type === 2 ? '浮动价' : '固定价' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'" effect="dark">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" align="center" fixed="right">
              <template #default="{ row }">
                <el-button v-if="canManage" size="small" plain @click="openMaterial(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 分类 -->
        <el-tab-pane label="分类管理" name="category">
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="系统预置分类所有租户共享，租户可新增自定义分类；停用分类不会影响历史磅单"
            class="mb"
          />
          <el-tree :data="categoryTree" node-key="category_id" default-expand-all :expand-on-click-node="false" class="cat-tree">
            <template #default="{ data }">
              <div class="cat-node">
                <span class="cat-name">{{ data.category_name }}</span>
                <span class="mono cat-code">{{ data.category_code }}</span>
                <el-tag v-if="data.is_builtin === 1" size="small" effect="plain" type="info">预置</el-tag>
                <el-tag v-else size="small" effect="plain" type="success">自定义</el-tag>
                <el-button v-if="canManage" text type="primary" size="small" @click.stop="openCategory(data)">
                  添加子类
                </el-button>
              </div>
            </template>
          </el-tree>
        </el-tab-pane>

        <!-- 站点 -->
        <el-tab-pane label="站点管理" name="station">
          <el-table :data="stations" v-loading="loading" height="calc(100vh - 290px)">
            <el-table-column prop="station_code" label="编码" width="120">
              <template #default="{ row }"><span class="mono">{{ row.station_code }}</span></template>
            </el-table-column>
            <el-table-column prop="station_name" label="站点名称" min-width="140" />
            <el-table-column prop="address" label="地址" min-width="200">
              <template #default="{ row }">{{ row.address || '-' }}</template>
            </el-table-column>
            <el-table-column prop="contact_name" label="联系人" width="110">
              <template #default="{ row }">{{ row.contact_name || '-' }}</template>
            </el-table-column>
            <el-table-column prop="contact_phone" label="联系电话" width="140">
              <template #default="{ row }">{{ row.contact_phone || '-' }}</template>
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
                <el-button v-if="canManage" size="small" plain @click="openStation(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 客户 -->
        <el-tab-pane label="客户管理" name="customer">
          <div class="filter-bar">
            <el-input v-model="customerKeyword" placeholder="姓名 / 手机号 / 编码" clearable style="width: 240px" :prefix-icon="Search" @keyup.enter="loadCustomers" @clear="loadCustomers" />
            <el-button @click="loadCustomers">查询</el-button>
          </div>
          <el-table :data="customers" v-loading="loading" height="calc(100vh - 320px)">
            <el-table-column prop="customer_code" label="编码" width="110">
              <template #default="{ row }"><span class="mono">{{ row.customer_code }}</span></template>
            </el-table-column>
            <el-table-column prop="customer_name" label="客户名称" min-width="140" />
            <el-table-column prop="phone" label="手机号" width="140">
              <template #default="{ row }">{{ row.phone || '-' }}</template>
            </el-table-column>
            <el-table-column label="类型" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">{{ row.customer_type === 2 ? '企业' : '个人' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="address" label="地址" min-width="180">
              <template #default="{ row }">{{ row.address || '-' }}</template>
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
                <el-button v-if="canManage" size="small" plain @click="openCustomer(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 扣杂规则 -->
        <el-tab-pane label="扣杂规则" name="deduct">
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="扣杂规则用于过磅时预填默认扣重，实际扣重以现场核价确认的快照为准"
            class="mb"
          />
          <el-table :data="rules" v-loading="loading" height="calc(100vh - 310px)">
            <el-table-column prop="rule_name" label="规则名称" min-width="140" />
            <el-table-column prop="material_name" label="适用物料" min-width="120">
              <template #default="{ row }">{{ row.material_name || '租户通用' }}</template>
            </el-table-column>
            <el-table-column label="扣重方式" width="120" align="center">
              <template #default="{ row }">
                <el-tag size="small" effect="plain">
                  {{ row.deduct_type === 1 ? '比例扣重' : row.deduct_type === 2 ? '固定扣重' : '比例扣款' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="参数" width="120" align="right">
              <template #default="{ row }">
                {{ row.deduct_type === 2 ? `${Number(row.fixed_value || 0).toFixed(2)} 吨` : `${(Number(row.ratio || 0) * 100).toFixed(2)}%` }}
              </template>
            </el-table-column>
            <el-table-column label="计算基数" width="100" align="center">
              <template #default="{ row }">{{ row.calc_base === 1 ? '毛重' : '净重' }}</template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="90" align="center" />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 1 ? 'success' : 'info'" effect="dark">
                  {{ row.status === 1 ? '启用' : '停用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" align="center">
              <template #default="{ row }">
                <el-button v-if="canManage" size="small" plain @click="openRule(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 物料弹窗 -->
    <el-dialog v-model="materialVisible" :title="materialForm.material_id ? '编辑物料' : '新增物料'" width="520px">
      <el-form :model="materialForm" label-width="92px">
        <el-form-item label="物料编码"><el-input v-model="materialForm.material_code" maxlength="50" /></el-form-item>
        <el-form-item label="物料名称"><el-input v-model="materialForm.material_name" maxlength="100" /></el-form-item>
        <el-form-item label="所属分类">
          <el-select v-model="materialForm.category_id" clearable placeholder="选择分类" style="width: 100%">
            <el-option v-for="c in flatCategories" :key="c.category_id" :label="c.label" :value="c.category_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计量单位"><el-input v-model="materialForm.unit" maxlength="10" /></el-form-item>
        <el-form-item label="默认单价">
          <el-input-number v-model="materialForm.default_price" :min="0" :precision="2" controls-position="right" style="width: 180px" />
          <span class="unit">元 / 吨</span>
        </el-form-item>
        <el-form-item label="价格类型">
          <el-radio-group v-model="materialForm.price_type">
            <el-radio :value="1">固定价</el-radio>
            <el-radio :value="2">浮动价</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序"><el-input-number v-model="materialForm.sort_no" :min="0" controls-position="right" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="materialForm.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="materialForm.remark" maxlength="200" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="materialVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveMaterial">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分类弹窗 -->
    <el-dialog v-model="categoryVisible" title="新增分类" width="440px">
      <el-form :model="categoryForm" label-width="88px">
        <el-form-item label="父分类">
          <el-select v-model="categoryForm.parent_id" clearable placeholder="顶级分类" style="width: 100%">
            <el-option v-for="c in flatCategories" :key="c.category_id" :label="c.label" :value="c.category_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类编码"><el-input v-model="categoryForm.category_code" maxlength="50" /></el-form-item>
        <el-form-item label="分类名称"><el-input v-model="categoryForm.category_name" maxlength="100" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>

    <!-- 站点弹窗 -->
    <el-dialog v-model="stationVisible" :title="stationForm.station_id ? '编辑站点' : '新增站点'" width="480px">
      <el-form :model="stationForm" label-width="88px">
        <el-form-item label="站点编码"><el-input v-model="stationForm.station_code" maxlength="50" /></el-form-item>
        <el-form-item label="站点名称"><el-input v-model="stationForm.station_name" maxlength="100" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="stationForm.address" maxlength="200" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="stationForm.contact_name" maxlength="50" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="stationForm.contact_phone" maxlength="20" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="stationForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stationVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveStation">保存</el-button>
      </template>
    </el-dialog>

    <!-- 客户弹窗 -->
    <el-dialog v-model="customerVisible" :title="customerForm.customer_id ? '编辑客户' : '新增客户'" width="480px">
      <el-form :model="customerForm" label-width="88px">
        <el-form-item label="客户名称"><el-input v-model="customerForm.customer_name" maxlength="100" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="customerForm.phone" maxlength="20" /></el-form-item>
        <el-form-item label="客户类型">
          <el-radio-group v-model="customerForm.customer_type">
            <el-radio :value="1">个人</el-radio>
            <el-radio :value="2">企业</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="地址"><el-input v-model="customerForm.address" maxlength="200" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="customerForm.remark" maxlength="200" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCustomer">保存</el-button>
      </template>
    </el-dialog>

    <!-- 扣杂规则弹窗 -->
    <el-dialog v-model="ruleVisible" :title="ruleForm.rule_id ? '编辑规则' : '新增规则'" width="500px">
      <el-form :model="ruleForm" label-width="96px">
        <el-form-item label="规则名称"><el-input v-model="ruleForm.rule_name" maxlength="50" /></el-form-item>
        <el-form-item label="适用物料">
          <el-select v-model="ruleForm.material_id" clearable placeholder="租户通用" style="width: 100%">
            <el-option v-for="m in materials" :key="m.material_id" :label="m.material_name" :value="m.material_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="扣重方式">
          <el-radio-group v-model="ruleForm.deduct_type">
            <el-radio :value="1">比例扣重</el-radio>
            <el-radio :value="2">固定扣重</el-radio>
            <el-radio :value="3">比例扣款</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="ruleForm.deduct_type !== 2" label="比例">
          <el-input-number v-model="ruleForm.ratioPercent" :min="0" :max="30" :precision="2" :step="0.5" controls-position="right" style="width: 160px" />
          <span class="unit">%</span>
        </el-form-item>
        <el-form-item v-else label="固定扣重">
          <el-input-number v-model="ruleForm.fixed_value" :min="0" :precision="2" :step="0.05" controls-position="right" style="width: 160px" />
          <span class="unit">吨</span>
        </el-form-item>
        <el-form-item label="计算基数">
          <el-radio-group v-model="ruleForm.calc_base">
            <el-radio :value="1">毛重</el-radio>
            <el-radio :value="2">净重</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="优先级"><el-input-number v-model="ruleForm.priority" :min="0" controls-position="right" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="ruleForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { basicApi } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const canManage = computed(() => auth.hasPerm('material:manage'))

const tab = ref('material')
const loading = ref(false)
const saving = ref(false)

const materials = ref([])
const categoryTree = ref([])
const stations = ref([])
const customers = ref([])
const rules = ref([])

const materialKeyword = ref('')
const materialCategory = ref(null)
const customerKeyword = ref('')

const materialVisible = ref(false)
const categoryVisible = ref(false)
const stationVisible = ref(false)
const customerVisible = ref(false)
const ruleVisible = ref(false)

const materialForm = reactive({})
const categoryForm = reactive({ parent_id: null, category_code: '', category_name: '' })
const stationForm = reactive({})
const customerForm = reactive({})
const ruleForm = reactive({})

const flatCategories = computed(() => {
  const out = []
  const walk = (nodes, depth = 0) => {
    nodes.forEach((n) => {
      out.push({
        category_id: n.category_id,
        label: `${'　'.repeat(depth)}${n.category_name}`,
        category_name: n.category_name,
        parent_id: n.parent_id
      })
      if (n.children?.length) walk(n.children, depth + 1)
    })
  }
  walk(categoryTree.value)
  return out
})

async function loadMaterials() {
  loading.value = true
  try {
    materials.value = await basicApi.materials({
      keyword: materialKeyword.value || undefined,
      category_id: materialCategory.value || undefined
    })
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  categoryTree.value = await basicApi.categories()
}

async function loadStations() {
  loading.value = true
  try {
    stations.value = await basicApi.stations()
  } finally {
    loading.value = false
  }
}

async function loadCustomers() {
  loading.value = true
  try {
    customers.value = await basicApi.customers({ keyword: customerKeyword.value || undefined })
  } finally {
    loading.value = false
  }
}

async function loadRules() {
  loading.value = true
  try {
    rules.value = await basicApi.deductRules()
  } finally {
    loading.value = false
  }
}

function reset(obj, data) {
  Object.keys(obj).forEach((k) => delete obj[k])
  Object.assign(obj, data)
}

function openMaterial(row) {
  reset(
    materialForm,
    row
      ? { ...row }
      : {
          material_id: null,
          material_code: '',
          material_name: '',
          category_id: null,
          unit: '吨',
          default_price: 0,
          price_type: 1,
          sort_no: 0,
          status: 1,
          remark: ''
        }
  )
  materialVisible.value = true
}

async function saveMaterial() {
  if (!materialForm.material_code || !materialForm.material_name) {
    return ElMessage.warning('请填写物料编码与名称')
  }
  saving.value = true
  try {
    const payload = {
      material_code: materialForm.material_code,
      material_name: materialForm.material_name,
      category_id: materialForm.category_id || null,
      unit: materialForm.unit || '吨',
      default_price: materialForm.default_price ?? 0,
      price_type: materialForm.price_type || 1,
      sort_no: materialForm.sort_no || 0,
      status: materialForm.status ?? 1,
      remark: materialForm.remark || null
    }
    if (materialForm.material_id) {
      await basicApi.updateMaterial(materialForm.material_id, payload)
    } else {
      await basicApi.createMaterial(payload)
    }
    ElMessage.success('保存成功')
    materialVisible.value = false
    await loadMaterials()
    await loadCategories()
  } finally {
    saving.value = false
  }
}

function openCategory(parent) {
  reset(categoryForm, { parent_id: parent?.category_id || null, category_code: '', category_name: '' })
  categoryVisible.value = true
}

async function saveCategory() {
  if (!categoryForm.category_code || !categoryForm.category_name) {
    return ElMessage.warning('请填写分类编码与名称')
  }
  saving.value = true
  try {
    await basicApi.createCategory({
      category_code: categoryForm.category_code,
      category_name: categoryForm.category_name,
      parent_id: categoryForm.parent_id || null
    })
    ElMessage.success('分类已创建')
    categoryVisible.value = false
    await loadCategories()
  } finally {
    saving.value = false
  }
}

function openStation(row) {
  reset(
    stationForm,
    row
      ? { ...row }
      : { station_id: null, station_code: '', station_name: '', address: '', contact_name: '', contact_phone: '', status: 1 }
  )
  stationVisible.value = true
}

async function saveStation() {
  if (!stationForm.station_code || !stationForm.station_name) {
    return ElMessage.warning('请填写站点编码与名称')
  }
  saving.value = true
  try {
    const payload = {
      station_code: stationForm.station_code,
      station_name: stationForm.station_name,
      address: stationForm.address || null,
      contact_name: stationForm.contact_name || null,
      contact_phone: stationForm.contact_phone || null,
      status: stationForm.status ?? 1
    }
    if (stationForm.station_id) await basicApi.updateStation(stationForm.station_id, payload)
    else await basicApi.createStation(payload)
    ElMessage.success('保存成功')
    stationVisible.value = false
    await loadStations()
  } finally {
    saving.value = false
  }
}

function openCustomer(row) {
  reset(
    customerForm,
    row
      ? { ...row }
      : { customer_id: null, customer_name: '', phone: '', customer_type: 1, address: '', remark: '' }
  )
  customerVisible.value = true
}

async function saveCustomer() {
  if (!customerForm.customer_name) return ElMessage.warning('请填写客户名称')
  saving.value = true
  try {
    const payload = {
      customer_name: customerForm.customer_name,
      phone: customerForm.phone || null,
      customer_type: customerForm.customer_type || 1,
      address: customerForm.address || null,
      remark: customerForm.remark || null
    }
    if (customerForm.customer_id) await basicApi.updateCustomer(customerForm.customer_id, payload)
    else await basicApi.createCustomer(payload)
    ElMessage.success('保存成功')
    customerVisible.value = false
    await loadCustomers()
  } finally {
    saving.value = false
  }
}

function openRule(row) {
  reset(
    ruleForm,
    row
      ? { ...row, ratioPercent: Number(row.ratio || 0) * 100 }
      : {
          rule_id: null,
          rule_name: '',
          material_id: null,
          deduct_type: 1,
          ratioPercent: 2,
          fixed_value: 0,
          calc_base: 2,
          priority: 0,
          status: 1
        }
  )
  ruleVisible.value = true
}

async function saveRule() {
  if (!ruleForm.rule_name) return ElMessage.warning('请填写规则名称')
  saving.value = true
  try {
    await basicApi.saveDeductRule(
      {
        rule_name: ruleForm.rule_name,
        material_id: ruleForm.material_id || null,
        deduct_type: ruleForm.deduct_type,
        ratio: ruleForm.deduct_type === 2 ? null : Number(ruleForm.ratioPercent || 0) / 100,
        fixed_value: ruleForm.deduct_type === 2 ? ruleForm.fixed_value : null,
        calc_base: ruleForm.calc_base,
        priority: ruleForm.priority || 0,
        status: ruleForm.status ?? 1
      },
      ruleForm.rule_id || undefined
    )
    ElMessage.success('规则已保存')
    ruleVisible.value = false
    await loadRules()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadMaterials()
  loadCategories()
  loadStations()
  loadCustomers()
  loadRules()
})
</script>

<style scoped>
.head-actions { display: flex; gap: 10px; }
.basic-tabs :deep(.el-tabs__header) { margin-bottom: 16px; }
.basic-tabs :deep(.el-tabs__nav-wrap::after) { background-color: rgba(70, 150, 255, 0.12); }
.filter-bar { display: flex; gap: 10px; margin-bottom: 14px; }
.mb { margin-bottom: 14px; }

.cat-tree {
  background: transparent;
  --el-tree-node-hover-bg-color: rgba(31, 129, 255, 0.08);
}
.cat-tree :deep(.el-tree-node__content) { height: 42px; border-radius: 8px; }
.cat-node { display: flex; align-items: center; gap: 10px; width: 100%; }
.cat-name { font-size: 13px; color: #dbeafe; }
.cat-code { font-size: 11px; color: #5f7f9f; }
.unit { margin-left: 8px; font-size: 12px; color: #6f8bb0; }
</style>
