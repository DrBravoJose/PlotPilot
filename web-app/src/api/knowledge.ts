import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

request.interceptors.response.use(response => response.data)

// TypeScript interfaces
export interface ChapterSummary {
  chapter_id: number
  summary: string
  key_events: string
  open_threads: string
  consistency_note: string
  beat_sections: string[]
  sync_status: string
}

export interface KnowledgeTriple {
  id: string
  subject: string
  predicate: string
  object: string
  chapter_id: number | null
  note: string
  entity_type?: 'character' | 'location'
  importance?: 'primary' | 'secondary' | 'minor' | 'core' | 'important' | 'normal'
  location_type?: 'city' | 'region' | 'building' | 'faction' | 'realm'
  description?: string
  first_appearance?: number
  related_chapters?: number[]
  tags?: string[]
  attributes?: Record<string, any>
}

export interface StoryKnowledge {
  version: number
  premise_lock: string
  chapters: ChapterSummary[]
  facts: KnowledgeTriple[]
}

export interface KnowledgeSearchHit {
  id: string
  text: string
  meta?: {
    type?: string
    id?: string
    [key: string]: any
  }
}

export interface KnowledgeSearchResponse {
  hits: KnowledgeSearchHit[]
}

export const knowledgeApi = {
  /**
   * Get knowledge graph for a novel
   */
  getKnowledge: (novelId: string) =>
    request.get(`/novels/${novelId}/knowledge`) as Promise<StoryKnowledge>,

  /**
   * Update knowledge graph for a novel
   */
  updateKnowledge: (novelId: string, data: StoryKnowledge) =>
    request.put(`/novels/${novelId}/knowledge`, data) as Promise<StoryKnowledge>,

  /**
   * Search knowledge graph
   */
  searchKnowledge: (novelId: string, query: string, k = 6) =>
    request.get(`/novels/${novelId}/knowledge/search`, {
      params: { q: query, k }
    }) as Promise<KnowledgeSearchResponse>,

  /**
   * AI generate (or regenerate) initial Knowledge for a novel
   * POST /api/v1/novels/{novelId}/knowledge/generate
   */
  generateKnowledge: (novelId: string) =>
    request.post<{ success: boolean; message: string; facts_count: number; premise_lock: string }>(
      `/novels/${novelId}/knowledge/generate`,
      {},
      { timeout: 120_000 }
    ) as Promise<{ success: boolean; message: string; facts_count: number; premise_lock: string }>,
}
