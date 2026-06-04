<template>
  <div class="home-container">
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <span>任务概览</span>
          <div>
            <el-button type="success" @click="exportExcel" :icon="Document">导出Excel</el-button>
            <el-button type="warning" @click="exportImage" :icon="Document">导出图片</el-button>
            <el-button type="danger" @click="exportPDF" :icon="Document">导出PDF</el-button>
            <el-button type="primary" @click="refreshData" :icon="Refresh">刷新</el-button>
          </div>
        </div>
      </template>

      <div class="filter-bar">
        <span class="filter-label">选择客户：</span>
        <el-select
          v-model="selectedCustomerId"
          clearable
          placeholder="全部客户"
          style="width: 180px;"
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

        <span class="filter-label">选择人员：</span>
        <el-select
          v-model="selectedPersonId"
          clearable
          placeholder="全部人员"
          style="width: 180px;"
          @change="loadCalendarData"
        >
          <el-option
            v-for="p in personList"
            :key="p.id"
            :label="`${p.code} - ${p.name}`"
            :value="p.id"
          />
        </el-select>

        <span class="filter-label">选择日期范围：</span>
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

      <div class="task-legend">
        <span class="legend-item">
          <i class="legend-dot legend-completed" />
          已完成
        </span>
        <span class="legend-item">
          <i class="legend-dot legend-pending" />
          待执行
        </span>
        <span class="legend-item">
          <i class="legend-dot legend-failed" />
          失败
        </span>
      </div>

      <div v-if="personList.length === 0" class="empty-tip">
        暂无数据
      </div>

      <div v-if="selectedPersonId" class="person-card-view">
        <div class="person-header-card">
          <span class="person-title">{{ getSelectedPersonInfo() }}</span>
          <span class="task-count-badge">共 {{ getSelectedPersonTasks().length }} 个任务</span>
        </div>
        
        <div v-if="getSelectedPersonTasks().length === 0" class="empty-tip">
          该人员暂无任务
        </div>
        
        <div class="task-cards">
          <div 
            v-for="(task, index) in getSelectedPersonTasks()" 
            :key="task.id" 
            class="task-card-item"
            :style="getTaskCardStyle(task)"
          >
            <div class="task-card-main">
              <div class="task-card-left">
                <div class="qr-code-container" v-if="getQRCode(task)">
                  <img 
                    :src="getQRCodeUrl(getQRCode(task))" 
                    alt="收款码" 
                    class="qr-code-image"
                    @click="previewQRCode(getQRCode(task))"
                  />
                </div>
                <div class="no-qr-code" v-else>
                  暂无收款码
                </div>
              </div>
              <div class="task-card-right">
                <div class="detail-row">
                  <span class="detail-label">客户：</span>
                  <span class="detail-value" :style="{ color: getCustomerColor(task.customer_name) }">{{ task.customer_name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">银行：</span>
                  <span class="detail-value">{{ task.bank_name.replace('银行', '') }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">微信：</span>
                  <span class="detail-value green-text">{{ getSplitAmount(task, 1) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">支付宝：</span>
                  <span class="detail-value blue-text">{{ Math.round(task.amount) - getSplitAmount(task, 1) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">日期：</span>
                  <span class="detail-value">{{ formatTaskDate(task.task_date) }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">状态：</span>
                  <span :class="['detail-value', 'status-text', task.status === 'completed' ? 'status-completed' : task.status === 'failed' ? 'status-failed' : 'status-pending']">
                    {{ task.status === 'completed' ? '已完成' : task.status === 'failed' ? '失败' : '待执行' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="getSelectedPersonTasks().length > 0" class="total-summary">
          <div class="summary-item">
            <span class="summary-label">微信合计：</span>
            <span class="summary-value green">¥{{ getWechatTotal() }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">支付宝合计：</span>
            <span class="summary-value blue">¥{{ getAlipayTotal() }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">总计：</span>
            <span class="summary-value total">¥{{ getTotalAmount() }}</span>
          </div>
        </div>
      </div>

      <div v-else class="person-groups">
        <div
          v-for="person in personList"
          :key="person.id"
          class="person-card"
        >
          <div class="person-header">
            <span class="person-code">{{ person.code }} - {{ person.name }}</span>
            <span class="task-count">共 {{ getPersonTasks(person.code).length }} 个任务</span>
          </div>
          
          <div class="person-tasks">
            <div
              v-for="task in getPersonTasks(person.code)"
              :key="task.id"
              class="task-card"
              :class="getTaskStatusClass(task.status)"
              :style="getTaskStyle(task)"
              @click="showTaskDetail(task)"
            >
              <div class="task-content">
                <div class="task-info">
                  <span class="customer-name" :style="{ color: getCustomerColor(task.customer_name) }">{{ task.customer_name }}</span>
                  <span class="bank" :class="getBankBadgeClass(task.bank_name)">{{ task.bank_name }}</span>
                </div>
                <div class="amount-boxes">
                  <span class="amount-box green-box">¥{{ getSplitAmount(task, 1) }}</span>
                  <span class="amount-box blue-box">¥{{ getSplitAmount(task, 2) }}</span>
                </div>
              </div>
              <div class="task-footer">
                <span class="task-date">{{ formatTaskDate(task.task_date) }}</span>
                <span class="task-status" :style="{ background: getTaskStatusBg(task.status), color: getTaskStatusColor(task.status) }">
                  {{ getStatusText(task.status) }}
                </span>
              </div>
            </div>
            
            <div v-if="getPersonTasks(person.code).length === 0" class="no-task">
              暂无任务
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" title="任务详情" width="500px">
      <el-descriptions :column="1" border v-if="selectedTask">
        <el-descriptions-item label="人员">{{ selectedTask.person_code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ Math.round(selectedTask.amount || 0) }}</el-descriptions-item>
        <el-descriptions-item label="客户">
          <span
            v-if="selectedTask.customer_name"
            class="customer-tag"
            :style="{ color: selectedTask.customer_color, borderColor: selectedTask.customer_color }"
          >
            {{ selectedTask.customer_name }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="银行">{{ selectedTask.bank_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="任务日期">{{ formatTaskDate(selectedTask.task_date) }}</el-descriptions-item>
        <el-descriptions-item label="收款码">
          <div v-if="getQRCode(selectedTask)" class="qr-preview">
            <img 
              :src="getQRCodeUrl(getQRCode(selectedTask))" 
              alt="收款码" 
              class="qr-large"
            />
          </div>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedTask.status)">{{ getStatusText(selectedTask.status) }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 收款码预览弹窗 -->
    <el-dialog v-model="qrPreviewVisible" title="收款码" width="400px">
      <div class="qr-preview-container">
        <img :src="previewQRUrl" alt="收款码" class="qr-preview-image" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Refresh, Document } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import * as XLSX from 'xlsx'

const dateRange = ref([])
const dates = ref([])
const personList = ref([])
const customerList = ref([])
const cardList = ref([])
const selectedCustomerId = ref(null)
const selectedPersonId = ref(null)
const calendarData = ref({})
const detailVisible = ref(false)
const selectedTask = ref(null)
const qrPreviewVisible = ref(false)
const previewQRUrl = ref('')

const today = new Date()
const weekLater = new Date(today.getTime() + 6 * 24 * 60 * 60 * 1000)
dateRange.value = [
  today.toISOString().split('T')[0],
  weekLater.toISOString().split('T')[0]
]

function buildGanttRows() {
  return personList.value
    .map((person) => {
      const dateTasks = {}
      dates.value.forEach((date) => {
        const personData = calendarData.value[person.code]
        dateTasks[date] = personData?.tasks?.[date] || []
      })
      return { code: person.code, dateTasks }
    })
}

function getPersonTasks(personCode) {
  const personData = calendarData.value[personCode]
  if (!personData?.tasks) return []
  
  const tasks = []
  Object.keys(personData.tasks).forEach(date => {
    tasks.push(...personData.tasks[date])
  })
  
  return tasks.sort((a, b) => new Date(a.task_date) - new Date(b.task_date))
}

function getPersonNameByCode(personCode) {
  const person = personList.value.find(p => p.code === personCode)
  return person ? person.name : personCode || '-'
}

function getSelectedPersonInfo() {
  const person = personList.value.find(p => p.id === selectedPersonId.value)
  return person ? `${person.code} - ${person.name}` : '-'
}

function getTaskCardStyle(task) {
  if (task.status === 'completed') {
    return {
      background: '#f0f9eb',
      borderColor: '#67c23a',
      borderWidth: '2px',
      borderStyle: 'solid'
    }
  }
  if (task.status === 'failed') {
    return {
      background: '#fef0f0',
      borderColor: '#f56c6c',
      borderWidth: '2px',
      borderStyle: 'solid'
    }
  }
  return {
    background: '#fff7e6',
    borderColor: '#e6a23c',
    borderWidth: '2px',
    borderStyle: 'solid'
  }
}

function getWechatTotal() {
  return getSelectedPersonTasks().reduce((sum, task) => sum + getSplitAmount(task, 1), 0)
}

function getAlipayTotal() {
  return getSelectedPersonTasks().reduce((sum, task) => sum + (Math.round(task.amount) - getSplitAmount(task, 1)), 0)
}

function getTotalAmount() {
  return getSelectedPersonTasks().reduce((sum, task) => sum + Math.round(task.amount), 0)
}

function getSelectedPersonTasks() {
  const tasks = []
  Object.keys(calendarData.value).forEach(personCode => {
    const personData = calendarData.value[personCode]
    if (personData?.tasks) {
      Object.keys(personData.tasks).forEach(date => {
        personData.tasks[date].forEach(task => {
          const total = Math.round(task.amount)
          const wechat = getSplitAmount(task, 1)
          const tasksWithAmount = {
            ...task,
            wechat_amount: wechat,
            alipay_amount: total - wechat
          }
          tasks.push(tasksWithAmount)
        })
      })
    }
  })
  return tasks.sort((a, b) => new Date(a.task_date) - new Date(b.task_date))
}

const personTasksWithTotal = computed(() => {
  const tasks = getSelectedPersonTasks()
  
  if (tasks.length === 0) {
    return []
  }
  
  const wechatTotal = tasks.reduce((sum, row) => sum + (row.wechat_amount || 0), 0)
  const alipayTotal = tasks.reduce((sum, row) => sum + (row.alipay_amount || 0), 0)
  const amountTotal = tasks.reduce((sum, row) => sum + (row.amount || 0), 0)
  
  const totalRow = {
    customer_name: '合计',
    task_date: '',
    bank_name: '',
    wechat_amount: Math.round(wechatTotal),
    alipay_amount: Math.round(alipayTotal),
    amount: Math.round(amountTotal),
    status: '',
    isTotal: true,
    id: 'total-row'
  }
  
  return [...tasks, totalRow]
})

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

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '-'
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}`
  } catch (e) {
    return '-'
  }
}

onMounted(() => {
  generateDates()
  loadPersonList()
  loadCustomerList()
  loadCardList()
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
      const res = await axios.post('/api/task-detail/calendar', payload)
      calendarData.value = res.data.data?.persons || {}
    } catch (e) {
      console.error(e)
    }
  }
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

function showTaskDetail(task) {
  selectedTask.value = task
  detailVisible.value = true
}

function getQRCode(task) {
  const card = cardList.value.find(
    c => c.customer_name === task.customer_name && c.bank_name === task.bank_name
  )
  return card?.receive_code || null
}

function isQRCodeImage(code) {
  return code && (code.startsWith('/uploads/') || code.startsWith('http') || code.match(/\.(jpg|jpeg|png|gif|webp)$/i))
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

function hexToRgb(hex) {
  const h = (hex || '#409EFF').replace('#', '')
  if (h.length !== 6) return { r: 64, g: 158, b: 255 }
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16)
  }
}

function getTaskStyle(task) {
  if (task.status === 'completed') {
    return {
      background: '#f0f9eb',
      borderColor: '#67c23a',
      borderWidth: '2px',
      borderStyle: 'solid'
    }
  }
  if (task.status === 'failed') {
    return {
      background: '#fef0f0',
      borderColor: '#f56c6c',
      borderWidth: '2px',
      borderStyle: 'solid'
    }
  }
  return {
    background: '#fff7e6',
    borderColor: '#e6a23c',
    borderWidth: '2px',
    borderStyle: 'solid'
  }
}

function getBankBadgeClass(bankName) {
  if (!bankName) return ''
  if (bankName.includes('工商银行')) return 'bank-icbc'
  if (bankName.includes('建设银行')) return 'bank-ccb'
  return ''
}

function getTaskStatusClass(status) {
  const map = {
    pending: 'status-pending',
    completed: 'status-completed',
    failed: 'status-failed'
  }
  return map[status] || 'status-pending'
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

function getTaskStatusColor(status) {
  const map = {
    pending: '#e6a23c',
    completed: '#67c23a',
    failed: '#f56c6c'
  }
  return map[status] || '#606266'
}

function getTaskStatusBg(status) {
  const map = {
    pending: '#fff7e6',
    completed: '#e1f3d8',
    failed: '#fde2e2'
  }
  return map[status] || '#f5f7fa'
}

function getCustomerColor(customerName) {
  const customer = customerList.value.find(c => c.name === customerName)
  return customer ? customer.color : '#606266'
}

function getSummary(param) {
  const { columns, data } = param
  const sums = []
  
  const wechatTotal = data.reduce((sum, row) => sum + (row.wechat_amount || 0), 0)
  const alipayTotal = data.reduce((sum, row) => sum + (row.alipay_amount || 0), 0)
  const amountTotal = data.reduce((sum, row) => sum + (row.amount || 0), 0)
  
  columns.forEach((column) => {
    if (column.prop === 'customer_name') {
      sums.push({
        cellStyle: { textAlign: 'center', fontWeight: 'bold' },
        value: '合计'
      })
    } else if (column.prop === 'wechat_amount') {
      sums.push({
        cellStyle: { textAlign: 'center', fontWeight: 'bold', color: '#67c23a' },
        value: `¥${Math.round(wechatTotal)}`
      })
    } else if (column.prop === 'alipay_amount') {
      sums.push({
        cellStyle: { textAlign: 'center', fontWeight: 'bold', color: '#409eff' },
        value: `¥${Math.round(alipayTotal)}`
      })
    } else if (column.prop === 'amount') {
      sums.push({
        cellStyle: { textAlign: 'center', fontWeight: 'bold' },
        value: `¥${Math.round(amountTotal)}`
      })
    } else {
      sums.push('')
    }
  })
  
  return [sums]
}

function refreshData() {
  loadPersonList()
  loadCustomerList()
  loadCardList()
  loadCalendarData()
  ElMessage.success('数据已刷新')
}

async function exportPDF() {
  if (dates.value.length === 0 || Object.keys(calendarData.value).length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    ElMessage.info('正在生成PDF，请稍候...')

    let element = document.querySelector('.person-card-view')
    if (!element) {
      element = document.querySelector('.person-table-container')
    }
    if (!element) {
      element = document.querySelector('.person-groups')
    }
    
    if (!element) {
      ElMessage.error('未找到可导出的内容')
      return
    }
    
    const canvas = await html2canvas(element, {
      scale: selectedPersonId.value ? 3 : 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      width: element.scrollWidth,
      height: element.scrollHeight,
      windowWidth: element.scrollWidth,
      windowHeight: element.scrollHeight
    })

    const imgData = canvas.toDataURL('image/png')
    
    let pdfWidth, pdfHeight
    if (selectedPersonId.value) {
      pdfWidth = canvas.width * 0.75
      pdfHeight = canvas.height * 0.75
    } else {
      pdfWidth = canvas.width * 0.5
      pdfHeight = canvas.height * 0.5
    }
    
    const pdf = new jsPDF({
      orientation: pdfWidth > pdfHeight ? 'landscape' : 'portrait',
      unit: 'px',
      format: [pdfWidth, pdfHeight]
    })

    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
    
    let fileName = ''
    const datePart = dateRange.value[0] === dateRange.value[1] 
      ? dateRange.value[0] 
      : `${dateRange.value[0]}_${dateRange.value[1]}`
    
    if (selectedPersonId.value) {
      const person = personList.value.find(p => p.id === selectedPersonId.value)
      if (person) {
        fileName = `${person.name}-${datePart}.pdf`
      } else {
        fileName = `${datePart}.pdf`
      }
    } else {
      fileName = `${datePart}.pdf`
    }
    pdf.save(fileName)
    
    ElMessage.success('PDF导出成功')
  } catch (error) {
    console.error('PDF导出失败:', error)
    ElMessage.error('PDF导出失败，请重试')
  }
}

async function exportExcel() {
  if (dates.value.length === 0 || Object.keys(calendarData.value).length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    ElMessage.info('正在生成Excel，请稍候...')
    
    const tasks = []
    Object.keys(calendarData.value).forEach(personCode => {
      const personData = calendarData.value[personCode]
      if (personData?.tasks) {
        Object.keys(personData.tasks).forEach(date => {
          personData.tasks[date].forEach(task => {
            const total = Math.round(task.amount)
            const wechat = getSplitAmount(task, 1)
            const card = cardList.value.find(
              c => c.customer_name === task.customer_name && c.bank_name === task.bank_name
            )
            tasks.push({
              '人员': getPersonNameByCode(personCode),
              '客户': task.customer_name || '',
              '日期': formatTaskDate(task.task_date),
              '银行': task.bank_name || '',
              '微信金额': wechat,
              '支付宝金额': total - wechat,
              '总金额': total,
              '收款码': card?.receive_code ? '已上传' : '未上传',
              '状态': task.status === 'completed' ? '已完成' : task.status === 'failed' ? '失败' : '待执行'
            })
          })
        })
      }
    })
    
    if (tasks.length === 0) {
      ElMessage.warning('没有可导出的任务数据')
      return
    }
    
    tasks.sort((a, b) => new Date(a.日期) - new Date(b.日期))
    
    const wechatTotal = tasks.reduce((sum, t) => sum + t.微信金额, 0)
    const alipayTotal = tasks.reduce((sum, t) => sum + t.支付宝金额, 0)
    const amountTotal = tasks.reduce((sum, t) => sum + t.总金额, 0)
    
    tasks.push({
      '人员': '合计',
      '客户': '',
      '日期': '',
      '银行': '',
      '微信金额': wechatTotal,
      '支付宝金额': alipayTotal,
      '总金额': amountTotal,
      '收款码': '',
      '状态': ''
    })
    
    const ws = XLSX.utils.json_to_sheet(tasks)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '任务明细')
    
    ws['!cols'] = [
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 12 },
      { wch: 10 }
    ]
    
    let fileName = ''
    const datePart = dateRange.value[0] === dateRange.value[1] 
      ? dateRange.value[0] 
      : `${dateRange.value[0]}_${dateRange.value[1]}`
    
    if (selectedPersonId.value) {
      const person = personList.value.find(p => p.id === selectedPersonId.value)
      if (person) {
        fileName = `${person.name}-${datePart}.xlsx`
      } else {
        fileName = `${datePart}.xlsx`
      }
    } else {
      fileName = `${datePart}.xlsx`
    }
    
    XLSX.writeFile(wb, fileName)
    ElMessage.success('Excel导出成功')
  } catch (error) {
    console.error('Excel导出失败:', error)
    ElMessage.error('Excel导出失败，请重试')
  }
}

async function exportImage() {
  if (dates.value.length === 0 || Object.keys(calendarData.value).length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    ElMessage.info('正在生成图片，请稍候...')

    let element = document.querySelector('.person-card-view')
    if (!element) {
      element = document.querySelector('.person-table-container')
    }
    if (!element) {
      element = document.querySelector('.person-groups')
    }
    
    if (!element) {
      ElMessage.error('未找到可导出的内容')
      return
    }
    
    const canvas = await html2canvas(element, {
      scale: 3,
      useCORS: true,
      backgroundColor: '#ffffff',
      logging: false,
      width: element.scrollWidth,
      height: element.scrollHeight,
      windowWidth: element.scrollWidth,
      windowHeight: element.scrollHeight
    })

    const imgData = canvas.toDataURL('image/png')
    
    const link = document.createElement('a')
    link.href = imgData
    
    let fileName = ''
    const datePart = dateRange.value[0] === dateRange.value[1] 
      ? dateRange.value[0] 
      : `${dateRange.value[0]}_${dateRange.value[1]}`
    
    if (selectedPersonId.value) {
      const person = personList.value.find(p => p.id === selectedPersonId.value)
      if (person) {
        fileName = `${person.name}-${datePart}.png`
      } else {
        fileName = `${datePart}.png`
      }
    } else {
      fileName = `${datePart}.png`
    }
    
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
</script>

<style scoped>
.home-container {
  max-width: 1800px;
  margin: 0 auto;
  padding: 0 20px;
}

.stats-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px 20px;
}

.filter-label {
  color: #606266;
  font-size: 14px;
  white-space: nowrap;
}

.customer-option {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.option-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 14px;
}

.task-legend {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #606266;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  border: 2px solid transparent;
}

.legend-completed {
  background: #e1f3d8;
  border-color: #67c23a;
}

.legend-pending {
  background: #e8f4fd;
  border-color: #409eff;
}

.legend-failed {
  background: #fde2e2;
  border-color: #f56c6c;
}

.person-groups {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.person-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e4e7ed;
}

.person-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.person-code {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

.task-count {
  font-size: 12px;
  color: #909399;
}

.person-tasks {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-card {
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.task-content {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.task-card .customer-name {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.task-card .bank {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.task-card .bank.bank-icbc {
  background: linear-gradient(135deg, #e63946 0%, #cc2936 100%);
  color: #fff;
}

.task-card .bank.bank-ccb {
  background: linear-gradient(135deg, #2a9d8f 0%, #21867a 100%);
  color: #fff;
}

.task-card .task-date {
  font-size: 12px;
  color: #909399;
}

.task-card .task-amount {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.task-card .completed-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: #67c23a;
  color: white;
  border-radius: 4px;
  font-weight: 500;
}

.amount-boxes {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.amount-box {
  font-size: 14px;
  font-weight: bold;
  padding: 4px 10px;
  border-radius: 4px;
  color: white;
  white-space: nowrap;
}

.green-box {
  background: #67c23a;
}

.blue-box {
  background: #409EFF;
}

.qr-code-section {
  display: flex;
  justify-content: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #d9d9d9;
}

.qr-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
}

.qr-small {
  width: 100px;
  height: 100px;
  object-fit: contain;
  cursor: pointer;
  border: 1px solid #eee;
  border-radius: 4px;
}

.no-qr {
  font-size: 12px;
  color: #909399;
}

.task-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #d9d9d9;
}

.task-date {
  font-size: 12px;
  color: #909399;
}

.task-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: #fff7e6;
  color: #e6a23c;
}

.no-task {
  text-align: center;
  color: #909399;
  padding: 20px 0;
  font-size: 13px;
}

.status-completed {
  opacity: 0.95;
}

.person-table-container {
  margin-top: 16px;
}

.amount-tag {
  font-size: 12px;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 4px;
  color: white;
}

.green-tag {
  background: #67c23a;
}

.blue-tag {
  background: #409EFF;
}

.status-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-pending {
  background: #fff7e6;
  color: #e6a23c;
}

.status-completed {
  background: #e1f3d8;
  color: #67c23a;
}

.status-failed {
  background: #fde2e2;
  color: #f56c6c;
}

.customer-tag {
  font-weight: 600;
  padding: 2px 8px;
  border-left: 3px solid;
  border-radius: 2px;
}

.person-card-view {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.person-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.person-title {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.task-count-badge {
  font-size: 14px;
  color: #909399;
}

.task-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.task-card-item {
  display: flex;
  background: #fff;
  border: 4px solid #409eff;
  border-radius: 16px;
  overflow: hidden;
}

.task-card-main {
  display: flex;
  width: 100%;
}

.task-card-left {
  flex: 1;
  background: #fff;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-right: 2px solid #e4e7ed;
}

.card-number {
  font-size: 24px;
  font-weight: bold;
  color: #ff4d4f;
  margin-bottom: 10px;
}

.task-card-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.customer-label {
  font-size: 16px;
  font-weight: 600;
  color: #e6a23c;
}

.bank-label {
  font-size: 14px;
  color: #606266;
}

.task-card-amounts {
  display: flex;
  gap: 8px;
}

.amount-badge {
  font-size: 16px;
  font-weight: bold;
  padding: 6px 14px;
  border-radius: 6px;
  color: white;
}

.green-badge {
  background: #67c23a;
}

.blue-badge {
  background: #409EFF;
}

.task-card-right {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.detail-row {
  display: flex;
  margin-bottom: 10px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  min-width: 70px;
}

.detail-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.green-text {
  color: #67c23a;
}

.blue-text {
  color: #409EFF;
}

.status-text {
  padding: 4px 12px;
  border-radius: 4px;
}

.status-text.status-completed {
  background: #e1f3d8;
  color: #67c23a;
}

.status-text.status-pending {
  background: #fff7e6;
  color: #e6a23c;
}

.status-text.status-failed {
  background: #fde2e2;
  color: #f56c6c;
}

.qr-code-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.qr-code-image {
  max-width: 300px;
  max-height: 350px;
  width: auto;
  height: auto;
  object-fit: contain;
  cursor: pointer;
}

.no-qr-code {
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.task-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px dashed #d9d9d9;
}

.status-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 4px;
}

.status-badge.status-pending {
  background: #fff7e6;
  color: #e6a23c;
}

.status-badge.status-completed {
  background: #e1f3d8;
  color: #67c23a;
}

.status-badge.status-failed {
  background: #fde2e2;
  color: #f56c6c;
}

.total-summary {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

.summary-value {
  font-size: 16px;
  font-weight: bold;
}

.summary-value.green {
  color: #67c23a;
}

.summary-value.blue {
  color: #409EFF;
}

.summary-value.total {
  color: #303133;
  font-size: 18px;
}

.qr-preview-container {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.qr-preview-image {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.qr-preview {
  display: flex;
  justify-content: center;
}

.qr-large {
  width: 200px;
  height: 200px;
  object-fit: contain;
}
</style>
