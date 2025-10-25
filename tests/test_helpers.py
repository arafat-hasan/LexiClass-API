"""Helper functions for generating test data."""

from typing import List, Dict, Optional
from faker import Faker
import random

fake = Faker()


class DocumentGenerator:
    """Generate realistic test documents."""

    # Sample categories for document classification
    CATEGORIES = [
        "Technology",
        "Business",
        "Health",
        "Sports",
        "Entertainment",
        "Politics",
        "Science",
        "Education",
    ]

    @classmethod
    def generate_document(
        cls,
        category: Optional[str] = None,
        min_words: int = 50,
        max_words: int = 500,
    ) -> Dict[str, any]:
        """Generate a single realistic document.

        Args:
            category: Document category/label (random if None)
            min_words: Minimum number of words in content
            max_words: Maximum number of words in content

        Returns:
            Dictionary with document data
        """
        if category is None:
            category = random.choice(cls.CATEGORIES)

        # Generate content based on category
        content = cls._generate_content_for_category(
            category,
            min_words,
            max_words
        )

        return {
            "content": content,
            "label": category,
            "metadata": {
                "title": fake.sentence(nb_words=6),
                "author": fake.name(),
                "source": fake.company(),
                "date": fake.date_this_year().isoformat(),
                "category": category,
            }
        }

    @classmethod
    def generate_documents(
        cls,
        count: int,
        balanced: bool = True,
    ) -> List[Dict[str, any]]:
        """Generate multiple documents.

        Args:
            count: Number of documents to generate
            balanced: If True, distribute evenly across categories

        Returns:
            List of document dictionaries
        """
        documents = []

        if balanced:
            # Distribute evenly across categories
            docs_per_category = count // len(cls.CATEGORIES)
            remainder = count % len(cls.CATEGORIES)

            for category in cls.CATEGORIES:
                category_count = docs_per_category
                if remainder > 0:
                    category_count += 1
                    remainder -= 1

                for _ in range(category_count):
                    documents.append(cls.generate_document(category=category))
        else:
            # Random distribution
            for _ in range(count):
                documents.append(cls.generate_document())

        return documents

    @classmethod
    def _generate_content_for_category(
        cls,
        category: str,
        min_words: int,
        max_words: int
    ) -> str:
        """Generate contextually relevant content for a category.

        Args:
            category: Document category
            min_words: Minimum words
            max_words: Maximum words

        Returns:
            Generated content text
        """
        # Category-specific content templates
        templates = {
            "Technology": cls._tech_content,
            "Business": cls._business_content,
            "Health": cls._health_content,
            "Sports": cls._sports_content,
            "Entertainment": cls._entertainment_content,
            "Politics": cls._politics_content,
            "Science": cls._science_content,
            "Education": cls._education_content,
        }

        generator = templates.get(category, cls._generic_content)
        return generator(min_words, max_words)

    @staticmethod
    def _tech_content(min_words: int, max_words: int) -> str:
        """Generate technology-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        tech_terms = [
            "artificial intelligence", "machine learning", "cloud computing",
            "blockchain", "cybersecurity", "data analytics", "IoT",
            "quantum computing", "5G", "edge computing", "API", "software"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            # Inject tech terms
            if random.random() > 0.5:
                term = random.choice(tech_terms)
                para = para.replace(
                    para.split()[random.randint(0, len(para.split())-1)],
                    term
                )
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _business_content(min_words: int, max_words: int) -> str:
        """Generate business-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        business_terms = [
            "revenue", "profit", "market share", "stakeholders", "investment",
            "ROI", "strategy", "competition", "merger", "acquisition",
            "quarter", "financial"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(business_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _health_content(min_words: int, max_words: int) -> str:
        """Generate health-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        health_terms = [
            "diagnosis", "treatment", "patient", "symptoms", "medical",
            "healthcare", "prevention", "wellness", "therapy", "research",
            "clinical", "disease"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(health_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _sports_content(min_words: int, max_words: int) -> str:
        """Generate sports-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        sports_terms = [
            "championship", "tournament", "athlete", "team", "coach",
            "victory", "defeat", "score", "season", "training",
            "competition", "league"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(sports_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _entertainment_content(min_words: int, max_words: int) -> str:
        """Generate entertainment-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        entertainment_terms = [
            "movie", "film", "actor", "director", "audience", "premiere",
            "box office", "streaming", "series", "episode", "celebrity",
            "performance"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(entertainment_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _politics_content(min_words: int, max_words: int) -> str:
        """Generate politics-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        politics_terms = [
            "government", "policy", "election", "parliament", "legislation",
            "democracy", "vote", "campaign", "politician", "reform",
            "political", "administration"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(politics_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _science_content(min_words: int, max_words: int) -> str:
        """Generate science-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        science_terms = [
            "research", "experiment", "hypothesis", "discovery", "laboratory",
            "scientist", "theory", "analysis", "data", "publication",
            "scientific", "methodology"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(science_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _education_content(min_words: int, max_words: int) -> str:
        """Generate education-related content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        education_terms = [
            "student", "teacher", "learning", "curriculum", "school",
            "university", "education", "course", "study", "exam",
            "academic", "classroom"
        ]

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            if random.random() > 0.5:
                term = random.choice(education_terms)
                words = para.split()
                if words:
                    words[random.randint(0, len(words)-1)] = term
                    para = " ".join(words)
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)

    @staticmethod
    def _generic_content(min_words: int, max_words: int) -> str:
        """Generate generic content."""
        paragraphs = []
        word_count = 0
        target = random.randint(min_words, max_words)

        while word_count < target:
            para = fake.paragraph(nb_sentences=random.randint(3, 6))
            paragraphs.append(para)
            word_count += len(para.split())

        return " ".join(paragraphs)
