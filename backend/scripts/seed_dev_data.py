"""Insert a small set of realistic development topics/questions, plus (as of
Phase 10) the Category/Topic taxonomy.

Safe to run more than once: categories/topics are matched by name, questions
by (topic_id, question_text), so re-running this script never creates
duplicates. Existing topics from earlier phases are never renamed or
deleted — they're backfilled with a category_id (once, if not already set).

Requires the schema to already exist — run `alembic upgrade head` first.

Run from backend/: python -m scripts.seed_dev_data
"""

from app.database import SessionLocal
from app.models.category import Category
from app.models.question import DifficultyLevel, Question
from app.models.topic import Topic
from app.models.user import User
from app.services.auth_service import DEV_ADMIN_EMAIL, DEV_ADMIN_PASSWORD, hash_password

# The curated Category taxonomy (Phase 10). Kept small and manageable —
# see docs/architecture.md for why hierarchy matters.
CATEGORIES = [
    {
        "name": "AI & Machine Learning",
        "description": "Machine learning, deep learning, and generative AI",
    },
    {
        "name": "Software Engineering",
        "description": "Programming, backend development, APIs, and system design",
    },
    {
        "name": "DevOps & Cloud",
        "description": "Containers, CI/CD, orchestration, and cloud infrastructure",
    },
    {
        "name": "Data",
        "description": "Databases, data engineering, and data science",
    },
    {
        "name": "Business",
        "description": "Business, product, and SaaS fundamentals for engineers",
    },
]

# Backfill map: existing (Phase 4) topic name -> category name. These topics
# already exist with real questions attached — they are never renamed, only
# assigned a category_id if they don't already have one.
EXISTING_TOPIC_CATEGORY_MAP = {
    "AI/ML": "AI & Machine Learning",
    "Generative AI": "AI & Machine Learning",
    "Software Engineering": "Software Engineering",
    "Data Engineering": "Data",
    "DevOps": "DevOps & Cloud",
    "Cloud": "DevOps & Cloud",
    "Databases": "Data",
    "Business/Product": "Business",
}

# New, more granular topics (Phase 10) — deliberately small, not "hundreds."
# importance: 1=low, 2=normal, 3=important, 4=very important, 5=critical —
# how essential this topic is for an AI/software engineer in general.
NEW_TOPICS = [
    {"name": "LLMs", "description": "Large language models: how they work and are used", "category": "AI & Machine Learning", "importance": 5},
    {"name": "RAG", "description": "Retrieval-Augmented Generation: combining search with LLMs", "category": "AI & Machine Learning", "importance": 4},
    {"name": "AI Agents", "description": "Systems where an LLM plans and takes actions using tools", "category": "AI & Machine Learning", "importance": 4},
    {"name": "Deep Learning", "description": "Neural networks and the techniques behind modern AI", "category": "AI & Machine Learning", "importance": 4},
    {"name": "Python", "description": "The Python programming language", "category": "Software Engineering", "importance": 5},
    {"name": "Backend", "description": "Server-side application development", "category": "Software Engineering", "importance": 5},
    {"name": "APIs", "description": "Designing and consuming application programming interfaces", "category": "Software Engineering", "importance": 5},
    {"name": "Testing", "description": "Automated testing practices for software", "category": "Software Engineering", "importance": 4},
    {"name": "System Design", "description": "Designing large-scale, reliable software systems", "category": "Software Engineering", "importance": 5},
    {"name": "Docker", "description": "Containerizing applications for consistent deployment", "category": "DevOps & Cloud", "importance": 5},
    {"name": "Kubernetes", "description": "Orchestrating containers at scale", "category": "DevOps & Cloud", "importance": 4},
    {"name": "CI/CD", "description": "Automating testing and deployment pipelines", "category": "DevOps & Cloud", "importance": 4},
    {"name": "SQL", "description": "Querying and working with relational databases", "category": "Data", "importance": 5},
    {"name": "Data Science", "description": "Extracting insights from data using statistics and code", "category": "Data", "importance": 4},
    {"name": "SaaS", "description": "Software-as-a-Service business models", "category": "Business", "importance": 3},
    {"name": "Product", "description": "Product management and product thinking for engineers", "category": "Business", "importance": 3},
    {"name": "Business Fundamentals", "description": "Core business concepts relevant to engineers", "category": "Business", "importance": 3},
]

