<template>
  <div class="home-container">
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon total-icon">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalTasks }}</span>
            <span class="stat-label">总任务数</span>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon completed-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ completedTasks }}</span>
            <span class="stat-label">已完成</span>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon pending-icon">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ pendingTasks }}</span>
            <span class="stat-label">待执行</span>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon failed-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ failedTasks }}</span>
            <span class="stat-label">失败</span>
          </div>
        </div>
      </el-card>
    </div>

    <el-card class="main-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">任务列表</span>
          <div class="header-actions">
            <el-button type="warning" @click="exportImage" :icon="Document">导出图片</el-button>
            <el-button type="primary" @click="refreshData" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div class="filter-bar">
        <div class="filter-group">
          <span class="filter-label">客户：</span>
          <el-select
            v-model="selectedCustomerId"
            clearable
            placeholder="全部客户"
            style="width: 160px;"
            @change="loadCalendarData"
          >
            <el-option
              v-for="c in customerList"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            >
              <span class="customer-option">
                <i class="option-dot" :style="{ backgroundColor: c.color }" />
                {{ c.name }}
              </span>
            </el-option>
          </el-select>
        </div>

        <div class="filter-group">
          <span class="filter-label">银行：</span>
          <el-select
            v-model="selectedBankId"
            clearable
            placeholder="全部银行"
            style="width: 140px;"
            @change="loadCalendarData"
          >
            <el-option
              v-for="b in bankList"
              :key="b.id"
              :label="b.name"
              :value="b.id"
            />
          </el-select>
        </div>

        <div class="filter-group">
          <span class="filter-label">人员：</span>
          <el-select
            v-model="selectedPersonId"
            clearable
            placeholder="全部人员"
            style="width: 160px;"
            @change="loadCalendarData"
          >
            <el-option
              v-for="p in personList"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </div>

        <div class="filter-group">
          <span class="filter-label">状态：</span>
          <el-select
            v-model="selectedStatus"
            clearable
            placeholder="全部状态"
            style="width: 120px;"
            @change="loadCalendarData"
          >
            <el-option label="已完成" value="completed" />
            <el-option label="待执行" value="pending" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>

        <div class="filter-group">
          <span class="filter-label">日期范围：</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadCalendarData"
          />
        </div>
      </div>

      <div class="action-bar">
        <span class="selected-count">已选择 {{ selectedRows.length }} 条</span>
        <el-button type="primary" @click="showAddTaskDialog" :icon="Plus">新建任务</el-button>
        <el-button type="success" @click="batchUpdateStatus('completed')" :disabled="selectedRows.length === 0">批量已完成</el-button>
        <el-button type="warning" @click="batchUpdateStatus('pending')" :disabled="selectedRows.length === 0">批量待完成</el-button>
        <el-button type="danger" @click="batchUpdateStatus('failed')" :disabled="selectedRows.length === 0">批量失败</el-button>
        <el-button class="btn-delete" @click="batchDelete" :disabled="selectedRows.length === 0" :icon="Delete">批量删除</el-button>
        <el-button type="info" @click="exportExcel" :icon="Document">导出Excel</el-button>
      </div>

      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value">{{ formatAmount(dayTotalAmount) }}</span>
          <span class="stat-label">当日总金额</span>
        </div>
        <div class="stat-item completed">
          <span class="stat-value">{{ formatAmount(dayCompletedAmount) }}</span>
          <span class="stat-label">已完成金额</span>
        </div>
        <div class="stat-item pending">
          <span class="stat-value">{{ formatAmount(dayTotalAmount - dayCompletedAmount - dayFailedAmount) }}</span>
          <span class="stat-label">待完成金额</span>
        </div>
        <div class="stat-item failed">
          <span class="stat-value">{{ formatAmount(dayFailedAmount) }}</span>
          <span class="stat-label">失败金额</span>
        </div>
      </div>

      <el-table
        :data="taskTableData"
        stripe
        border
        style="width: 100%;"
        row-key="id"
        fit
        @selection-change="handleSelectionChange"
        cell-class-name="table-cell-center"
      >
        <el-table-column type="selection" width="50" />


        <el-table-column prop="person_name" label="人员" width="120" />
        <el-table-column prop="customer_name" label="客户" width="100">
          <template #default="{ row }">
            <span class="customer-tag" :style="{ color: getCustomerColor(row.customer_name) }">
              {{ row.customer_name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="bank_name" label="银行" width="100">
          <template #default="{ row }">
            <el-tag :type="getBankTagType(row.bank_name)" size="small">
              {{ row.bank_name.replace('银行', '') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="task_date" label="任务日期" width="120" />
        <el-table-column prop="amount" label="总金额" width="120">
          <template #default="{ row }">
            <span class="amount-text">¥{{ Math.round(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="微信" width="100">
          <template #default="{ row }">
            <span class="wechat-amount">¥{{ ((row.wechat_amount || 0) + (row.alipay_amount || 0) > 0 && (row.wechat_amount || 0) + (row.alipay_amount || 0) === Math.round(row.amount)) ? (row.wechat_amount || 0) : getSplitAmount(row, 1) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="支付宝" width="100">
          <template #default="{ row }">
            <span class="alipay-amount">¥{{ ((row.wechat_amount || 0) + (row.alipay_amount || 0) > 0 && (row.wechat_amount || 0) + (row.alipay_amount || 0) === Math.round(row.amount)) ? (row.alipay_amount || 0) : (Math.round(row.amount) - getSplitAmount(row, 1)) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.remark && row.remark !== '-' ? 'primary' : 'success'" size="small">
              {{ row.remark && row.remark !== '-' ? '手动' : '自动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="200" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)" :icon="Edit">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div id="export-cards" class="export-cards-container" style="display: none;">
      <template v-for="(personTasks, personCode) in groupedTasks" :key="personCode">
        <div class="person-header">
          <span class="person-title">{{ personCode }} - {{ getPersonName(personCode) }}</span>
          <span class="task-count">共 {{ personTasks.length }} 个任务</span>
        </div>
        <div class="cards-grid">
          <div 
            v-for="task in personTasks" 
            :key="task.id" 
            class="task-card"
            :class="getBankCardClass(task.bank_name)"
          >
            <div class="card-left">
              <div class="qr-container" v-if="getQRCode(task)">
                <img :src="getQRCodeUrl(getQRCode(task))" alt="收款码" class="qr-code" />
              </div>
              <div class="qr-placeholder" v-else>
                <span>暂无收款码</span>
              </div>
            </div>
            <div class="card-right">
              <div class="card-info">
                <div class="info-group">
                  <div class="info-row">
                    <span class="info-label">客户</span>
                    <span class="info-value customer-value" :style="{ color: getCustomerColor(task.customer_name) }">{{ task.customer_name }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">银行</span>
                    <span class="info-value">{{ task.bank_name.replace('银行', '') }}</span>
                  </div>
                </div>
                <div class="info-divider"></div>
                <div class="info-group amounts">
                  <div class="info-row">
                    <span class="info-label">微信</span>
                    <span class="info-value wechat-value">¥{{ ((task.wechat_amount || 0) + (task.alipay_amount || 0) > 0 && (task.wechat_amount || 0) + (task.alipay_amount || 0) === Math.round(task.amount)) ? (task.wechat_amount || 0) : getSplitAmount(task, 1) }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">支付宝</span>
                    <span class="info-value alipay-value">¥{{ ((task.wechat_amount || 0) + (task.alipay_amount || 0) > 0 && (task.wechat_amount || 0) + (task.alipay_amount || 0) === Math.round(task.amount)) ? (task.alipay_amount || 0) : (Math.round(task.amount) - getSplitAmount(task, 1)) }}</span>
                  </div>
                </div>
                <div class="info-divider"></div>
                <div class="info-group">
                  <div class="info-row">
                    <span class="info-label">日期</span>
                    <span class="info-value">{{ task.task_date }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="summary-row">
          <div class="summary-item">
            <span class="summary-label">微信合计：</span>
            <span class="summary-value wechat-summary">¥{{ getPersonWechatTotal(personTasks) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">支付宝合计：</span>
            <span class="summary-value alipay-summary">¥{{ getPersonAlipayTotal(personTasks) }}</span>
          </div>
          <div class="summary-item total">
            <span class="summary-label">总计：</span>
            <span class="summary-value total-summary">¥{{ getPersonTotal(personTasks) }}</span>
          </div>
        </div>
      </template>
    </div>

    <el-dialog v-model="qrPreviewVisible" title="收款码" width="400px">
      <div class="qr-preview-container">
        <img :src="previewQRUrl" alt="收款码" class="qr-preview-image" />
      </div>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑任务" width="500px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="人员">
          <el-select v-model="editForm.person_id" style="width: 100%;">
            <el-option v-for="p in personList" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户">
          <el-select v-model="editForm.customer_id" style="width: 100%;">
            <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="银行">
          <el-select v-model="editForm.bank_id" style="width: 100%;">
            <el-option v-for="b in bankList" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="总金额">
          <el-input :model-value="editForm.wechat_amount + editForm.alipay_amount" disabled style="width: 100%; text-align: center;" />
        </el-form-item>
        <el-form-item label="微信金额">
          <el-input-number v-model="editForm.wechat_amount" :min="0" controls-position="right" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="支付宝金额">
          <el-input-number v-model="editForm.alipay_amount" :min="0" controls-position="right" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="任务日期">
          <el-date-picker v-model="editForm.task_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%;">
            <el-option label="待执行" value="pending" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="addTaskDialogVisible" title="新建任务" width="500px">
      <el-form :model="addTaskForm" label-width="100px">
        <el-form-item label="人员">
          <el-select v-model="addTaskForm.person_id" style="width: 100%;">
            <el-option v-for="p in personList" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户">
          <el-select v-model="addTaskForm.customer_id" style="width: 100%;">
            <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="银行">
          <el-select v-model="addTaskForm.bank_id" style="width: 100%;">
            <el-option v-for="b in bankList" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="总金额">
          <el-input :model-value="addTaskForm.wechat_amount + addTaskForm.alipay_amount" disabled style="width: 100%; text-align: center;" />
        </el-form-item>
        <el-form-item label="微信金额">
          <el-input-number v-model="addTaskForm.wechat_amount" :min="0" controls-position="right" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="支付宝金额">
          <el-input-number v-model="addTaskForm.alipay_amount" :min="0" controls-position="right" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="任务日期">
          <el-date-picker v-model="addTaskForm.task_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="addTaskForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addTaskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAddTask">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { Refresh, Document, DataAnalysis, CircleCheck, Clock, CircleClose, Delete, Edit, Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'

const dateRange = ref([])
const dates = ref([])
const personList = ref([])
const customerList = ref([])
const cardList = ref([])
const selectedCustomerId = ref(null)
const selectedPersonId = ref(null)
const selectedBankId = ref(null)
const selectedStatus = ref(null)
const calendarData = ref({})
const expandedRowKeys = ref([])
const qrPreviewVisible = ref(false)
const previewQRUrl = ref('')
const selectedRows = ref([])
const editDialogVisible = ref(false)
const editingRow = ref(null)
const editForm = ref({
  id: null,
  amount: 0,
  wechat_amount: 0,
  alipay_amount: 0,
  status: 'pending',
  remark: ''
})

watch(() => editForm.value.wechat_amount, () => {})

watch(() => editForm.value.alipay_amount, () => {})

const addTaskDialogVisible = ref(false)
const bankList = ref([])
const addTaskForm = ref({
  person_id: null,
  customer_id: null,
  bank_id: null,
  amount: 0,
  wechat_amount: 0,
  alipay_amount: 0,
  task_date: '',
  remark: ''
})

watch(() => addTaskForm.value.wechat_amount, () => {})

watch(() => addTaskForm.value.alipay_amount, () => {})

const today = new Date()
dateRange.value = [
  today.toISOString().split('T')[0],
  today.toISOString().split('T')[0]
]

const taskTableData = computed(() => {
  const tasks = []
  Object.keys(calendarData.value).forEach(personId => {
    const personData = calendarData.value[personId]
    if (personData?.tasks) {
      Object.keys(personData.tasks).forEach(date => {
        personData.tasks[date].forEach(task => {
          const person = personList.value.find(p => p.id == personId)
          const taskData = {
            ...task,
            person_name: person ? person.name : task.person_name,
            person_id: personId
          }
          tasks.push(taskData)
        })
      })
    }
  })

  if (selectedStatus.value) {
    return tasks.filter(t => t.status === selectedStatus.value)
  }

  return tasks.sort((a, b) => new Date(b.task_date) - new Date(a.task_date))
})

const totalTasks = computed(() => taskTableData.value.length)
const completedTasks = computed(() => taskTableData.value.filter(t => t.status === 'completed').length)
const pendingTasks = computed(() => taskTableData.value.filter(t => t.status === 'pending').length)
const failedTasks = computed(() => taskTableData.value.filter(t => t.status === 'failed').length)

const dayTotalAmount = computed(() => {
  return taskTableData.value.reduce((sum, t) => sum + (t.amount || 0), 0)
})

const dayCompletedAmount = computed(() => {
  return taskTableData.value
    .filter(t => t.status === 'completed')
    .reduce((sum, t) => sum + (t.amount || 0), 0)
})

const dayFailedAmount = computed(() => {
  return taskTableData.value
    .filter(t => t.status === 'failed')
    .reduce((sum, t) => sum + (t.amount || 0), 0)
})

function formatAmount(amount) {
  return `¥${Math.round(amount).toLocaleString()}`
}

function handleExpandChange(row, expandedRows) {
  expandedRowKeys.value = expandedRows.map(r => r.id)
}

function formatTaskDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '-'
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
  } catch (e) {
    return '-'
  }
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

onMounted(() => {
  generateDates()
  loadPersonList()
  loadCustomerList()
  loadCardList()
  loadBankList()
  loadCalendarData()
})

function generateDates() {
  if (dateRange.value && dateRange.value.length === 2) {
    const start = new Date(dateRange.value[0])
    const end = new Date(dateRange.value[1])
    dates.value = []
    const current = new Date(start)
    while (current <= end) {
      dates.value.push(current.toISOString().split('T')[0])
      current.setDate(current.getDate() + 1)
    }
  }
}

async function loadPersonList() {
  try {
    const res = await axios.get('/api/person/list')
    personList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

async function loadCustomerList() {
  try {
    const res = await axios.get('/api/customer/list')
    customerList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

async function loadCardList() {
  try {
    const res = await axios.get('/api/bankcard/list')
    cardList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

async function loadBankList() {
  try {
    const res = await axios.get('/api/customer/banks')
    bankList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

function showAddTaskDialog() {
  addTaskForm.value = {
    person_id: null,
    customer_id: null,
    bank_id: null,
    amount: 0,
    wechat_amount: 0,
    alipay_amount: 0,
    task_date: new Date().toISOString().split('T')[0],
    remark: ''
  }
  addTaskDialogVisible.value = true
}

async function saveAddTask() {
  if (!addTaskForm.value.person_id) {
    ElMessage.warning('请选择人员')
    return
  }
  if (!addTaskForm.value.customer_id || !addTaskForm.value.bank_id) {
    ElMessage.warning('请选择客户和银行')
    return
  }
  const totalAmount = addTaskForm.value.wechat_amount + addTaskForm.value.alipay_amount
  if (!totalAmount || totalAmount <= 0) {
    ElMessage.warning('请输入有效的金额')
    return
  }

  try {
    await axios.post('/api/task-detail/create', {
      ...addTaskForm.value,
      amount: totalAmount
    })
    ElMessage.success('任务添加成功')
    addTaskDialogVisible.value = false
    loadCalendarData()
  } catch (e) {
    console.error(e)
    ElMessage.error('添加失败')
  }
}

async function loadCalendarData() {
  generateDates()
  if (dateRange.value && dateRange.value.length === 2) {
    try {
      const payload = {
        start_date: dateRange.value[0],
        end_date: dateRange.value[1]
      }
      if (selectedCustomerId.value) {
        payload.customer_id = selectedCustomerId.value
      }
      if (selectedPersonId.value) {
        payload.person_id = selectedPersonId.value
      }
      if (selectedBankId.value) {
        payload.bank_id = selectedBankId.value
      }
      const res = await axios.post('/api/task-detail/calendar', payload)
      calendarData.value = res.data.data?.persons || {}
    } catch (e) {
      console.error(e)
    }
  }
}

function getQRCode(task) {
  const card = cardList.value.find(
    c => c.customer_name === task.customer_name && c.bank_name === task.bank_name
  )
  return card?.receive_code || null
}

function getQRCodeUrl(code) {
  if (!code) return ''
  if (code.startsWith('/uploads/')) {
    return `http://localhost:5001${code}`
  }
  return code
}

function previewQRCode(code) {
  previewQRUrl.value = getQRCodeUrl(code)
  qrPreviewVisible.value = true
}

function getCustomerColor(customerName) {
  const customer = customerList.value.find(c => c.name === customerName)
  return customer ? customer.color : '#606266'
}

function getBankTagType(bankName) {
  if (!bankName) return 'info'
  if (bankName.includes('工商银行')) return 'danger'
  if (bankName.includes('建设银行')) return 'success'
  return 'info'
}

function getStatusType(status) {
  const map = {
    pending: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    pending: '待执行',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

function refreshData() {
  loadPersonList()
  loadCustomerList()
  loadCardList()
  loadCalendarData()
  ElMessage.success('数据已刷新')
}

function openEditDialog(row) {
  editingRow.value = row
  
  let wechatAmount = row.wechat_amount !== undefined && row.wechat_amount !== null ? row.wechat_amount : 0
  let alipayAmount = row.alipay_amount !== undefined && row.alipay_amount !== null ? row.alipay_amount : 0
  
  if (wechatAmount === 0 && alipayAmount === 0 && row.amount > 0) {
    wechatAmount = getSplitAmount(row, 1)
    alipayAmount = Math.round(row.amount) - wechatAmount
  }
  
  const total = Math.round(row.amount)
  if (wechatAmount + alipayAmount !== total) {
    alipayAmount = total - wechatAmount
  }
  
  editForm.value = {
    id: row.id,
    person_id: row.person_id,
    customer_id: row.customer_id,
    bank_id: row.bank_id,
    amount: total,
    wechat_amount: wechatAmount,
    alipay_amount: alipayAmount,
    task_date: row.task_date,
    status: row.status,
    remark: row.remark !== undefined && row.remark !== null ? row.remark : ''
  }
  editDialogVisible.value = true
}

async function saveEdit() {
  if (!editForm.value.id) {
    ElMessage.warning('无效的记录')
    return
  }

  try {
    const totalAmount = editForm.value.wechat_amount + editForm.value.alipay_amount
    const wechatAmount = editForm.value.wechat_amount || 0
    const alipayAmount = editForm.value.alipay_amount || 0
    
    await axios.put(`/api/task-detail/update/${editForm.value.id}`, {
      customer_id: editForm.value.customer_id,
      bank_id: editForm.value.bank_id,
      amount: totalAmount,
      wechat_amount: wechatAmount,
      alipay_amount: alipayAmount,
      task_date: editForm.value.task_date,
      status: editForm.value.status,
      remark: editForm.value.remark
    })
    ElMessage.success('编辑成功')
    editDialogVisible.value = false
    loadCalendarData()
  } catch (e) {
    console.error(e)
    ElMessage.error('编辑失败')
  }
}

function handleSelectionChange(rows) {
  selectedRows.value = rows
}

async function batchUpdateStatus(status) {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要操作的记录')
    return
  }

  const ids = selectedRows.value.map(r => r.id)
  try {
    await axios.put('/api/task-detail/batch-update-status', { ids, status })
    ElMessage.success(`批量${getStatusText(status)}成功`)
    loadCalendarData()
    selectedRows.value = []
  } catch (e) {
    console.error(e)
    ElMessage.error('批量操作失败')
  }
}

async function batchDelete() {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择要删除的记录')
    return
  }

  const ids = selectedRows.value.map(r => r.id)
  try {
    await axios.delete('/api/task-detail/batch-delete', { data: { ids } })
    ElMessage.success('批量删除成功')
    loadCalendarData()
    selectedRows.value = []
  } catch (e) {
    console.error(e)
    ElMessage.error('批量删除失败')
  }
}

const groupedTasks = computed(() => {
  const groups = {}
  taskTableData.value.forEach(task => {
    const key = task.person_id || task.person_name
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(task)
  })
  return groups
})

function getPersonName(personIdOrName) {
  const person = personList.value.find(p => p.id == personIdOrName)
  return person ? person.name : personIdOrName
}

function getBankCardClass(bankName) {
  if (bankName?.includes('工商银行')) return 'bank-icbc'
  if (bankName?.includes('建设银行')) return 'bank-ccb'
  return 'bank-default'
}

function getBankHeaderClass(bankName) {
  if (bankName?.includes('工商银行')) return 'header-icbc'
  if (bankName?.includes('建设银行')) return 'header-ccb'
  return 'header-default'
}

function getBankLogo(bankName) {
  if (bankName?.includes('工商银行')) return 'ICBC'
  if (bankName?.includes('建设银行')) return 'CCB'
  return 'BANK'
}

function getStatusClass(status) {
  const map = {
    pending: 'status-pending',
    completed: 'status-completed',
    failed: 'status-failed'
  }
  return map[status] || 'status-default'
}

function getPersonWechatTotal(tasks) {
  return tasks.reduce((sum, t) => sum + getSplitAmount(t, 1), 0)
}

function getPersonAlipayTotal(tasks) {
  return tasks.reduce((sum, t) => sum + (Math.round(t.amount) - getSplitAmount(t, 1)), 0)
}

function getPersonTotal(tasks) {
  return tasks.reduce((sum, t) => sum + Math.round(t.amount), 0)
}

async function exportImage() {
  if (taskTableData.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    ElMessage.info('正在生成图片，请稍候...')

    const exportContainer = document.getElementById('export-cards')
    if (!exportContainer) {
      ElMessage.error('未找到可导出的内容')
      return
    }

    exportContainer.style.display = 'block'
    exportContainer.style.position = 'fixed'
    exportContainer.style.top = '-9999px'
    exportContainer.style.left = '-9999px'
    exportContainer.style.width = '600px'
    
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const canvas = await html2canvas(exportContainer, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      width: 600
    })

    exportContainer.style.display = 'none'
    exportContainer.style.position = ''
    exportContainer.style.top = ''
    exportContainer.style.left = ''
    exportContainer.style.width = ''

    const imgData = canvas.toDataURL('image/png')
    
    const link = document.createElement('a')
    link.href = imgData
    
    const personIds = Object.keys(groupedTasks.value)
    const firstPersonId = personIds[0] || ''
    const personName = getPersonName(firstPersonId)
    
    let fileName = ''
    const datePart = dateRange.value[0] === dateRange.value[1] 
      ? dateRange.value[0] 
      : `${dateRange.value[0]}_${dateRange.value[1]}`
    
    fileName = `${personName}_${datePart}.png`
    
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('图片导出成功')
  } catch (error) {
    console.error('图片导出失败:', error)
    ElMessage.error('图片导出失败，请重试')
  }
}

import * as XLSX from 'xlsx'

function exportExcel() {
  if (taskTableData.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  const data = taskTableData.value.map(row => ({
    '人员': getPersonName(row.person_id || row.person_name),
    '客户': row.customer_name || '-',
    '银行': row.bank_name || '-',
    '任务日期': row.task_date || '-',
    '总金额': row.amount || 0,
    '微信': ((row.wechat_amount || 0) + (row.alipay_amount || 0) > 0 && (row.wechat_amount || 0) + (row.alipay_amount || 0) === Math.round(row.amount)) ? (row.wechat_amount || 0) : getSplitAmount(row, 1),
    '支付宝': ((row.wechat_amount || 0) + (row.alipay_amount || 0) > 0 && (row.wechat_amount || 0) + (row.alipay_amount || 0) === Math.round(row.amount)) ? (row.alipay_amount || 0) : (Math.round(row.amount) - getSplitAmount(row, 1)),
    '状态': row.status === 'pending' ? '待执行' : row.status === 'completed' ? '已完成' : row.status === 'failed' ? '失败' : row.status,
    '备注': row.remark || '-'
  }))

  const worksheet = XLSX.utils.json_to_sheet(data)
  
  const wscols = [
    { wch: 10 },
    { wch: 12 },
    { wch: 12 },
    { wch: 12 },
    { wch: 10 },
    { wch: 10 },
    { wch: 10 },
    { wch: 10 },
    { wch: 20 }
  ]
  worksheet['!cols'] = wscols

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '任务数据')

  const today = new Date()
  const dateStr = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`
  
  XLSX.writeFile(workbook, `任务数据_${dateStr}.xlsx`)
  
  ElMessage.success('Excel导出成功')
}
</script>

<style scoped>
.home-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
  padding: 16px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.total-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.completed-icon {
  background: linear-gradient(135deg, #67c23a 0%, #52c41a 100%);
  color: #fff;
}

.pending-icon {
  background: linear-gradient(135deg, #e6a23c 0%, #d4942f 100%);
  color: #fff;
}

.failed-icon {
  background: linear-gradient(135deg, #f56c6c 0%, #e85d5d 100%);
  color: #fff;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.main-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.selected-count {
  font-size: 14px;
  color: #606266;
}

.stats-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.table-cell-center {
  text-align: center;
}

.el-table .el-button::after {
  content: none;
}

.el-table__column-filter-trigger {
  display: none;
}

.stat-item {
  flex: 1;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  border: 1px solid #ebeef5;
}

.stat-item .stat-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: #667eea;
}

.stat-item .stat-label {
  display: block;
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.stat-item.completed .stat-value {
  color: #67c23a;
}

.stat-item.pending .stat-value {
  color: #e6a23c;
}

.stat-item.manual .stat-value {
  color: #f56c6c;
}

.stat-item.failed .stat-value {
  color: #909399;
}

.btn-delete {
  --el-button-bg-color: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  --el-button-text-color: #fff;
  --el-button-border-color: #8e44ad;
  --el-button-hover-bg-color: linear-gradient(135deg, #8e44ad 0%, #7d3c98 100%);
  --el-button-hover-border-color: #7d3c98;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  border-color: #8e44ad;
  color: white;
}

.btn-delete:not(:disabled):hover {
  background: linear-gradient(135deg, #8e44ad 0%, #7d3c98 100%);
  border-color: #7d3c98;
}

.btn-delete.is-disabled {
  opacity: 0.5;
  background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
  border-color: #8e44ad;
  color: white;
  cursor: not-allowed;
  pointer-events: none;
}

.action-bar .el-button--success:not(:disabled):hover {
  --el-button-hover-bg-color: #52c41a;
  --el-button-hover-border-color: #52c41a;
  background-color: #52c41a;
  border-color: #52c41a;
}

.action-bar .el-button--warning:not(:disabled):hover {
  --el-button-hover-bg-color: #d4943c;
  --el-button-hover-border-color: #d4943c;
  background-color: #d4943c;
  border-color: #d4943c;
}

.action-bar .el-button--danger:not(:disabled):hover {
  --el-button-hover-bg-color: #dc2626;
  --el-button-hover-border-color: #dc2626;
  background-color: #dc2626;
  border-color: #dc2626;
}

.customer-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.option-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 14px;
}

.customer-tag {
  font-weight: 500;
}

.amount-text {
  font-weight: 600;
  color: #303133;
}

.wechat-amount {
  color: #67c23a;
  font-weight: 500;
}

.alipay-amount {
  color: #409eff;
  font-weight: 500;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.remark-text {
  font-size: 12px;
  color: #909399;
}

.editable-code {
  width: 100%;
}

.expand-detail {
  padding: 16px 0;
}

.qr-mini-preview {
  display: inline-block;
}

.qr-mini {
  width: 60px;
  height: 60px;
  cursor: pointer;
  border-radius: 4px;
}

.qr-preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.qr-preview-image {
  max-width: 300px;
  max-height: 300px;
  border-radius: 8px;
}

.el-table__expand-icon {
  font-size: 16px;
}

.export-cards-container {
  padding: 20px;
  background: #ffffff;
}

.person-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e0e0e0;
}

.person-title {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.task-count {
  font-size: 14px;
  color: #999;
}

.cards-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  display: flex;
  align-items: stretch;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-left {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: transparent;
}

.qr-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-code {
  max-width: 220px;
  height: auto;
  object-fit: contain;
}

.qr-placeholder {
  width: 220px;
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8f9fa;
  border-radius: 8px;
  color: #999;
  font-size: 12px;
}

.card-right {
  flex: 1;
  padding: 20px;
  background: #fff8f0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.card-info {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 300px;
}

.info-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 0;
}

.info-group.amounts {
  gap: 10px;
  padding: 10px 0;
}

.info-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.06);
  margin: 2px 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #888;
  font-size: 13px;
  font-weight: 500;
}

.info-value {
  color: #333;
  font-weight: 600;
  font-size: 16px;
}

.info-group.amounts .info-value {
  font-size: 18px;
  font-weight: 700;
}

.customer-value {
  font-weight: 600;
}

.wechat-value {
  color: #07c160;
}

.alipay-value {
  color: #1677ff;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 14px;
}

.status-pending {
  background: #fff7e6;
  color: #faad14;
}

.status-completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-failed {
  background: #fff2f0;
  color: #ff4d4f;
}

.summary-row {
  display: flex;
  justify-content: flex-end;
  gap: 24px;
  margin-top: 16px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-label {
  font-size: 14px;
  color: #666;
}

.summary-value {
  font-size: 16px;
  font-weight: bold;
}

.wechat-summary {
  color: #07c160;
}

.alipay-summary {
  color: #1677ff;
}

.total-summary {
  color: #333;
}

.summary-item.total {
  border-left: 1px solid #ddd;
  padding-left: 24px;
}
</style>