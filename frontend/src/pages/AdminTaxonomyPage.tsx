import { useEffect, useState } from 'react'
import { fetchAllTopics, fetchCategories } from '../api/admin'
import { ErrorState, Skeleton } from '../components/Feedback'
import type { Category, Topic } from '../types'
import './AdminPages.css'

function AdminTaxonomyPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchCategories(), fetchAllTopics()])
      .then(([categoryData, topicData]) => {
        setCategories(categoryData)
        setTopics(topicData)
      })
      .catch(() => setError('Could not load taxonomy'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="admin-page">
      <h1>Categories &amp; Topics</h1>
      <p className="admin-subtitle">The curated taxonomy that structures all learning content.</p>

      {error && <ErrorState message={error} />}

      {loading ? (
        <Skeleton height={200} />
      ) : (
        categories.map((category) => (
          <div className="admin-card" key={category.id}>
            <h2>{category.name}</h2>
            {category.description && <p className="admin-subtitle">{category.description}</p>}
            <ul className="admin-list">
              {topics
                .filter((t) => t.category_id === category.id)
                .map((t) => (
                  <li key={t.id}>
                    {t.name} <span className="admin-list-meta">(importance {t.importance}{!t.active && ', inactive'})</span>
                  </li>
                ))}
            </ul>
          </div>
        ))
      )}
    </div>
  )
}

export default AdminTaxonomyPage
