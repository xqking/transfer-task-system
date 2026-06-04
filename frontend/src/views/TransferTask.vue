<template>
  <div class="transfer-task">
    <div class="main-layout">
      <div class="left-column">
        <el-card class="main-card">
          <template #header>
            <div class="card-header">
              <span>创建转账任务</span>
            </div>
          </template>

          <el-form :model="taskForm" label-width="120px" :rules="rules" ref="formRef">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="任务名称" prop="task_name">
                  <el-input v-model="taskForm.task_name" placeholder="如：张三建设银行转账" />
                </el-form-item>
              </el-col>
            </el-row>

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
                <el-form-item label="选择银行" prop="bank_id">
                  <el-select 
                    v-model="taskForm.bank_id" 
                    placeholder="请选择银行" 
                    style="width: 100%;"
                    @change="updateTaskName"
                  >
                    <el-option 
                      v-for="b in bankList" 
                      :key="b.id" 
                      :label="b.name" 
                      :value="b.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="单日所需金额" prop="total_amount">
                  <el-input-number 
                    v-model="taskForm.total_amount" 
                    :min="2000" 
                    :step="1000"
                    :precision="0"
                    :value-on-clear="30000"
                    style="width: 100%;"
                    @change="updateTaskName"
                  />
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
                    @change="updateTaskName"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-button type="primary" @click="createTask" :loading="creating" size="large">
                创建并智能分配
              </el-button>
              <el-button @click="resetForm" size="large">重置</el-button>
            </el-form-item>
          </el-form>

          <el-divider />

          <div class="allocation-preview" v-if="allocationResult">
            <h4>分配预览</h4>
            <el-alert 
              :title="`共分配 ${allocationResult.allocated_count} 条任务，剩余 ¥${Math.round(allocationResult.remaining_amount || 0)} 未分配`" 
              :type="allocationResult.remaining_amount > 0 ? 'warning' : 'success'"
              show-icon
              :closable="false"
              style="margin-bottom: 15px;"
            />
            
            <el-table :data="allocationDetails" max-height="300" size="small">
              <el-table-column prop="person_code" label="人员" width="80" />
              <el-table-column prop="task_date" label="日期" width="120" />
              <el-table-column prop="amount" label="金额" width="100">
                <template #default="{ row }">
                  <span style="color: #409eff; font-weight: bold;">¥{{ Math.round(row.amount) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="card_no" label="卡号" width="120">
                <template #default="{ row }">
                  ****{{ row.card_no }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </div>

      <div class="right-column">
        <el-card class="info-card">
          <template #header>
            <span>可用人员 ({{ personList.length }}人)</span>
          </template>
          <div class="person-list">
            <el-tag 
              v-for="p in personList" 
              :key="p.id"
              :type="unselectedPersonIds.has(p.id) ? 'danger' : 'primary'" 
              effect="plain"
              @click="togglePerson(p.id)"
              class="clickable-tag person-tag"
            >{{ p.code }} - {{ p.name }}</el-tag>
          </div>
        </el-card>

        <el-card class="stats-card" style="margin-top: 20px;">
          <template #header>
            <span>任务统计</span>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ personList.length }}</div>
              <div class="stat-label">总人数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value participating">{{ personList.length - unselectedPersonIds.size }}</div>
              <div class="stat-label">参加人数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value excluded">{{ unselectedPersonIds.size }}</div>
              <div class="stat-label">排除人数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value amount">¥{{ taskForm.total_amount.toLocaleString() }}</div>
              <div class="stat-label">任务金额</div>
            </div>
          </div>
        </el-card>

      </div>
    </div>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>历史任务列表</span>
          <div>
            <el-button 
              type="success" 
              :disabled="selectedTasks.length === 0" 
              @click="batchComplete"
            >
              批量执行完成 ({{ selectedTasks.length }})
            </el-button>
            <el-button 
              type="danger" 
              :disabled="selectedTasks.length === 0" 
              @click="batchDelete"
              :icon="Delete"
            >
              批量删除 ({{ selectedTasks.length }})
            </el-button>
            <el-button @click="loadTaskList" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div v-for="(group, groupIndex) in groupedTasks" :key="group.customer_name" class="task-group">
        <div class="group-header" @click="toggleGroup(groupIndex)">
          <el-icon class="expand-icon" :class="{ expanded: !collapsedGroups[groupIndex] }">
            <ArrowRight />
          </el-icon>
          <span class="group-title">{{ group.customer_name }}</span>
          <span class="group-count">共 {{ group.tasks.length }} 个任务</span>
          <span class="group-total">总金额: ¥{{ group.totalAmount }}</span>
        </div>
        <div v-show="!collapsedGroups[groupIndex]" class="group-content">
          <el-table 
            :data="group.tasks" 
            stripe 
            row-key="id"
            :expand-row-keys="expandedRowKeys"
            @expand-change="(row, expandedRows) => handleExpandChange(row, expandedRows, groupIndex)"
            @selection-change="(selection) => handleSelectionChange(selection, groupIndex)"
          >
            <el-table-column type="selection" width="50" :reserve-selection="true" />
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="detail-expand">
                  <el-descriptions :column="3" border size="small" style="margin-bottom: 16px;">
                    <el-descriptions-item label="任务名称">{{ row.task_name }}</el-descriptions-item>
                    <el-descriptions-item label="客户">{{ row.customer_name }}</el-descriptions-item>
                    <el-descriptions-item label="银行">{{ row.bank_name }}</el-descriptions-item>
                    <el-descriptions-item label="总金额">¥{{ row.total_amount }}</el-descriptions-item>
                    <el-descriptions-item label="已转金额">¥{{ row.transferred_amount }}</el-descriptions-item>
                    <el-descriptions-item label="状态">
                      <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                  
                  <el-table :data="getTaskDetails(row.id)" stripe size="small" max-height="300">
                    <el-table-column prop="person_code" label="人员" width="150">
                      <template #default="{ row }">
                        {{ getPersonNameByCode(row.person_code) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="task_date" label="任务日期" width="120" />
                    <el-table-column prop="amount" label="金额" width="100">
                      <template #default="{ row }">
                        ¥{{ Math.round(row.amount) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="card_no" label="银行卡号" width="180" />
                    <el-table-column prop="bank_name" label="银行" width="100" />
                    <el-table-column prop="status" label="状态" width="100">
                      <template #default="{ row }">
                        <el-select 
                          v-model="row.status" 
                          size="small" 
                          @change="(val) => updateStatus(row.id, val)"
                        >
                          <el-option label="待执行" value="pending" />
                          <el-option label="已完成" value="completed" />
                          <el-option label="失败" value="failed" />
                        </el-select>
                      </template>
                    </el-table-column>
                    <el-table-column prop="execute_time" label="执行时间" width="160" />
                  </el-table>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="task_name" label="任务名称" min-width="180" />
            <el-table-column prop="bank_name" label="银行" width="100" />
            <el-table-column prop="total_amount" label="单日金额" width="110">
              <template #default="{ row }">
                ¥{{ row.total_amount }}
              </template>
            </el-table-column>
            <el-table-column prop="transferred_amount" label="已转金额" width="110">
              <template #default="{ row }">
                <span :style="{ color: row.transferred_amount >= row.total_amount ? '#67c23a' : '#e6a23c' }">
                  ¥{{ row.transferred_amount }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="detail_count" label="明细数" width="80" />
            <el-table-column label="操作" fixed="right" width="120">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="deleteTask(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Refresh, Delete, ArrowRight } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const formRef = ref(null)
const taskTableRef = ref(null)
const customerList = ref([])
const bankList = ref([])
const personList = ref([])
const unselectedPersonIds = ref(new Set())
const taskList = ref([])
const selectedTaskIds = ref(new Set())
const collapsedGroups = ref({})
const expandedRowKeys = ref([])
const taskDetailsMap = ref({})

const selectedTasks = computed(() => {
  const result = []
  const visited = new Set()
  groupedTasks.value.forEach(group => {
    group.tasks.forEach(task => {
      if (selectedTaskIds.value.has(task.id) && !visited.has(task.id)) {
        visited.add(task.id)
        result.push(task)
      }
    })
  })
  return result
})
const creating = ref(false)

const taskForm = ref({
  task_name: '',
  customer_id: '',
  bank_id: '',
  total_amount: 30000,
  task_date: new Date().toISOString().slice(0, 10),
  remark: ''
})

const allocationResult = ref(null)
const allocationDetails = ref([])

const rules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  bank_id: [{ required: true, message: '请选择银行', trigger: 'change' }],
  total_amount: [{ required: true, message: '请输入转账金额', trigger: 'blur' }]
}

onMounted(async () => {
  await Promise.all([loadCustomers(), loadBanks(), loadPersons(), loadTaskList()])
})

async function loadCustomers() {
  try {
    const res = await axios.get('/api/customer/list')
    customerList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

async function loadBanks() {
  try {
    const res = await axios.get('/api/customer/banks')
    bankList.value = res.data.data || []
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

async function loadTaskList() {
  try {
    const res = await axios.get('/api/task/list')
    taskList.value = res.data.data || []
    initCollapsedGroups()
  } catch (e) {
    console.error(e)
  }
}

function initCollapsedGroups() {
  const groups = {}
  const customerMap = {}
  taskList.value.forEach(task => {
    if (!customerMap[task.customer_name]) {
      customerMap[task.customer_name] = Object.keys(groups).length
      groups[Object.keys(groups).length] = true
    }
  })
  collapsedGroups.value = groups
}

const groupedTasks = computed(() => {
  const groups = {}
  taskList.value.forEach(task => {
    if (!groups[task.customer_name]) {
      groups[task.customer_name] = {
        customer_name: task.customer_name,
        tasks: [],
        totalAmount: 0
      }
    }
    groups[task.customer_name].tasks.push(task)
    groups[task.customer_name].totalAmount += task.total_amount
  })
  
  const result = Object.values(groups).sort((a, b) => b.totalAmount - a.totalAmount)
  
  result.forEach(group => {
    group.tasks.sort((a, b) => {
      const dateA = extractDate(a.task_name)
      const dateB = extractDate(b.task_name)
      return new Date(dateA) - new Date(dateB)
    })
  })
  
  return result
})

function extractDate(taskName) {
  const match = taskName.match(/(\d{4}-\d{2}-\d{2})/)
  return match ? match[1] : '1970-01-01'
}

function toggleGroup(index) {
  collapsedGroups.value[index] = !collapsedGroups.value[index]
}

function updateTaskName() {
  const customer = customerList.value.find(c => c.id === taskForm.value.customer_id)
  const bank = bankList.value.find(b => b.id === taskForm.value.bank_id)
  const date = taskForm.value.task_date
  
  let name = ''
  if (customer) {
    name += customer.name
  }
  if (bank) {
    name += `-${bank.name}`
  }
  if (taskForm.value.total_amount) {
    name += `-${taskForm.value.total_amount}`
  }
  if (date) {
    name += `-${date}`
  }
  
  taskForm.value.task_name = name
}

function onCustomerChange() {
  updateTaskName()
}

async function createTask() {
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
      excluded_person_ids: Array.from(unselectedPersonIds.value)
    }
    const res = await axios.post('/api/task/create', data)
    
    allocationResult.value = res.data.data
    if (res.data.data && res.data.data.task_id) {
      const detailRes = await axios.get(`/api/task-detail/list/${res.data.data.task_id}`)
      allocationDetails.value = detailRes.data.data || []
    }

    ElMessage.success(`任务创建成功！已分配 ${res.data.data.allocated_count} 条任务`)
    loadTaskList()
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
    task_name: '',
    customer_id: '',
    bank_id: '',
    total_amount: 30000,
    task_date: new Date().toISOString().slice(0, 10),
    remark: ''
  }
  allocationResult.value = null
  allocationDetails.value = []
}

async function handleExpandChange(row, expandedRows, groupIndex) {
  if (expandedRows.some(r => r.id === row.id)) {
    if (!taskDetailsMap.value[row.id]) {
      try {
        const detailRes = await axios.get(`/api/task-detail/list/${row.id}`)
        taskDetailsMap.value[row.id] = detailRes.data.data || []
      } catch (e) {
        console.error(e)
      }
    }
    expandedRowKeys.value = [...expandedRowKeys.value, row.id]
  } else {
    expandedRowKeys.value = expandedRowKeys.value.filter(id => id !== row.id)
  }
}

function getTaskDetails(taskId) {
  return taskDetailsMap.value[taskId] || []
}

async function deleteTask(id) {
  try {
    await ElMessageBox.confirm('确定要删除该任务吗？删除后不可恢复', '提示', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' })
    const res = await axios.delete(`/api/task/delete/${id}`)
    if (res.data.code === 200) {
      ElMessage.success('删除成功')
      loadTaskList()
    } else {
      ElMessage.error(res.data.message || '删除失败')
    }
  } catch (e) {
    if (e === 'cancel' || e?.action === 'cancel') return
  }
}

function handleSelectionChange(selection, groupIndex) {
  const selectedIds = new Set(selection.map(s => s.id))
  
  groupedTasks.value[groupIndex]?.tasks.forEach(task => {
    if (selectedIds.has(task.id)) {
      selectedTaskIds.value.add(task.id)
    } else {
      selectedTaskIds.value.delete(task.id)
    }
  })
}

async function batchComplete() {
  if (selectedTasks.value.length === 0) return
  
  const ids = selectedTasks.value.map(t => t.id)
  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${ids.length} 个任务标记为完成吗？`,
      '批量执行完成',
      { type: 'info', confirmButtonText: `确定完成(${ids.length}个)`, cancelButtonText: '取消' }
    )
    
    const res = await axios.post('/api/task/batch-complete', { ids })
    if (res.data.code === 200) {
      ElMessage.success(`成功将 ${res.data.data.completed_count} 个任务标记为完成`)
      selectedTaskIds.value.clear()
      loadTaskList()
    } else {
      ElMessage.error(res.data.message || '批量执行失败')
    }
  } catch (e) {
    if (e === 'cancel' || e?.action === 'cancel') return
  }
}

async function batchDelete() {
  if (selectedTasks.value.length === 0) return
  
  const ids = selectedTasks.value.map(t => t.id)
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${ids.length} 个任务吗？删除后不可恢复`,
      '批量删除',
      { type: 'warning', confirmButtonText: `确定删除(${ids.length}个)`, cancelButtonText: '取消' }
    )
    
    const res = await axios.post('/api/task/batch-delete', { ids })
    if (res.data.code === 200) {
      ElMessage.success(`成功删除 ${res.data.data.deleted_count} 个任务`)
      selectedTaskIds.value.clear()
      loadTaskList()
    } else {
      ElMessage.error(res.data.message || '批量删除失败')
    }
  } catch (e) {
    if (e === 'cancel' || e?.action === 'cancel') return
  }
}

async function updateStatus(detailId, status) {
  try {
    await axios.put(`/api/task-detail/update-status/${detailId}`, { status })
    ElMessage.success('状态更新成功')
    loadTaskList()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

function getStatusType(status) {
  const map = {
    'pending': 'warning',
    'executing': 'primary',
    'completed': 'success',
    'cancelled': 'info'
  }
  return map[status] || 'info'
}

function getPersonNameByCode(personCode) {
  const person = personList.value.find(p => p.code === personCode)
  return person ? `${person.code} - ${person.name}` : personCode || '-'
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
.main-layout {
  display: flex;
  gap: 20px;
}

.left-column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.left-column .main-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.left-column .main-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.left-column .main-card :deep(.el-card__body) > *:last-child {
  margin-top: auto;
}

.right-column {
  width: 48%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-column .info-card,
.right-column .stats-card {
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card {
  height: fit-content;
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

.stats-card {
  height: fit-content;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.stat-item {
  text-align: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #606266;
}

.stat-value.participating {
  color: #67c23a;
}

.stat-value.excluded {
  color: #f56c6c;
}

.stat-value.amount {
  color: #409eff;
  font-size: 20px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.task-group {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  cursor: pointer;
  user-select: none;
}

.group-header:hover {
  background: #ecf5ff;
}

.expand-icon {
  transition: transform 0.3s;
  color: #909399;
  font-size: 14px;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.group-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.group-count {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.group-total {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
  margin-left: 16px;
}

.group-content {
  border-top: 1px solid #e4e7ed;
}

.detail-expand {
  padding: 20px;
  background: #fafafa;
}
</style>