SEED_DATA = [
    {
        "name": "AI/ML",
        "description": "Artificial Intelligence and Machine Learning fundamentals",
        "questions": [
            {
                "question_text": "What is machine learning?",
                "answer": "Machine learning is a way of building software that learns patterns from data instead of following hand-written rules.",
                "simple_explanation": "Instead of programming every rule, you show the computer lots of examples and it figures out the pattern itself.",
                "real_world_example": "An email provider learns to flag spam by studying millions of emails people have already marked as spam.",
                "business_relevance": "Lets companies automate decisions (fraud detection, recommendations) that would be impossible to hand-code.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "machine learning, ai, model, training data",
            },
            {
                "question_text": "What is overfitting?",
                "answer": "Overfitting is when a model learns the training data too closely, including its noise, and performs poorly on new data.",
                "simple_explanation": "The model memorized the practice questions instead of learning the underlying concept.",
                "real_world_example": "A model trained on last year's sales data predicts perfectly for last year but fails on this year's trends.",
                "business_relevance": "An overfit model looks great in testing but makes bad real-world business decisions.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": "overfitting, generalization, model training",
            },
        ],
    },
    {
        "name": "Generative AI",
        "description": "Models that generate text, images, or other content",
        "questions": [
            {
                "question_text": "What is a large language model (LLM)?",
                "answer": "An LLM is a machine learning model trained on huge amounts of text that can generate and understand human language.",
                "simple_explanation": "It predicts the next word over and over, which lets it write coherent sentences and answer questions.",
                "real_world_example": "ChatGPT and Claude are LLMs used for writing, coding help, and answering questions.",
                "business_relevance": "Companies use LLMs to automate support, draft content, and summarize documents at scale.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "llm, generative ai, nlp",
            },
            {
                "question_text": "What is RAG (Retrieval-Augmented Generation)?",
                "answer": "RAG combines an LLM with a search step: relevant documents are retrieved and given to the model as context before it answers.",
                "simple_explanation": "Instead of relying only on what the model memorized during training, it 'looks things up' first, like an open-book exam.",
                "real_world_example": "A support chatbot retrieves your company's help docs and uses them to answer a customer's specific question accurately.",
                "business_relevance": "Reduces made-up answers ('hallucinations') and lets AI answer questions about private, up-to-date company data.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": "rag, retrieval, embeddings, llm",
            },
        ],
    },
    {
        "name": "Software Engineering",
        "description": "Principles and practices for building reliable software",
        "questions": [
            {
                "question_text": "What is version control?",
                "answer": "Version control is a system that tracks changes to code over time, so you can see history and collaborate without overwriting each other's work.",
                "simple_explanation": "It's like 'track changes' in a document, but for an entire codebase, with the ability to go back to any past version.",
                "real_world_example": "A team uses Git and GitHub so multiple engineers can work on the same project without losing each other's changes.",
                "business_relevance": "Prevents lost work, enables code review, and makes it possible to safely roll back a bad release.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "git, version control, collaboration",
            },
            {
                "question_text": "What is a design pattern?",
                "answer": "A design pattern is a reusable, well-known solution to a common software design problem.",
                "simple_explanation": "It's a proven template for solving a recurring problem, so you don't have to reinvent the solution each time.",
                "real_world_example": "The 'Singleton' pattern ensures only one database connection object exists across an entire application.",
                "business_relevance": "Using known patterns makes code easier for other engineers to understand and maintain, reducing long-term cost.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": "design pattern, software architecture",
            },
        ],
    },
    {
        "name": "Data Engineering",
        "description": "Building pipelines to move and transform data",
        "questions": [
            {
                "question_text": "What is ETL?",
                "answer": "ETL stands for Extract, Transform, Load — the process of pulling data from a source, cleaning/reshaping it, and loading it into a destination system.",
                "simple_explanation": "Extract = get the raw data. Transform = clean and reshape it. Load = save it somewhere useful, like a data warehouse.",
                "real_world_example": "A pipeline extracts daily sales from a store's point-of-sale system, cleans it, and loads it into a warehouse for reporting.",
                "business_relevance": "Reliable ETL is what makes accurate dashboards and business reporting possible.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "etl, data pipeline, data warehouse",
            },
            {
                "question_text": "What is a data pipeline?",
                "answer": "A data pipeline is a series of automated steps that move data from one system to another, often transforming it along the way.",
                "simple_explanation": "Think of it as a conveyor belt: data goes in one end, gets processed at each station, and comes out ready to use.",
                "real_world_example": "A pipeline moves clickstream events from a website into an analytics database every hour.",
                "business_relevance": "Automated pipelines mean fresh, trustworthy data is available for decisions without manual work.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "data pipeline, automation, data engineering",
            },
        ],
    },
    {
        "name": "DevOps",
        "description": "Practices that unify software development and IT operations",
        "questions": [
            {
                "question_text": "What is Docker?",
                "answer": "Docker is a tool that packages an application and its dependencies into a lightweight, portable container.",
                "simple_explanation": "A container is a box that includes everything an app needs to run, so it behaves the same on any machine.",
                "real_world_example": "A company packages its FastAPI application into a Docker image so it runs the same way on every developer's laptop and in production.",
                "business_relevance": "Docker makes deployments more consistent and reduces 'it works on my machine' bugs.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "docker, container, deployment",
            },
            {
                "question_text": "What is CI/CD?",
                "answer": "CI/CD stands for Continuous Integration and Continuous Delivery/Deployment — automatically testing and shipping code changes.",
                "simple_explanation": "Every time code changes, a pipeline automatically tests it and, if it passes, can even deploy it — no manual steps.",
                "real_world_example": "A GitHub Actions workflow runs tests on every pull request and deploys automatically when code merges to main.",
                "business_relevance": "Ships features faster and more safely by catching bugs early and removing manual deployment errors.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": "ci/cd, automation, devops, pipeline",
            },
        ],
    },
    {
        "name": "Cloud",
        "description": "Computing resources delivered over the internet",
        "questions": [
            {
                "question_text": "What is cloud computing?",
                "answer": "Cloud computing means renting computing resources (servers, storage, databases) over the internet instead of owning physical hardware.",
                "simple_explanation": "Instead of buying and maintaining your own computers, you pay a provider like AWS to use theirs, only when you need them.",
                "real_world_example": "A startup runs its entire app on AWS instead of buying and managing its own servers.",
                "business_relevance": "Removes large upfront hardware costs and lets companies scale resources up or down as demand changes.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "cloud computing, aws, infrastructure",
            },
            {
                "question_text": "What is the difference between IaaS, PaaS, and SaaS?",
                "answer": "IaaS gives you raw infrastructure (servers, networking), PaaS gives you a platform to deploy code without managing servers, and SaaS gives you a ready-to-use application.",
                "simple_explanation": "IaaS = rent the building. PaaS = rent a furnished office. SaaS = use a service someone else runs entirely, like Gmail.",
                "real_world_example": "AWS EC2 is IaaS, Heroku is PaaS, and Google Docs is SaaS.",
                "business_relevance": "Choosing the right layer affects how much engineering effort a company spends on infrastructure vs. its actual product.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": "iaas, paas, saas, cloud service models",
            },
        ],
    },
    {
        "name": "Databases",
        "description": "Systems for storing and querying structured data",
        "questions": [
            {
                "question_text": "What is a primary key?",
                "answer": "A primary key is a column (or set of columns) that uniquely identifies each row in a database table.",
                "simple_explanation": "It's like a unique ID number — no two rows in the table can share the same primary key value.",
                "real_world_example": "In a 'users' table, the 'id' column is the primary key, so every user has a unique identifier.",
                "business_relevance": "Primary keys let systems reliably reference specific records, e.g. linking an order to the correct customer.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "primary key, database, sql",
            },
            {
                "question_text": "What is database indexing?",
                "answer": "An index is a data structure that lets the database find rows matching a condition much faster than scanning the whole table.",
                "simple_explanation": "It's like the index at the back of a book — instead of reading every page, you jump straight to what you need.",
                "real_world_example": "Indexing the 'email' column on a users table makes login lookups fast even with millions of users.",
                "business_relevance": "Good indexing keeps an app fast as data grows; missing indexes are a common cause of slow, expensive queries.",
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "keywords": "index, database performance, sql",
            },
        ],
    },
    {
        "name": "Business/Product",
        "description": "Business, product, and SaaS fundamentals for engineers",
        "questions": [
            {
                "question_text": "What is MRR (Monthly Recurring Revenue)?",
                "answer": "MRR is the predictable revenue a business expects to receive every month from subscriptions.",
                "simple_explanation": "If 100 customers each pay $10/month, the business's MRR is $1,000.",
                "real_world_example": "A SaaS company tracks MRR growth month over month to measure how the business is performing.",
                "business_relevance": "MRR is one of the most important metrics investors and founders use to judge a subscription business's health.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "mrr, saas metrics, revenue",
            },
            {
                "question_text": "What is a SaaS business model?",
                "answer": "SaaS (Software as a Service) is a model where customers pay a recurring subscription to use software hosted by the provider, rather than buying and installing it themselves.",
                "simple_explanation": "Instead of buying software once, you pay monthly or yearly to keep using it, and the company handles hosting/updates.",
                "real_world_example": "Netflix, Slack, and Notion are all SaaS products — you subscribe instead of purchasing a copy.",
                "business_relevance": "SaaS creates predictable recurring revenue and ongoing customer relationships instead of one-time sales.",
                "difficulty": DifficultyLevel.BEGINNER,
                "keywords": "saas, business model, subscription",
            },
        ],
    },
]


