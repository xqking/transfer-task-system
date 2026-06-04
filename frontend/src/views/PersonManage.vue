<template>
  <div class="person-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>人员管理</span>
          <el-button type="primary" @click="showAddDialog" :icon="Plus">添加人员</el-button>
        </div>
      </template>

      <el-table :data="personList" stripe style="width: 100%">
        <el-table-column prop="code" label="编号" width="150" />
        <el-table-column prop="name" label="姓名" width="150" />
        <el-table-column prop="single_min" label="单次最小金额" width="150">
          <template #default="{ row }">
            ¥{{ row.single_min }}
          </template>
        </el-table-column>
        <el-table-column prop="single_max" label="单次最大金额" width="150">
          <template #default="{ row }">
            ¥{{ row.single_max }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editPerson(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deletePerson(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑人员' : '添加人员'" width="500px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="人员编号" required>
          <el-input v-model="form.code" placeholder="如：001" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="单次最小金额">
          <el-input-number v-model="form.single_min" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="单次最大金额">
          <el-input-number v-model="form.single_max" :min="0" :step="100" />
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

const personList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({
  code: '',
  name: '',
  single_min: 2000,
  single_max: 6000
})

onMounted(loadPersonList)

async function loadPersonList() {
  try {
    const res = await axios.get('/api/person/list')
    personList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

function showAddDialog() {
  isEdit.value = false
  editId.value = null
  form.value = {
    code: '',
    name: '',
    single_min: 2000,
    single_max: 6000
  }
  dialogVisible.value = true
}

function editPerson(row) {
  isEdit.value = true
  editId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.value.code) {
    ElMessage.warning('请填写人员编号')
    return
  }
  
  try {
    if (isEdit.value) {
      await axios.put(`/api/person/update/${editId.value}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/person/add', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadPersonList()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

async function deletePerson(id) {
  try {
    await ElMessageBox.confirm('确定要删除该人员吗？', '提示', { type: 'warning' })
    await axios.delete(`/api/person/delete/${id}`)
    ElMessage.success('删除成功')
    loadPersonList()
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
</style>