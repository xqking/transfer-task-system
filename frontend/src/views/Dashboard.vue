<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-left">
        <div class="title-icon">📊</div>
        <div>
          <h2>任务大屏</h2>
          <p class="subtitle">实时监控任务执行情况</p>
        </div>
      </div>
      <div class="header-right">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="default"
          @change="loadData"
        />
      </div>
    </div>

    <div class="summary-cards">
      <div class="summary-card total">
        <div class="card-icon">💰</div>
        <div class="card-content">
          <div class="summary-value">¥{{ formatAmount(dashboardData.grand_total) }}</div>
          <div class="summary-label">总金额</div>
        </div>
      </div>
      <div class="summary-card completed">
        <div class="card-icon">✅</div>
        <div class="card-content">
          <div class="summary-value">¥{{ formatAmount(dashboardData.grand_completed) }}</div>
          <div class="summary-label">已完成</div>
        </div>
      </div>
      <div class="summary-card pending">
        <div class="card-icon">⏳</div>
        <div class="card-content">
          <div class="summary-value">¥{{ formatAmount(dashboardData.grand_pending) }}</div>
          <div class="summary-label">待完成</div>
        </div>
      </div>
      <div class="summary-card failed">
        <div class="card-icon">❌</div>
        <div class="card-content">
          <div class="summary-value">¥{{ formatAmount(dashboardData.grand_failed || 0) }}</div>
          <div class="summary-label">失败金额</div>
        </div>
      </div>
    </div>

    <div class="section-title">
      <span class="title-bar"></span>
      <span>客户任务统计</span>
    </div>

    <div class="customer-cards">
      <div 
        v-for="customer in dashboardData.customers" 
        :key="customer.customer_id" 
        class="customer-card"
      >
        <div class="customer-header" :style="{ borderBottomColor: customer.customer_color + '30' }">
          <div class="customer-name" :style="{ color: customer.customer_color }">
            <span class="name-dot" :style="{ backgroundColor: customer.customer_color }"></span>
            {{ customer.customer_name }}
          </div>
          <div class="customer-total">
            <span class="total-value" :style="{ color: customer.customer_color }">¥{{ formatAmount(customer.total_amount) }}</span>
            <span class="total-label">总金额</span>
          </div>
        </div>
        
        <div class="card-details">
          <div 
            v-for="card in customer.cards" 
            :key="card.card_id" 
            class="card-item"
          >
            <div class="card-info">
              <div class="bank-name">{{ card.bank_name }}</div>
              <div class="card-no">****{{ card.card_no }}</div>
            </div>
            <div class="card-amount">
              <div class="amount-item">
                <div class="amount-value total-val">¥{{ formatAmount(card.total_amount) }}</div>
                <div class="amount-label">总金额</div>
              </div>
              <div class="amount-item">
                <div class="amount-value completed-val">¥{{ formatAmount(card.completed_amount) }}</div>
                <div class="amount-label">已完成</div>
              </div>
              <div class="amount-item">
                <div class="amount-value pending-val">¥{{ formatAmount(card.pending_amount) }}</div>
                <div class="amount-label">待完成</div>
              </div>
            </div>
          </div>
        </div>

        <div class="customer-progress">
          <div class="progress-header">
            <span>完成进度</span>
            <span class="progress-percent" :style="{ color: customer.customer_color }">
              {{ customer.total_amount > 0 ? Math.round(customer.completed_amount / customer.total_amount * 100) : 0 }}%
            </span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ 
                width: customer.total_amount > 0 ? (customer.completed_amount / customer.total_amount * 100) + '%' : '0%',
                background: `linear-gradient(90deg, ${customer.customer_color}, ${customer.customer_color}dd)`
              }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const dateRange = ref([new Date().toISOString().slice(0, 10), new Date().toISOString().slice(0, 10)])

const dashboardData = reactive({
  customers: [],
  grand_total: 0,
  grand_completed: 0,
  grand_pending: 0
})

function formatAmount(amount) {
  return Math.round(amount).toLocaleString()
}

async function loadData() {
  try {
    const res = await axios.get(`/api/task-detail/dashboard`, {
      params: { 
        start_date: dateRange.value[0], 
        end_date: dateRange.value[1] 
      }
    })
    Object.assign(dashboardData, res.data.data)
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  min-height: 100vh;
  background: #f5f7fa;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
  padding: 0 4px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  font-size: 40px;
  line-height: 1;
}

.dashboard-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 14px;
  color: #9ca3af;
  margin: 4px 0 0 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.summary-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

.summary-card.total::before {
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.summary-card.completed::before {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.summary-card.pending::before {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.summary-card.failed::before {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card-icon {
  font-size: 36px;
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #f3f4f6;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
  line-height: 1.2;
}

.summary-label {
  font-size: 14px;
  color: #9ca3af;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 0 4px;
}

.title-bar {
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: 2px;
}

.section-title span:last-child {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
}

.customer-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 24px;
}

.customer-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
}

.customer-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.customer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid;
}

.customer-name {
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.name-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.customer-total {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.total-value {
  font-size: 22px;
  font-weight: 700;
}

.total-label {
  font-size: 12px;
  color: #9ca3af;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 24px;
}

.card-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #f9fafb;
  border-radius: 10px;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bank-name {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
}

.card-no {
  font-size: 12px;
  color: #9ca3af;
  font-family: monospace;
}

.card-amount {
  display: flex;
  gap: 16px;
}

.amount-item {
  text-align: right;
}

.amount-value {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.2;
}

.amount-value.total-val {
  color: #374151;
}

.amount-value.completed-val {
  color: #10b981;
}

.amount-value.pending-val {
  color: #f59e0b;
}

.amount-label {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.customer-progress {
  padding: 0 24px 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #6b7280;
}

.progress-percent {
  font-weight: 600;
  font-size: 14px;
}

.progress-bar {
  height: 8px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
</style>