def get_or_create_category(db, name: str, description: str) -> Category:
    category = db.query(Category).filter(Category.name == name).first()
    if category:
        return category
    category = Category(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def backfill_topic_category(db, topic_name: str, category: Category) -> bool:
    """Sets category_id on an existing topic only if it doesn't have one
    yet. Never overwrites an already-assigned category. Returns True if a
    change was made."""
    topic = db.query(Topic).filter(Topic.name == topic_name).first()
    if topic is None or topic.category_id is not None:
        return False
    topic.category_id = category.id
    db.commit()
    return True


def get_or_create_topic(
    db, name: str, description: str, category_id: int | None = None, importance: int = 3
) -> Topic:
    topic = db.query(Topic).filter(Topic.name == name).first()
    if topic:
        return topic
    topic = Topic(name=name, description=description, category_id=category_id, importance=importance)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def create_question_if_missing(db, topic: Topic, **fields) -> Question | None:
    exists = (
        db.query(Question)
        .filter(
            Question.topic_id == topic.id,
            Question.question_text == fields["question_text"],
        )
        .first()
    )
    if exists:
        return None
    question = Question(topic_id=topic.id, **fields)
    db.add(question)
    db.commit()
    return question


def get_or_create_dev_admin_user(db) -> User:
    """Phase 14: the local dev/admin account, identified by email (not
    username, which is now legacy — see app/models/user.py). Same
    credentials the Phase 14 migration backfills onto the pre-existing
    dev_user row, so a fresh database (seed script) and an upgraded
    existing one (migration) both end up with the same working login."""
    user = db.query(User).filter(User.email == DEV_ADMIN_EMAIL).first()
    if user:
        return user
    user = User(
        username="dev_user",
        email=DEV_ADMIN_EMAIL,
        password_hash=hash_password(DEV_ADMIN_PASSWORD),
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    db = SessionLocal()
    categories_created = 0
    topics_backfilled = 0
    topics_created = 0
    new_topics_created = 0
    questions_created = 0
    try:
        # 1. Categories (Phase 10 taxonomy).
        categories_by_name: dict[str, Category] = {}
        for category_data in CATEGORIES:
            existing_category = db.query(Category).filter(Category.name == category_data["name"]).first()
            category = get_or_create_category(db, category_data["name"], category_data["description"])
            categories_by_name[category.name] = category
            if existing_category is None:
                categories_created += 1

        # 2. Existing (Phase 4) topics + their questions — unchanged, plus a
        #    category_id backfill for any that don't have one yet.
        for topic_data in SEED_DATA:
            existing_topic = db.query(Topic).filter(Topic.name == topic_data["name"]).first()
            topic = get_or_create_topic(db, topic_data["name"], topic_data["description"])
            if existing_topic is None:
                topics_created += 1

            category_name = EXISTING_TOPIC_CATEGORY_MAP.get(topic_data["name"])
            if category_name and backfill_topic_category(db, topic_data["name"], categories_by_name[category_name]):
                topics_backfilled += 1

            for question_fields in topic_data["questions"]:
                created = create_question_if_missing(db, topic, **question_fields)
                if created:
                    questions_created += 1

        # 3. New, more granular topics (Phase 10) under the same categories.
        for topic_data in NEW_TOPICS:
            existing_new_topic = db.query(Topic).filter(Topic.name == topic_data["name"]).first()
            get_or_create_topic(
                db,
                topic_data["name"],
                topic_data["description"],
                category_id=categories_by_name[topic_data["category"]].id,
                importance=topic_data["importance"],
            )
            if existing_new_topic is None:
                new_topics_created += 1

        existing_user = db.query(User).filter(User.email == DEV_ADMIN_EMAIL).first()
        dev_user = get_or_create_dev_admin_user(db)

        print(f"Categories created: {categories_created} (of {len(CATEGORIES)} defined)")
        print(f"Existing topics created: {topics_created} (of {len(SEED_DATA)} defined)")
        print(f"Existing topics backfilled with a category: {topics_backfilled}")
        print(f"New topics created: {new_topics_created} (of {len(NEW_TOPICS)} defined)")
        print(f"Questions created: {questions_created}")
        print(
            f"Dev admin user: id={dev_user.id} email={dev_user.email!r} is_admin={dev_user.is_admin} "
            f"({'created' if existing_user is None else 'already existed'}) "
            "— see README.md for the dev password"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
