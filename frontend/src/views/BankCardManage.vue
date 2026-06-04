<template>
  <div class="bankcard-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>银行卡管理</span>
          <el-button type="primary" @click="showAddDialog" :icon="Plus">添加银行卡</el-button>
        </div>
      </template>

      <el-table :data="cardList" stripe style="width: 100%">
        <el-table-column prop="customer_name" label="客户名称" width="150" />
        <el-table-column prop="bank_name" label="银行" width="120" />
        <el-table-column label="收款码" min-width="150">
          <template #default="{ row }">
            <div v-if="row.receive_code" class="receive-code-container">
              <img 
                v-if="isImage(row.receive_code)" 
                :src="getImageUrl(row.receive_code)" 
                alt="收款码" 
                class="receive-code-image"
                @click="previewImage(row.receive_code)"
              />
              <span v-else>{{ row.receive_code }}</span>
            </div>
            <span v-else class="empty-text">暂无收款码</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="showUpdateDialog(row)">修改收款码</el-button>
            <el-button size="small" type="danger" @click="deleteCard(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加银行卡弹窗 -->
    <el-dialog v-model="dialogVisible" title="添加银行卡" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择客户" required>
          <el-select v-model="form.customer_id" placeholder="请选择客户" style="width: 100%;" filterable>
            <el-option 
              v-for="c in customerList" 
              :key="c.id" 
              :label="c.name" 
              :value="c.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="银行" required>
          <el-select v-model="form.bank_id" placeholder="请选择银行" style="width: 100%;">
            <el-option 
              v-for="bank in bankList" 
              :key="bank.id" 
              :label="bank.name" 
              :value="bank.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="卡号" required>
          <el-input v-model="form.card_no" placeholder="请输入银行卡号" />
        </el-form-item>
        <el-form-item label="收款码">
          <div class="upload-area">
            <el-upload
              class="uploader"
              action="/api/bankcard/add"
              :headers="headers"
              :data="{ customer_id: form.customer_id, bank_id: form.bank_id, card_no: form.card_no }"
              :file-list="uploadFiles"
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              accept="image/*"
            >
              <el-button type="primary" :icon="Upload">上传收款码照片</el-button>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 修改收款码弹窗 -->
    <el-dialog v-model="updateDialogVisible" title="修改收款码" width="500px">
      <el-form :model="updateForm" label-width="100px">
        <el-form-item label="当前收款码">
          <div v-if="updateForm.receive_code" class="receive-code-container">
            <img 
              v-if="isImage(updateForm.receive_code)" 
              :src="getImageUrl(updateForm.receive_code)" 
              alt="收款码" 
              class="receive-code-image"
            />
            <span v-else>{{ updateForm.receive_code }}</span>
          </div>
          <span v-else class="empty-text">暂无收款码</span>
        </el-form-item>
        <el-form-item label="新收款码">
          <div class="upload-area">
            <el-upload
              class="uploader"
              :file-list="updateUploadFiles"
              :auto-upload="false"
              :on-change="handleUpdateFileChange"
              :on-remove="handleUpdateFileRemove"
              accept="image/*"
            >
              <el-button type="primary" :icon="Upload">上传收款码照片</el-button>
            </el-upload>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="updateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpdate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 图片预览弹窗 -->
    <el-dialog v-model="previewVisible" title="收款码预览" width="400px">
      <img :src="previewImageUrl" alt="收款码" class="preview-image" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const cardList = ref([])
const customerList = ref([])
const bankList = ref([])
const dialogVisible = ref(false)
const updateDialogVisible = ref(false)
const previewVisible = ref(false)
const previewImageUrl = ref('')

const form = ref({
  customer_id: '',
  bank_id: '',
  card_no: '',
  receive_code: ''
})

const updateForm = ref({
  id: '',
  receive_code: '',
  receive_code_text: ''
})

const uploadFiles = ref([])
const updateUploadFiles = ref([])

const headers = ref({})

onMounted(async () => {
  await Promise.all([loadCardList(), loadCustomers(), loadBanks()])
})

async function loadCardList() {
  try {
    const res = await axios.get('/api/bankcard/list')
    cardList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

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

function showAddDialog() {
  form.value = { customer_id: '', bank_id: '', card_no: '', receive_code: '' }
  uploadFiles.value = []
  dialogVisible.value = true
}

function showUpdateDialog(row) {
  updateForm.value = {
    id: row.id,
    receive_code: row.receive_code,
    receive_code_text: ''
  }
  updateUploadFiles.value = []
  updateDialogVisible.value = true
}

function previewImage(url) {
  previewImageUrl.value = getImageUrl(url)
  previewVisible.value = true
}

function isImage(url) {
  return url && (url.startsWith('/uploads/') || url.startsWith('http') || url.match(/\.(jpg|jpeg|png|gif|webp)$/i))
}

function getImageUrl(url) {
  if (!url) return ''
  if (url.startsWith('/uploads/')) {
    return `http://localhost:5001${url}`
  }
  return url
}

function handleFileChange(file, fileList) {
  uploadFiles.value = fileList
}

function handleFileRemove(file, fileList) {
  uploadFiles.value = fileList
}

function handleUpdateFileChange(file, fileList) {
  updateUploadFiles.value = fileList
}

function handleUpdateFileRemove(file, fileList) {
  updateUploadFiles.value = fileList
}

async function submitForm() {
  if (!form.value.customer_id || !form.value.bank_id || !form.value.card_no) {
    ElMessage.warning('请填写所有必填项')
    return
  }

  try {
    const formData = new FormData()
    formData.append('customer_id', form.value.customer_id)
    formData.append('bank_id', form.value.bank_id)
    formData.append('card_no', form.value.card_no)
    
    // 如果有上传的文件，添加文件
    if (uploadFiles.value.length > 0) {
      formData.append('receive_code_file', uploadFiles.value[0].raw)
    } else if (form.value.receive_code) {
      // 否则使用文本收款码
      formData.append('receive_code', form.value.receive_code)
    }

    await axios.post('/api/bankcard/add', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    ElMessage.success('添加成功')
    dialogVisible.value = false
    uploadFiles.value = []
    loadCardList()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function submitUpdate() {
  try {
    const formData = new FormData()
    
    // 如果有上传的文件，添加文件
    if (updateUploadFiles.value.length > 0) {
      formData.append('receive_code_file', updateUploadFiles.value[0].raw)
    } else if (updateForm.value.receive_code_text) {
      // 否则使用文本收款码
      formData.append('receive_code', updateForm.value.receive_code_text)
    } else {
      ElMessage.warning('请上传收款码照片或输入收款码文本')
      return
    }

    await axios.post(`/api/bankcard/update/${updateForm.value.id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    ElMessage.success('更新成功')
    updateDialogVisible.value = false
    updateUploadFiles.value = []
    loadCardList()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function deleteCard(id) {
  try {
    await ElMessageBox.confirm('确定要删除该银行卡吗？', '提示', { type: 'warning' })
    await axios.delete(`/api/bankcard/delete/${id}`)
    ElMessage.success('删除成功')
    loadCardList()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.receive-code-container {
  display: flex;
  align-items: center;
}

.receive-code-image {
  width: 100px;
  height: 100px;
  object-fit: contain;
  cursor: pointer;
  border: 1px solid #eee;
  border-radius: 4px;
}

.preview-image {
  width: 100%;
  max-height: 400px;
  object-fit: contain;
}

.empty-text {
  color: #999;
  font-size: 12px;
}

.upload-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.uploader {
  margin-bottom: 8px;
}

.code-input {
  width: 100%;
}
</style>
