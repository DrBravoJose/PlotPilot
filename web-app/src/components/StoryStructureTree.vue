<template>
  <div class="story-structure">
    <div class="structure-header">
      <h3>叙事结构</h3>
      <n-space>
        <n-button
          size="small"
          type="primary"
          @click="handleCreateDefault"
          :loading="loading"
          v-if="!hasStructure"
        >
          创建默认结构
        </n-button>
        <n-button
          size="small"
          @click="handleRefresh"
          :loading="loading"
        >
          刷新
        </n-button>
      </n-space>
    </div>

    <div class="structure-body" v-if="treeData.length > 0">
      <n-tree
        :data="treeData"
        :node-props="nodeProps"
        :render-label="renderLabel"
        :render-suffix="renderSuffix"
        block-line
        expand-on-click
        selectable
        @update:selected-keys="handleSelect"
      />
    </div>

    <n-empty
      v-else-if="!loading"
      description="暂无叙事结构"
      class="structure-empty"
    >
      <template #extra>
        <n-button size="small" @click="handleCreateDefault">
          创建默认结构
        </n-button>
      </template>
    </n-empty>

    <!-- 节点编辑对话框 -->
    <n-modal
      v-model:show="showEditModal"
      preset="dialog"
      title="编辑节点"
      positive-text="保存"
      negative-text="取消"
      @positive-click="handleSaveNode"
    >
      <n-form :model="editForm" label-placement="left" label-width="80">
        <n-form-item label="标题">
          <n-input v-model:value="editForm.title" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input
            v-model:value="editForm.description"
            type="textarea"
            :rows="3"
          />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { NTree, NButton, NSpace, NEmpty, NModal, NForm, NFormItem, NInput, NIcon, useMessage, useDialog } from 'naive-ui'
import { structureApi, type StoryNode } from '@/api/structure'
import { BookOutline, FolderOpenOutline, FilmOutline } from '@vicons/ionicons5'

const props = defineProps<{
  slug: string
}>()

const emit = defineEmits<{
  select: [node: StoryNode]
}>()

const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const treeData = ref<StoryNode[]>([])
const selectedNode = ref<StoryNode | null>(null)
const showEditModal = ref(false)
const editForm = ref({
  title: '',
  description: ''
})

const hasStructure = computed(() => treeData.value.length > 0)

// 加载结构树
const loadTree = async () => {
  loading.value = true
  try {
    const res = await structureApi.getTree(props.slug)
    treeData.value = res.tree
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '加载结构失败')
  } finally {
    loading.value = false
  }
}

// 创建默认结构
const handleCreateDefault = () => {
  dialog.warning({
    title: '创建默认结构',
    content: '将创建一个包含 3 部、每部 3 卷的默认叙事结构（适合 100 章左右的小说）。',
    positiveText: '创建',
    negativeText: '取消',
    onPositiveClick: async () => {
      loading.value = true
      try {
        await structureApi.createDefaultStructure(props.slug, 100)
        message.success('默认结构创建成功')
        await loadTree()
      } catch (e: any) {
        message.error(e?.response?.data?.detail || '创建失败')
      } finally {
        loading.value = false
      }
    }
  })
}

// 刷新
const handleRefresh = () => {
  loadTree()
}

// 选择节点
const handleSelect = (keys: string[]) => {
  if (keys.length > 0) {
    const findNode = (nodes: StoryNode[], id: string): StoryNode | null => {
      for (const node of nodes) {
        if (node.id === id) return node
        if (node.children) {
          const found = findNode(node.children, id)
          if (found) return found
        }
      }
      return null
    }

    const node = findNode(treeData.value, keys[0])
    if (node) {
      selectedNode.value = node
      emit('select', node)
    }
  }
}

// 渲染节点标签
const renderLabel = ({ option }: { option: StoryNode }) => {
  return h('span', { class: 'node-label' }, [
    h('span', { class: 'node-icon' }, option.icon),
    h('span', { class: 'node-title' }, option.display_name)
  ])
}

// 渲染节点后缀（章节范围）
const renderSuffix = ({ option }: { option: StoryNode }) => {
  if (option.chapter_start && option.chapter_end) {
    return h('span', { class: 'node-range' },
      `${option.chapter_start}-${option.chapter_end}章 (${option.chapter_count})`
    )
  }
  return null
}

// 节点属性
const nodeProps = ({ option }: { option: StoryNode }) => {
  return {
    class: `node-level-${option.level}`
  }
}

// 编辑节点
const handleEditNode = (node: StoryNode) => {
  selectedNode.value = node
  editForm.value = {
    title: node.title,
    description: node.description || ''
  }
  showEditModal.value = true
}

// 保存节点
const handleSaveNode = async () => {
  if (!selectedNode.value) return

  loading.value = true
  try {
    await structureApi.updateNode(props.slug, selectedNode.value.id, {
      title: editForm.value.title,
      description: editForm.value.description
    })
    message.success('保存成功')
    showEditModal.value = false
    await loadTree()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '保存失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTree()
})
</script>

<style scoped>
.story-structure {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.structure-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
}

.structure-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.structure-body {
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.structure-empty {
  padding: 40px 0;
}

.node-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
}

.node-title {
  font-size: 13px;
}

.node-range {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.node-level-1 {
  font-weight: 600;
}

.node-level-2 {
  font-weight: 500;
}

.node-level-3 {
  font-weight: normal;
}
</style>
