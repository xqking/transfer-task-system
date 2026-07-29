<template>
  <div class="transfer-task">
    <div class="top-row">
      <el-card class="form-card">
        <template #header>
          <div class="card-header">
            <span>创建转账任务</span>
          </div>
        </template>

        <el-form :model="taskForm" label-width="100px" :rules="rules" ref="formRef" size="default">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="选择客户" prop="customer_id">
                <el-select 
                  v-model="taskForm.customer_id" 
                  placeholder="请选择客户" 
                  style="width: 100%;"
                  @change="onCustomerChange"
                >
                  <el-option 
                    v-for="c in customerList" 
                    :key="c.id" 
                    :label="c.name" 
                    :value="c.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="任务日期" prop="task_date">
                <el-date-picker
                  v-model="taskForm.task_date"
                  type="date"
                  placeholder="选择日期"
                  format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD"
                  style="width: 100%;"
                  @change="loadPersonStatusByCard"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="所需金额" prop="total_amount">
                <el-input-number 
                  v-model="taskForm.total_amount" 
                  :min="2000" 
                  :step="1000"
                  :precision="0"
                  :value-on-clear="30000"
                  style="width: 100%;"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="最低金额" prop="alloc_min">
                <el-input-number 
                  v-model="taskForm.alloc_min" 
                  :min="100" 
                  :step="100"
                  :precision="0"
                  style="width: 100%;"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="最高金额" prop="alloc_max">
                <el-input-number 
                  v-model="taskForm.alloc_max" 
                  :min="100" 
                  :step="100"
                  :precision="0"
                  style="width: 100%;"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item>
            <el-button type="primary" @click="createTask(false)" :loading="creating">
              创建并智能分配
            </el-button>
            <el-button type="danger" @click="createTask(true)" :loading="creating">
              强制分配
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="stats-card">
        <template #header>
          <span>任务统计</span>
        </template>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ personList.length }}</div>
            <div class="stat-label">总人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value available">{{ availablePersonCount }}</div>
            <div class="stat-label">可用人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value participating">{{ participatingPersonCount }}</div>
            <div class="stat-label">参与人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value excluded">{{ unselectedPersonIds.size }}</div>
            <div class="stat-label">排除人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value skipped">{{ skippedPersonCount }}</div>
            <div class="stat-label">跳过人数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value amount">¥{{ taskForm.total_amount.toLocaleString() }}</div>
            <div class="stat-label">总金额</div>
          </div>
        </div>
      </el-card>
    </div>

    <div class="middle-row">
      <el-card class="person-status-card">
        <template #header>
          <span>人员可用状态</span>
        </template>
        <div class="person-status-container">
          <div v-if="!taskForm.customer_id" class="no-data-tip">请先选择客户</div>
          <div v-else-if="personStatusList.length === 0" class="no-data-tip">加载中...</div>
          <div v-else>
            <div class="customer-info" v-if="customerList.find(c => c.id === taskForm.customer_id)">
              <span class="customer-name" :style="{ color: customerList.find(c => c.id === taskForm.customer_id)?.color }">
                {{ customerList.find(c => c.id === taskForm.customer_id)?.name }}
              </span>
              <span class="customer-desc">（负责该客户的所有银行卡任务）</span>
            </div>
            <div class="persons-section">
              <div class="persons-row">
                <span class="persons-label available">可用 ({{ personStatusList.filter(p => p.status === 'available').length }})</span>
                <div class="tags-group">
                  <el-tag 
                    v-for="p in personStatusList.filter(p => p.status === 'available')" 
                    :key="p.id"
                    size="small"
                    type="success"
                    effect="plain"
                    :title="p.reason || '可用'"
                    class="person-tag"
                  >{{ p.name }}</el-tag>
                  <span v-if="personStatusList.filter(p => p.status === 'available').length === 0" class="no-data">暂无可用人员</span>
                </div>
              </div>
              <div class="persons-row" v-if="personStatusList.filter(p => p.status === 'blocked').length > 0">
                <span class="persons-label blocked">不可用 ({{ personStatusList.filter(p => p.status === 'blocked').length }})</span>
                <div class="tags-group">
                  <el-tag 
                    v-for="p in personStatusList.filter(p => p.status === 'blocked')" 
                    :key="p.id"
                    size="small"
                    type="danger"
                    effect="plain"
                    :title="p.reason"
                    class="person-tag"
                  >{{ p.name }}</el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="preview-card" v-if="allocationResult">
        <template #header>
          <span>分配预览</span>
        </template>
        <el-alert 
          :title="`已分配给 ${allocationResult.selected_person} 负责 ${allocationResult.customer_name} 的 ${allocationResult.card_count} 张银行卡任务`" 
          type="success"
          show-icon
          :closable="false"
          style="margin-bottom: 15px;"
        />
        <el-descriptions title="分配详情" :column="1" border size="small">
          <el-descriptions-item label="负责人">
            <span style="font-weight: bold; color: #409eff;">{{ allocationResult.selected_person }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="客户">{{ allocationResult.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="银行卡数量">{{ allocationResult.card_count }} 张</el-descriptions-item>
          <el-descriptions-item label="总金额">
            <span style="color: #f56c6c; font-weight: bold; font-size: 16px;">¥{{ Math.round(taskForm.total_amount).toLocaleString() }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <el-divider content-position="left">银行卡明细</el-divider>
        <el-table :data="allocationDetails" max-height="300" size="small">
          <el-table-column prop="bank_name" label="银行" width="120">
            <template #default="{ row }">
              {{ row.bank_name?.replace('银行', '') }}
            </template>
          </el-table-column>
          <el-table-column prop="card_no" label="卡号" width="120">
            <template #default="{ row }">
              ****{{ row.card_no }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120">
            <template #default="{ row }">
              <span style="color: #409eff; font-weight: bold;">¥{{ Math.round(row.amount) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 15px; text-align: right; font-size: 14px; color: #666;">
          合计 <span style="color: #f56c6c; font-weight: bold; font-size: 16px;">¥{{ Math.round(taskForm.total_amount).toLocaleString() }}</span>
        </div>
      </el-card>
    </div>

    <el-card class="rules-card">
      <template #header>
        <div class="card-header">
          <span>执行规则</span>
        </div>
      </template>
      <div class="rules-grid">
        <div class="rule-item">
          <span class="rule-number">1</span>
          <div class="rule-content">
            <div class="rule-title">按客户分配</div>
            <div class="rule-desc">一个人负责一个客户的所有银行卡（建设+工商）任务</div>
          </div>
        </div>
        <div class="rule-item">
          <span class="rule-number">2</span>
          <div class="rule-content">
            <div class="rule-title">金额限制</div>
            <div class="rule-desc">每人每次最低分配 ¥2000，每日累计最高 ¥20000</div>
          </div>
        </div>
        <div class="rule-item">
          <span class="rule-number">3</span>
          <div class="rule-content">
            <div class="rule-title">金额格式</div>
            <div class="rule-desc">金额不能以"00"结尾（个位数和十位数都不能为0）</div>
          </div>
        </div>
        <div class="rule-item">
          <span class="rule-number">4</span>
          <div class="rule-content">
            <div class="rule-title">连续分配限制</div>
            <div class="rule-desc">同一个人给同一个客户连续分配2天后，第3天自动跳过</div>
          </div>
        </div>
        <div class="rule-item">
          <span class="rule-number">5</span>
          <div class="rule-content">
            <div class="rule-title">客户数量限制</div>
            <div class="rule-desc">一个人每天最多接2个不同客户的任务</div>
          </div>
        </div>
        <div class="rule-item">
          <span class="rule-number">6</span>
          <div class="rule-content">
            <div class="rule-title">强制分配</div>
            <div class="rule-desc">当没有符合条件的人员时，可以强制分配</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const formRef = ref(null)
const customerList = ref([])
const bankList = ref([])
const personList = ref([])
const unselectedPersonIds = ref(new Set())
const personStatusList = ref([])
const personStatusByCard = ref([])

const skippedPersonCount = computed(() => {
  return personStatusList.value.filter(s => s.status === 'blocked').length
})

const availablePersonCount = computed(() => {
  return personStatusList.value.filter(s => s.status === 'available').length
})

const participatingPersonCount = computed(() => {
  const excluded = unselectedPersonIds.value.size
  const skipped = skippedPersonCount.value
  return personList.value.length - excluded - skipped
})

const creating = ref(false)

const taskForm = ref({
  customer_id: '',
  total_amount: 30000,
  task_date: new Date().toISOString().slice(0, 10),
  alloc_min: 2000,
  alloc_max: 20000,
  remark: ''
})

const allocationResult = ref(null)
const allocationDetails = ref([])

const rules = {
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  total_amount: [{ required: true, message: '请输入转账金额', trigger: 'blur' }]
}

onMounted(async () => {
  await Promise.all([loadCustomers(), loadPersons(), loadPersonStatusByCard()])
})

async function loadCustomers() {
  try {
    const res = await axios.get('/api/customer/list')
    customerList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

function togglePerson(personId) {
  if (unselectedPersonIds.value.has(personId)) {
    unselectedPersonIds.value.delete(personId)
  } else {
    unselectedPersonIds.value.add(personId)
  }
}

async function loadPersons() {
  try {
    const res = await axios.get('/api/person/list')
    personList.value = res.data.data || []
    unselectedPersonIds.value = new Set()
  } catch (e) {
    console.error(e)
  }
}

function onCustomerChange() {
  checkPersonStatus()
}

async function checkPersonStatus() {
  if (!taskForm.value.customer_id) {
    personStatusList.value = []
    return
  }
  
  try {
    const res = await axios.post('/api/task/check-person-status', {
      customer_id: taskForm.value.customer_id,
      task_date: taskForm.value.task_date
    })
    personStatusList.value = res.data.data || []
  } catch (e) {
    console.error(e)
    personStatusList.value = []
  }
}

async function loadPersonStatusByCard() {
  try {
    const res = await axios.get('/api/task/person-status-by-card', {
      params: { task_date: taskForm.value.task_date }
    })
    personStatusByCard.value = res.data.data || []
  } catch (e) {
    console.error(e)
    personStatusByCard.value = []
  }
}

async function createTask(forceAllocate = false) {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
  } catch (e) {
    return
  }

  creating.value = true
  try {
    const data = {
      ...taskForm.value,
      excluded_person_ids: Array.from(unselectedPersonIds.value),
      alloc_min: taskForm.value.alloc_min,
      alloc_max: taskForm.value.alloc_max,
      force_allocate: forceAllocate
    }
    const res = await axios.post('/api/task/create', data)
    
    allocationResult.value = res.data.data
    if (res.data.data && res.data.data.task_id) {
      const detailRes = await axios.get(`/api/task-detail/list/${res.data.data.task_id}`)
      allocationDetails.value = detailRes.data.data || []
    } else if (res.data.data && res.data.data.preview) {
      allocationDetails.value = res.data.data.preview
    }

    ElMessage.success(`${res.data.message}`)
    
    // 刷新人员状态
    loadPersonStatusByCard()
  } catch (e) {
    const errData = e.response?.data?.data
    if (errData) {
      allocationResult.value = errData
      allocationDetails.value = errData.preview || []
    }
    const msg = e.response?.data?.message || '创建失败'
    ElMessage.error({ message: msg, duration: 8000, showClose: true })
  } finally {
    creating.value = false
  }
}

function resetForm() {
  taskForm.value = {
    customer_id: '',
    bank_id: '',
    total_amount: 30000,
    task_date: new Date().toISOString().slice(0, 10),
    remark: ''
  }
  allocationResult.value = null
  allocationDetails.value = []
}

function getPersonNameByCode(personCode) {
  const person = personList.value.find(p => p.code === personCode)
  return person ? `${person.code} - ${person.name}` : personCode || '-'
}

function getPersonStatusTip(person) {
  const status = personStatusList.value.find(s => s.id === person.id)
  if (!status) return ''
  if (status.status === 'blocked') {
    return status.reason
  }
  return '可用'
}

function getPersonTagType(person) {
  if (unselectedPersonIds.value.has(person.id)) {
    return 'danger'
  }
  const status = personStatusList.value.find(s => s.id === person.id)
  if (status && status.status === 'blocked') {
    return 'warning'
  }
  return 'primary'
}

function getStatusText(status) {
  const map = {
    'pending': '待执行',
    'executing': '执行中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return map[status] || status
}
</script>

<style scoped>
.transfer-task {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.top-row {
  display: flex;
  gap: 20px;
}

.form-card {
  flex: 2;
}

.stats-card {
  flex: 1;
  min-width: 320px;
}

.middle-row {
  display: flex;
  gap: 20px;
}

.person-status-card {
  flex: 2;
}

.preview-card {
  flex: 1;
  min-width: 360px;
}

.rules-card {
  margin-top: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.person-status-container {
  max-height: 500px;
  overflow-y: auto;
}

.no-data-tip {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 14px;
}

.customer-info {
  margin-bottom: 15px;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.customer-name {
  font-size: 18px;
  font-weight: bold;
}

.customer-desc {
  font-size: 13px;
  color: #999;
}

.persons-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.persons-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.persons-label {
  font-size: 13px;
  min-width: 80px;
  flex-shrink: 0;
  line-height: 24px;
  font-weight: 500;
}

.persons-label.available {
  color: #67c23a;
}

.persons-label.blocked {
  color: #f56c6c;
}

.tags-group {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  flex: 1;
}

.no-data {
  color: #c0c4cc;
  font-size: 13px;
}

.person-tag {
  margin: 0;
}

.person-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.clickable-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.clickable-tag:hover {
  transform: scale(1.05);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.rule-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
}

.rule-content {
  flex: 1;
}

.rule-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.rule-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.stat-item {
  text-align: center;
  padding: 10px 6px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #606266;
}

.stat-value.available {
  color: #67c23a;
}

.stat-value.participating {
  color: #409eff;
}

.stat-value.excluded {
  color: #f56c6c;
}

.stat-value.skipped {
  color: #e6a23c;
}

.stat-value.amount {
  color: #409eff;
  font-size: 18px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.allocation-preview h4 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}
</style>