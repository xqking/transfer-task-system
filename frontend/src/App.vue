<template>
  <el-container class="layout-container">
    <el-header class="header">
      <div class="logo">转账任务分发系统</div>
      <el-menu
        mode="horizontal"
        :default-active="$route.path"
        router
        class="nav-menu"
        :ellipsis="false"
      >
        <el-menu-item index="/">首页</el-menu-item>
        <el-menu-item index="/person">人员管理</el-menu-item>
        <el-menu-item index="/customer">客户管理</el-menu-item>
        <el-menu-item index="/bankcard">银行卡管理</el-menu-item>
        <el-menu-item index="/task">转账任务</el-menu-item>
      </el-menu>
    </el-header>
    <el-main class="main-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.layout-container {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: visible;
  height: 60px;
}

.logo {
  color: white;
  font-size: 20px;
  font-weight: bold;
  white-space: nowrap;
  flex-shrink: 0;
  height: 60px;
  line-height: 60px;
  display: flex;
  align-items: center;
  padding: 0 32px;
  background: rgba(255,255,255,0.1);
  margin: 0;
  border: none;
}

.nav-menu {
  background: transparent !important;
  border-bottom: none !important;
  flex: 1;
  min-width: 0;
  overflow: visible;
  padding: 0 !important;
  margin: 0 !important;
}

.nav-menu.el-menu--horizontal {
  height: 60px !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
}

.nav-menu .el-menu-item {
  color: rgba(255,255,255,0.9);
  border-bottom: none !important;
  padding: 0 32px !important;
  height: 60px !important;
  line-height: 60px !important;
  display: flex !important;
  align-items: center !important;
  min-width: 140px;
  justify-content: center !important;
  margin: 0 !important;
  border: none !important;
  box-shadow: none !important;
  overflow: visible !important;
  background: transparent !important;
}

.nav-menu .el-menu-item::before {
  display: none !important;
}

.nav-menu .el-menu-item::after {
  display: none !important;
}

.nav-menu .el-menu-item.is-active::after {
  display: none !important;
}

.nav-menu .el-menu-item.is-active {
  border-bottom: none !important;
}

.nav-menu .el-menu-item:hover,
.nav-menu .el-menu-item.is-active {
  color: white !important;
  background: rgba(255,255,255,0.15) !important;
}

.main-content {
  background: #f5f6fa;
  padding: 20px;
}
</style>