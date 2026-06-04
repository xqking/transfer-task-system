<template>
  <div class="history-task-container">
    <div class="page-header">
      <h2>历史任务</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAdd">新增任务</el-button>
        <el-button type="danger" :disabled="!multipleSelection.length" @click="handleBatchDelete">
          批量删除 ({{ multipleSelection.length }})
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-select v-model="searchPersonId" placeholder="选择人员" clearable class="search-select">
        <el-option v-for="person in personList" :key="person.id" :label="`${person.code} - ${person.name}`" :value="person.id" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" class="date-picker" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
      <el-select v-model="searchStatus" placeholder="任务状态" clearable class="status-select">
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
        <el-option label="待执行" value="pending" />
      </el-select>
      <el-button type="primary" @click="loadHistoryTasks">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <el-table 
      :data="historyTasks" 
      border 
      style="width: 100%" 
      :loading="loading"
      row-key="id"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" />
      <el-table-column prop="person_code" label="人员编号" width="120">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">{{ row.person_code }}</span>
          <el-select v-else v-model="row.person_code" placeholder="选择人员" size="small" style="width: 100%">
            <el-option v-for="person in personList" :key="person.code" :label="`${person.code} - ${person.name}`" :value="person.code" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" width="100">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">{{ row.customer_name }}</span>
          <el-input v-else v-model="row.customer_name" size="small" />
        </template>
      </el-table-column>
      <el-table-column prop="task_date" label="任务日期" width="120">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">{{ row.task_date }}</span>
          <el-date-picker v-else v-model="row.task_date" type="date" placeholder="选择日期" size="small" style="width: 100%" value-format="YYYY-MM-DD" />
        </template>
      </el-table-column>
      <el-table-column prop="bank_name" label="银行" width="120">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">{{ row.bank_name }}</span>
          <el-input v-else v-model="row.bank_name" size="small" />
        </template>
      </el-table-column>
      <el-table-column prop="wechat_amount" label="微信金额" width="130">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">¥{{ row.wechat_amount }}</span>
          <el-input-number v-else v-model="row.wechat_amount" :min="0" size="small" style="width: 100%" />
        </template>
      </el-table-column>
      <el-table-column prop="alipay_amount" label="支付宝金额" width="130">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">¥{{ row.alipay_amount }}</span>
          <el-input-number v-else v-model="row.alipay_amount" :min="0" size="small" style="width: 100%" />
        </template>
      </el-table-column>
      <el-table-column prop="amount" label="总金额" width="100">
        <template #default="{ row }">
          <span :style="{ fontWeight: 'bold' }">¥{{ row.amount }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <span v-if="!editingRows.has(row.id)">
            <span :class="['status-tag', getStatusClass(row.status)]">
              {{ getStatusText(row.status) }}
            </span>
          </span>
          <el-select v-else v-model="row.status" size="small" style="width: 100%">
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="待执行" value="pending" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="操作" fixed="right" width="180">
        <template #default="{ row }">
          <template v-if="editingRows.has(row.id)">
            <el-button type="success" size="small" @click="handleSave(row)">保存</el-button>
            <el-button size="small" @click="handleCancel(row)">取消</el-button>
          </template>
          <template v-else>
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="historyTasks.length === 0 && !loading" class="empty-tip">
      暂无历史任务数据
    </div>

    <el-dialog v-model="addDialogVisible" title="新增任务" width="500px">
      <el-form :model="addForm" label-width="120px">
        <el-form-item label="人员">
          <el-select v-model="addForm.person_code" placeholder="选择人员" style="width: 100%">
            <el-option v-for="person in personList" :key="person.code" :label="`${person.code} - ${person.name}`" :value="person.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户">
          <el-input v-model="addForm.customer_name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="任务日期">
          <el-date-picker v-model="addForm.task_date" type="date" placeholder="选择日期" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="银行">
          <el-input v-model="addForm.bank_name" placeholder="请输入银行名称" />
        </el-form-item>
        <el-form-item label="微信金额">
          <el-input-number v-model="addForm.wechat_amount" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="支付宝金额">
          <el-input-number v-model="addForm.alipay_amount" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="addForm.status" placeholder="选择状态" style="width: 100%">
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="待执行" value="pending" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddConfirm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const loading = ref(false)
const searchPersonId = ref('')
const searchStatus = ref('')
const dateRange = ref([])
const personList = ref([])
const historyTasks = ref([])
const editingRows = ref(new Set())
const multipleSelection = ref([])
const originalData = ref({})
const addDialogVisible = ref(false)

const addForm = ref({
  person_code: '',
  customer_name: '',
  task_date: '',
  bank_name: '',
  wechat_amount: 0,
  alipay_amount: 0,
  status: 'pending'
})

function loadPersonList() {
  axios.get('/api/person/list').then(res => {
    personList.value = res.data.data || []
  }).catch(e => {
    console.error(e)
  })
}

function getPersonNameByCode(code) {
  const person = personList.value.find(p => p.code === code)
  return person ? person.name : code || '-'
}

const splitCache = {}
const splitVersion = 'v2'

function avoidRoundThousand(num) {
  const remainder = num % 1000
  if (remainder === 0) {
    const offset = ((num / 1000) % 9 + 1) * 100 + Math.floor(Math.random() * 90)
    return num + offset > 9999 ? num - 500 : num + offset
  }
  return num
}

function getSplitAmount(task, part) {
  const key = `${splitVersion}_${task.id}_${task.amount}`
  if (!splitCache[key]) {
    const total = Math.round(task.amount)
    
    const str = `${task.id}-${task.customer_name}-${task.bank_name}-${task.task_date}`
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    
    const ratio1 = Math.abs(hash % 1000) / 1000 * 0.5 + 0.25
    const ratio2 = Math.abs((hash >> 8) % 100) / 100 * 0.3 + 0.35
    
    const ratio = (ratio1 + ratio2) / 2
    let first = Math.max(1000, Math.round(total * ratio))
    first = avoidRoundThousand(first)
    
    let second = total - first
    second = avoidRoundThousand(second)
    
    if (second < 1000) {
      second = 1000
      first = total - second
    }
    if (first < 1000) {
      first = 1000
      second = total - first
    }
    
    splitCache[key] = [first, second]
  }
  return splitCache[key][part - 1]
}

async function loadHistoryTasks() {
  loading.value = true
  try {
    // 先获取所有任务和任务详情，然后组合数据
    const [taskRes, detailRes] = await Promise.all([
      axios.get('/api/task/list'),
      axios.get('/api/task-detail/list') // 假设存在这个接口获取所有详情
    ])
    
    const tasks = taskRes.data.data || []
    const details = detailRes.data.data || []
    
    // 将详情展开为历史任务列表
    const result = []
    details.forEach(detail => {
      const task = tasks.find(t => t.id === detail.task_id)
      if (task) {
        const taskForSplit = {
          id: detail.id,
          amount: detail.amount,
          customer_name: task.customer_name,
          bank_name: detail.bank_name,
          task_date: detail.task_date
        }
        const wechat = getSplitAmount(taskForSplit, 1)
        const alipay = getSplitAmount(taskForSplit, 2)
        
        result.push({
          id: detail.id,
          task_id: task.id,
          person_code: detail.person_code,
          person_name: getPersonNameByCode(detail.person_code),
          customer_name: task.customer_name,
          task_date: detail.task_date,
          bank_name: detail.bank_name,
          wechat_amount: wechat,
          alipay_amount: alipay,
          amount: detail.amount,
          status: detail.status,
          create_time: detail.execute_time || ''
        })
      }
    })
    
    let filtered = result
    
    if (searchPersonId.value) {
      const person = personList.value.find(p => p.id === parseInt(searchPersonId.value))
      if (person) {
        filtered = filtered.filter(t => t.person_code === person.code)
      }
    }

    if (searchStatus.value) {
      filtered = filtered.filter(t => t.status === searchStatus.value)
    }

    if (dateRange.value && dateRange.value.length === 2) {
      const startDate = new Date(dateRange.value[0])
      const endDate = new Date(dateRange.value[1])
      // 设置结束日期的时间为23:59:59，确保包含整天
      endDate.setHours(23, 59, 59, 999)
      filtered = filtered.filter(t => {
        const taskDate = new Date(t.task_date)
        return taskDate >= startDate && taskDate <= endDate
      })
    }

    // 按日期升序排列
    filtered.sort((a, b) => new Date(a.task_date) - new Date(b.task_date))

    historyTasks.value = filtered
  } catch (error) {
    console.error(error)
    ElMessage.error('加载历史任务失败')
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchPersonId.value = ''
  searchStatus.value = ''
  dateRange.value = []
  loadHistoryTasks()
}

function handleSelectionChange(selection) {
  multipleSelection.value = selection
}

function handleEdit(row) {
  originalData.value[row.id] = { ...row }
  editingRows.value.add(row.id)
}

function handleSave(row) {
  // 如果用户修改了总金额，重新分配
  if (row.wechat_amount + row.alipay_amount !== row.amount) {
    const taskForSplit = {
      id: row.id,
      amount: row.amount,
      customer_name: row.customer_name,
      bank_name: row.bank_name,
      task_date: row.task_date
    }
    row.wechat_amount = getSplitAmount(taskForSplit, 1)
    row.alipay_amount = getSplitAmount(taskForSplit, 2)
  } else if (row.wechat_amount + row.alipay_amount === row.amount) {
    // 用户自定义了微信和支付宝金额，保持不变
  } else {
    // 确保总金额正确
    row.amount = row.wechat_amount + row.alipay_amount
  }
  
  const person = personList.value.find(p => p.code === row.person_code)
  if (person) {
    row.person_name = person.name
  }
  editingRows.value.delete(row.id)
  delete originalData.value[row.id]
  ElMessage.success('保存成功')
}

function handleCancel(row) {
  if (originalData.value[row.id]) {
    Object.assign(row, originalData.value[row.id])
    delete originalData.value[row.id]
  }
  editingRows.value.delete(row.id)
}

function handleDelete(row) {
  ElMessageBox.confirm('确定要删除这条任务吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const index = historyTasks.value.findIndex(t => t.id === row.id)
    if (index > -1) {
      historyTasks.value.splice(index, 1)
      ElMessage.success('删除成功')
    }
  }).catch(() => {})
}

function handleBatchDelete() {
  if (!multipleSelection.value.length) return
  
  ElMessageBox.confirm(`确定要删除选中的 ${multipleSelection.value.length} 条任务吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const ids = multipleSelection.value.map(t => t.id)
    historyTasks.value = historyTasks.value.filter(t => !ids.includes(t.id))
    multipleSelection.value = []
    ElMessage.success('批量删除成功')
  }).catch(() => {})
}

function handleAdd() {
  addForm.value = {
    person_code: '',
    customer_name: '',
    task_date: '',
    bank_name: '',
    wechat_amount: 0,
    alipay_amount: 0,
    status: 'pending'
  }
  addDialogVisible.value = true
}

function handleAddConfirm() {
  if (!addForm.value.person_code) {
    ElMessage.warning('请选择人员')
    return
  }
  if (!addForm.value.customer_name) {
    ElMessage.warning('请输入客户名称')
    return
  }
  if (!addForm.value.task_date) {
    ElMessage.warning('请选择任务日期')
    return
  }
  if (!addForm.value.bank_name) {
    ElMessage.warning('请输入银行名称')
    return
  }

  const person = personList.value.find(p => p.code === addForm.value.person_code)
  
  // 使用金额分配逻辑
  const taskId = Date.now()
  const taskForSplit = {
    id: taskId,
    amount: addForm.value.wechat_amount + addForm.value.alipay_amount || 4000, // 默认4000
    customer_name: addForm.value.customer_name,
    bank_name: addForm.value.bank_name,
    task_date: addForm.value.task_date
  }
  
  // 如果用户没有填写金额，使用自动分配
  let wechat, alipay, amount
  if (addForm.value.wechat_amount === 0 && addForm.value.alipay_amount === 0) {
    amount = 4000 // 默认金额
    wechat = getSplitAmount({ ...taskForSplit, amount }, 1)
    alipay = getSplitAmount({ ...taskForSplit, amount }, 2)
  } else {
    wechat = addForm.value.wechat_amount
    alipay = addForm.value.alipay_amount
    amount = wechat + alipay
  }
  
  const newTask = {
    id: taskId,
    person_code: addForm.value.person_code,
    customer_name: addForm.value.customer_name,
    task_date: addForm.value.task_date,
    bank_name: addForm.value.bank_name,
    wechat_amount: wechat,
    alipay_amount: alipay,
    amount: amount,
    status: addForm.value.status,
    person_name: person ? person.name : '',
    create_time: new Date().toLocaleString()
  }
  
  historyTasks.value.unshift(newTask)
  addDialogVisible.value = false
  ElMessage.success('新增成功')
}

function getStatusClass(status) {
  switch (status) {
    case 'completed': return 'status-completed'
    case 'failed': return 'status-failed'
    default: return 'status-pending'
  }
}

function getStatusText(status) {
  switch (status) {
    case 'completed': return '已完成'
    case 'failed': return '失败'
    default: return '待执行'
  }
}

onMounted(() => {
  loadPersonList()
  loadHistoryTasks()
})
</script>

<style scoped>
.history-task-container {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e4e7ed;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}

.search-select {
  width: 180px;
}

.date-picker {
  width: 280px;
}

.status-select {
  width: 120px;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.status-completed {
  background: #e1f3d8;
  color: #67c23a;
}

.status-failed {
  background: #fde2e2;
  color: #f56c6c;
}

.status-pending {
  background: #fff7e6;
  color: #e6a23c;
}

.empty-tip {
  text-align: center;
  padding: 40px;
  color: #909399;
}
</style>
