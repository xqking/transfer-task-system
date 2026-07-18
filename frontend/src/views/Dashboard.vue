<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h2>任务大屏</h2>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="loadData"
      />
    </div>

    <div class="summary-cards">
      <div class="summary-card total">
        <div class="summary-value">¥{{ formatAmount(dashboardData.grand_total) }}</div>
        <div class="summary-label">总金额</div>
      </div>
      <div class="summary-card completed">
        <div class="summary-value">¥{{ formatAmount(dashboardData.grand_completed) }}</div>
        <div class="summary-label">已完成</div>
      </div>
      <div class="summary-card pending">
        <div class="summary-value">¥{{ formatAmount(dashboardData.grand_pending) }}</div>
        <div class="summary-label">待完成</div>
      </div>
    </div>

    <div class="customer-cards">
      <div 
        v-for="customer in dashboardData.customers" 
        :key="customer.customer_id" 
        class="customer-card"
        :style="{ borderLeftColor: customer.customer_color }"
      >
        <div class="customer-header">
          <div class="customer-name">{{ customer.customer_name }}</div>
          <div class="customer-total">
            <span class="total-label">总金额：</span>
            <span class="total-value">¥{{ formatAmount(customer.total_amount) }}</span>
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
              <div class="amount-row">
                <span class="amount-label">总金额：</span>
                <span class="amount-value">¥{{ formatAmount(card.total_amount) }}</span>
              </div>
              <div class="amount-row">
                <span class="amount-label completed-label">已完成：</span>
                <span class="amount-value completed-value">¥{{ formatAmount(card.completed_amount) }}</span>
              </div>
              <div class="amount-row">
                <span class="amount-label pending-label">待完成：</span>
                <span class="amount-value pending-value">¥{{ formatAmount(card.pending_amount) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="customer-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ 
                width: customer.total_amount > 0 ? (customer.completed_amount / customer.total_amount * 100) + '%' : '0%',
                backgroundColor: customer.customer_color 
              }"
            ></div>
          </div>
          <div class="progress-text">
            完成率：{{ customer.total_amount > 0 ? Math.round(customer.completed_amount / customer.total_amount * 100) : 0 }}%
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
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h2 {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.summary-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.summary-card {
  flex: 1;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.summary-card.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.summary-card.completed {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.summary-card.pending {
  background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
}

.summary-value {
  font-size: 32px;
  font-weight: bold;
  color: white;
  margin-bottom: 8px;
}

.summary-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.customer-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.customer-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 20px;
  border-left: 4px solid #409EFF;
}

.customer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.customer-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.customer-total {
  font-size: 14px;
  color: #606266;
}

.total-value {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.card-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bank-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.card-no {
  font-size: 12px;
  color: #909399;
}

.card-amount {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: right;
}

.amount-row {
  font-size: 13px;
}

.amount-label {
  color: #909399;
}

.amount-value {
  font-weight: bold;
  color: #303133;
}

.completed-label {
  color: #67c23a;
}

.completed-value {
  color: #67c23a;
}

.pending-label {
  color: #e6a23c;
}

.pending-value {
  color: #e6a23c;
}

.customer-progress {
  margin-top: 16px;
}

.progress-bar {
  height: 6px;
  background: #ebeef5;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}
</style>
