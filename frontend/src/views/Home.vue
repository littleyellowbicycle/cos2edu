<template>
  <div class="home">
    <el-container>
      <el-header>
        <h1>苏格拉底AI教学系统</h1>
      </el-header>
      <el-main>
        <el-card>
          <template #header>
            <h2>欢迎使用</h2>
          </template>
          <el-space wrap>
            <el-button type="primary" @click="$router.push('/characters')">角色管理</el-button>
            <el-button type="success" @click="$router.push('/materials')">教材管理</el-button>
            <el-button type="warning" @click="$router.push('/conversations')">对话历史</el-button>
          </el-space>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home {
  height: 100vh;
}
.el-header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
}
.el-main {
  padding: 20px;
}
</style>