<template>
  <div class="location-graph-page">
    <n-page-header @back="handleBack" title="地点关系图">
      <template #extra>
        <n-space>
          <n-button @click="handleRefresh" :loading="loading">
            <template #icon>
              <n-icon><RefreshOutline /></n-icon>
            </template>
            刷新
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <div class="graph-body">
      <div class="graph-main">
        <LocationRelationGraph
          v-if="novelId"
          :slug="novelId"
          @loading="loading = $event"
          @node-click="handleNodeClick"
        />
      </div>
      <aside class="graph-side">
        <n-tabs v-model:value="activeTab" type="segment" animated>
          <n-tab-pane name="node" tab="地点详情">
            <div v-if="selectedNode" class="side-form">
              <n-descriptions label-placement="left" :column="1" bordered size="small">
                <n-descriptions-item label="名称">{{ selectedNode.name }}</n-descriptions-item>
                <n-descriptions-item label="类型" v-if="selectedNode.location_type">
                  {{ locationTypeLabel(selectedNode.location_type) }}
                </n-descriptions-item>
                <n-descriptions-item label="重要程度" v-if="selectedNode.importance">
                  <n-tag :type="importanceTagType(selectedNode.importance)" size="small">
                    {{ importanceLabel(selectedNode.importance) }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="描述" v-if="selectedNode.description">
                  {{ selectedNode.description }}
                </n-descriptions-item>
                <n-descriptions-item label="首次出现" v-if="selectedNode.first_appearance">
                  第 {{ selectedNode.first_appearance }} 章
                </n-descriptions-item>
                <n-descriptions-item label="相关章节" v-if="selectedNode.related_chapters?.length">
                  <n-space size="small">
                    <n-tag v-for="ch in selectedNode.related_chapters" :key="ch" size="small">
                      第 {{ ch }} 章
                    </n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="标签" v-if="selectedNode.tags?.length">
                  <n-space size="small">
                    <n-tag v-for="tag in selectedNode.tags" :key="tag" size="small" type="info">
                      {{ tag }}
                    </n-tag>
                  </n-space>
                </n-descriptions-item>
                <n-descriptions-item label="属性" v-if="selectedNode.attributes && Object.keys(selectedNode.attributes).length">
                  <div class="attributes-list">
                    <div v-for="(value, key) in selectedNode.attributes" :key="key" class="attr-item">
                      <span class="attr-key">{{ key }}:</span>
                      <span class="attr-value">{{ value }}</span>
                    </div>
                  </div>
                </n-descriptions-item>
              </n-descriptions>
            </div>
            <n-empty v-else description="点击图中节点查看地点详情" size="small" style="margin-top: 40px;" />
          </n-tab-pane>
        </n-tabs>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NPageHeader, NButton, NSpace, NIcon, NTabs, NTabPane, NDescriptions, NDescriptionsItem, NTag, NEmpty } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import LocationRelationGraph from '../components/LocationRelationGraph.vue'
import type { EChartsNode } from '../utils/visToEcharts'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const activeTab = ref<'node'>('node')

interface LocationNode extends EChartsNode {
  location_type?: string
  importance?: string
  description?: string
  first_appearance?: number
  related_chapters?: number[]
  tags?: string[]
  attributes?: Record<string, any>
}

const selectedNode = ref<LocationNode | null>(null)

const novelId = computed(() => route.params.slug as string)

const handleBack = () => {
  router.push(`/book/${novelId.value}/workbench`)
}

const handleRefresh = () => {
  window.location.reload()
}

const handleNodeClick = (node: EChartsNode) => {
  selectedNode.value = node as LocationNode
  activeTab.value = 'node'
}

const locationTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    city: '城市',
    region: '区域',
    building: '建筑',
    faction: '势力',
    realm: '境界/领域'
  }
  return labels[type] || type
}

const importanceLabel = (importance: string) => {
  const labels: Record<string, string> = {
    core: '核心地点',
    important: '重要地点',
    normal: '一般地点'
  }
  return labels[importance] || importance
}

const importanceTagType = (importance: string) => {
  const types: Record<string, 'success' | 'warning' | 'default'> = {
    core: 'success',
    important: 'warning',
    normal: 'default'
  }
  return types[importance] || 'default'
}
</script>

<style scoped>
.location-graph-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.graph-body {
  flex: 1;
  min-height: 0;
  display: flex;
}

.graph-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  padding: 16px;
  background: #f5f5f5;
}

.graph-side {
  width: min(400px, 42vw);
  flex-shrink: 0;
  padding: 12px;
  overflow: auto;
  background: #fff;
  border-left: 1px solid #e5e7eb;
}

.side-form {
  padding-top: 8px;
}

.attributes-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attr-item {
  display: flex;
  gap: 8px;
  font-size: 13px;
}

.attr-key {
  font-weight: 500;
  color: #64748b;
}

.attr-value {
  color: #0f172a;
}
</style>
