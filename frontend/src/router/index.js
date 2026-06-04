import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PersonManage from '../views/PersonManage.vue'
import CustomerManage from '../views/CustomerManage.vue'
import BankCardManage from '../views/BankCardManage.vue'
import TransferTask from '../views/TransferTask.vue'
import HistoryTask from '../views/HistoryTask.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/person',
    name: 'PersonManage',
    component: PersonManage
  },
  {
    path: '/customer',
    name: 'CustomerManage',
    component: CustomerManage
  },
  {
    path: '/bankcard',
    name: 'BankCardManage',
    component: BankCardManage
  },
  {
    path: '/task',
    name: 'TransferTask',
    component: TransferTask
  },
  {
    path: '/history',
    name: 'HistoryTask',
    component: HistoryTask
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
