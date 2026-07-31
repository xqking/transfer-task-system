<template>
  <div class="person-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>人员管理</span>
          <div>
            <el-checkbox v-model="showAll" @change="toggleShowAll">显示全部（含已删除）</el-checkbox>
            <el-button type="primary" @click="showAddDialog" :icon="Plus" style="margin-left: 12px;">添加人员</el-button>
          </div>
        </div>
      </template>

      <el-table :data="personList" stripe style="width: 100%">
        <el-table-column prop="name" label="姓名" width="200" />
        <el-table-column prop="status" label="状态" width="150">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '可用' : '不可用' }}
            </el-tag>
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
        <el-form-item label="姓名" required>
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="状态" required>
          <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%;">
            <el-option label="可用" :value="1" />
            <el-option label="不可用" :value="0" />
          </el-select>
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
const showAll = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = ref({
  name: '',
  status: 1
})

onMounted(loadPersonList)

async function loadPersonList() {
  try {
    const url = showAll.value ? '/api/person/list?show_all=1' : '/api/person/list'
    const res = await axios.get(url)
    personList.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

function toggleShowAll() {
  showAll.value = !showAll.value
  loadPersonList()
}

function showAddDialog() {
  isEdit.value = false
  editId.value = null
  form.value = {
    name: '',
    status: 1
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
  if (!form.value.name) {
    ElMessage.warning('请填写姓名')
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
