<template>
  <div class="chapter-status-panel">
    <n-empty v-if="!chapter" description="请从左侧选择一个章节" style="margin-top: 48px" />

    <n-space v-else vertical :size="16" style="width: 100%; padding: 8px 4px">
      <n-card title="本章概览" size="small" :bordered="false">
        <n-descriptions :column="1" label-placement="left" size="small">
          <n-descriptions-item label="章节号">第 {{ chapter.number }} 章</n-descriptions-item>
          <n-descriptions-item label="标题">{{ chapter.title || '（无标题）' }}</n-descriptions-item>
          <n-descriptions-item label="收稿状态">
            <n-tag :type="chapter.word_count > 0 ? 'success' : 'default'" size="small" round>
              {{ chapter.word_count > 0 ? '已收稿' : '未收稿' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="正文字数">{{ chapter.word_count ?? 0 }} 字</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-alert v-if="readOnly" type="warning" :show-icon="true" title="托管运行中">
        全托管正在执行时，辅助撰稿区仅可阅读正文与关联信息，无法保存或改稿。请停止托管后再编辑。
      </n-alert>

      <n-text v-else depth="3" style="font-size: 12px">
        此处汇总当前章在结构中的基本状态；细粒度张力、文风等请在中栏「托管撰稿」下的监控大盘查看。
      </n-text>
    </n-space>
  </div>
</template>

<script setup lang="ts">
interface Chapter {
  id: number
  number: number
  title: string
  word_count: number
}

defineProps<{
  chapter: Chapter | null
  readOnly?: boolean
}>()
</script>

<style scoped>
.chapter-status-panel {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 12px 20px 20px;
}
</style>
