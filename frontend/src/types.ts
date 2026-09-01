export type Topic = {
  id: number
  name: string
  description: string | null
  category_id: number | null
  importance: number
  active: boolean
}

export type Category = {
  id: number
  name: string
  description: string | null
}

export type Question = {
  id: number
  topic_id: number
  question_text: string
  answer: string
  simple_explanation: string | null
  real_world_example: string | null
  business_relevance: string | null
  difficulty: string
  keywords: string | null
}

export type DailyLearning = {
  new_questions: Question[]
  revision_questions: Question[]
}

export type LearningProgressResult = {
  question_id: number
  first_learned_at: string
  last_reviewed_at: string
  review_count: number
  next_review_at: string
}

export type RecentActivityItem = {
  question_id: number
  question_text: string
  last_reviewed_at: string
  review_count: number
}

export type TopicProgress = {
  topic_id: number
  topic_name: string
  learned_count: number
  total_questions: number
}

export type DashboardData = {
  learned_count: number
  due_revision_count: number
  new_available_count: number
  total_approved_questions: number
  progress_percent: number
  mastered_count: number
  total_reviews_completed: number
  current_streak_days: number
  difficulty_breakdown: Record<string, number>
  recent_activity: RecentActivityItem[]
  topics_in_progress: TopicProgress[]
}

export type ChatMessageDTO = {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export type ChatSessionSummaryDTO = {
  id: number
  title: string
  question_id: number | null
  created_at: string
  updated_at: string
}

export type ChatSessionDetailDTO = ChatSessionSummaryDTO & { messages: ChatMessageDTO[] }

export type SourceArticle = {
  id: number
  source_name: string
  title: string
  published_at: string | null
}

export type PipelineStatus = {
  total_source_articles: number
  classified_articles: number
  eligible_candidates: number
  pending_drafts: number
  approved_questions: number
  rejected_drafts: number
  target_new_pool_size: number
  pool_status: 'healthy' | 'needs_content'
  recommended_generation_count: number
  available_new_questions: number | null
  due_revision_count: number | null
}

export type Candidate = {
  article_id: number
  title: string
  category_name: string | null
  topic_name: string | null
  importance_score: number
  relevance_score: number
  freshness_score: number
  selection_score: number
}

export type AIDraft = {
  id: number
  source_article_id: number
  question_text: string
  answer: string
  simple_explanation: string
  real_world_example: string
  business_relevance: string
  difficulty: string
  keywords: string | null
  model_name: string
  status: 'generated' | 'approved' | 'rejected'
  created_at: string
  reviewed_at: string | null
  source_article_title: string
  source_article_topic_name: string | null
  source_article_relevance_score: number | null
}
