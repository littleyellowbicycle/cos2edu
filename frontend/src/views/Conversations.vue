<template>
  <div class="conversations">
    <el-container>
      <el-header>
        <h1>对话历史</h1>
        <el-button @click="$router.push('/')">返回首页</el-button>
      </el-header>
      <el-main>
        <el-table :data="conversations" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="character_id" label="角色ID" width="100" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" type="primary" @click="continueChat(scope.row)">继续对话</el-button>
              <el-button size="small" type="danger" @click="deleteConversation(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConversationStore } from '@/stores/conversation'
import { ElMessage } from 'element-plus'

const router = useRouter()
const store = useConversationStore()
const conversations = ref([])

onMounted(async () => {
  await store.fetchAll()
  conversations.value = store.conversations
})

function continueChat(conversation) {
  router.push(`/chat/${conversation.character_id}?conversationId=${conversation.id}`)
}

async function deleteConversation(id) {
  try {
    await store.delete(id)
    conversations.value = store.conversations
    ElMessage.success('删除成功')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.conversations {
  height: 100vh;
}
.el-header {
  background-color: #E6A23C;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>