<template>
  <div class="customer-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>客户管理</span>
          <el-button type="primary" @click="showAddDialog" :icon="Plus">添加客户</el-button>
        </div>
      </template>

      <el-table :data="customerList" stripe style="width: 100%" :row-style="getRowStyle">
        <el-table-column label="颜色" width="100" align="center">
          <template #default="{ row }">
            <span class="color-swatch" :style="{ backgroundColor: row.color }" :title="row.color" />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="客户名称" min-width="200">
          <template #default="{ row }">
            <span class="customer-name" :style="{ color: row.color }">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editCustomer(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCustomer(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑客户' : '添加客户'" width="450px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="客户名称" required>
          <el-input v-model="form.name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="标识颜色" required>
          <div class="color-picker-row">
            <el-color-picker v-model="form.color" :predefine="colorPalette" />
            <span
              v-for="c in colorPalette"
              :key="c"
              class="color-option"
              :class="{ active: form.color === c }"
              :style="{ backgroundColor: c }"
              @click="form.color = c"
            />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const customerList = ref([])
const colorPalette = ref([
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C',
  '#9B59B6', '#00CED1', '#FF85C0', '#909399'
])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({ name: '', color: '#409EFF' })

onMounted(async () => {
  await loadColorPalette()
  loadCustomerList()
})

async function loadColorPalette() {
  try {
    const res = await axios.get('/api/customer/colors')
    if (res.data.data?.length) {
      colorPalette.value = res.data.data
    }
  } catch (e) {
    console.error(e)
  }
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

function getRowStyle({ row }) {
  const { r, g, b } = hexToRgb(row.color)
  return { backgroundColor: `rgba(${r}, ${g}, ${b}, 0.08)` }
}

async function loadCustomerList() {
  try {
    const res = await axios.get('/api/customer/list')
    customerList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

function nextDefaultColor() {
  const used = new Set(customerList.value.map(c => c.color))
  return colorPalette.value.find(c => !used.has(c)) || colorPalette.value[0]
}

function showAddDialog() {
  isEdit.value = false
  editId.value = null
  form.value = { name: '', color: nextDefaultColor() }
  dialogVisible.value = true
}

function editCustomer(row) {
  isEdit.value = true
  editId.value = row.id
  form.value = { name: row.name, color: row.color || '#409EFF' }
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.value.name) {
    ElMessage.warning('请输入客户名称')
    return
  }
  if (!form.value.color) {
    ElMessage.warning('请选择标识颜色')
    return
  }

  try {
    if (isEdit.value) {
      await axios.put(`/api/customer/update/${editId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/customer/add', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadCustomerList()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function deleteCustomer(id) {
  try {
    await ElMessageBox.confirm('确定要删除该客户吗？', '提示', { type: 'warning' })
    await axios.delete(`/api/customer/delete/${id}`)
    ElMessage.success('删除成功')
    loadCustomerList()
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

.color-swatch {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid rgba(0, 0, 0, 0.08);
  vertical-align: middle;
}

.customer-name {
  font-weight: 600;
}

.color-picker-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.color-option {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.15s;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.active {
  border-color: #303133;
  box-shadow: 0 0 0 2px #fff, 0 0 0 4px currentColor;
}
</style>
