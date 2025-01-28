import logging
import os
import re

import numpy as np
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from notion.models.page import Page

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for managing embeddings for Notion pages."""

    def __init__(self):
        """Initialize the OpenAI client with local endpoint."""
        api_base = os.getenv("OPENAI_API_BASE", "http://10.16.1.11:1234")
        self.client = openai.OpenAI(
            base_url=f"{api_base}/v1",  # Update to include /v1 prefix
            api_key="not-needed",  # API key not needed for local endpoint
        )
        self.model = "gaianet/Nomic-embed-text-v1.5-Embedding-GGUF"  # E5-Mistral model
        self.max_content_length = 8192  # Maximum content length in characters
        self.target_dimensions = 384  # Target number of dimensions after compression'

        self.models = self.client.models.list()
        print(self.models)

    def _clean_content(self, page):
        """
        Clean and prepare page content for embedding generation.
        Uses the page's markdown content and cleans it for embedding.

        Args:
            page: The Page model instance

        Returns:
            str: Cleaned text content suitable for embedding
        """
        # Get markdown content using PageManager
        content = Page.objects.get_page_markdown(page.id)

        if not content:
            logger.warning(f"No content found for page {page.id}")
            return ""

        # Clean up the text
        text = re.sub(r"\s+", " ", content)  # Replace multiple spaces with single space
        text = re.sub(r"[^\w\s.,!?-]", "", text)  # Remove special characters except basic punctuation
        text = text.strip()

        # Add title if available
        if page.title:
            text = f"{page.title}\n\n{text}"

        # Save the cleaned content to the page model
        # TODO: Find out why the save is failing
        # try:
        #     page.content = text[: self.max_content_length]  # Truncate to max length
        #     page.save(update_fields=["content"])
        # except Exception as e:
        #     logger.error(f"Error saving page content for page {page.id}: {str(e)}")

        # Truncate if needed
        if len(text) > self.max_content_length:
            logger.warning(
                f"Content length ({len(text)}) exceeds maximum ({self.max_content_length}) "
                f"for page {page.id}. Truncating content."
            )
            text = text[: self.max_content_length]

        return text

    def _compress_embedding(self, embedding):
        """
        Compress embedding vector to fit within database limits.
        Uses dimensionality reduction while preserving as much information as possible.

        Args:
            embedding (list): Original embedding vector

        Returns:
            list: Compressed embedding vector
        """
        # Convert to numpy array for easier manipulation
        arr = np.array(embedding)

        # If the embedding is already small enough, return as is
        if len(arr) <= self.target_dimensions:
            return embedding.tolist()

        # Use average pooling to reduce dimensions
        # Reshape array into 2D where each row has target_dimensions elements
        n_chunks = len(arr) // self.target_dimensions
        remainder = len(arr) % self.target_dimensions

        if remainder > 0:
            # Pad the array to make it evenly divisible
            pad_size = self.target_dimensions - remainder
            arr = np.pad(arr, (0, pad_size), mode="mean")
            n_chunks = len(arr) // self.target_dimensions

        # Reshape and take mean along each column
        arr = arr.reshape(n_chunks, self.target_dimensions)
        compressed = np.mean(arr, axis=0)

        # Convert back to list and round to 6 decimal places to reduce size
        return [round(float(x), 6) for x in compressed]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
    def _generate_embedding(self, content):
        """
        Generate embeddings using the OpenAI API with retry mechanism.

        Args:
            content: The text content to generate embeddings for

        Returns:
            list: The generated embedding vector

        Raises:
            ValueError: If the API response is invalid or missing data
            openai.APIError: If the API request fails after all retries
        """
        try:
            response = self.client.embeddings.create(model=self.model, input=content)
            if not response.data:
                raise ValueError("API response missing embedding data")

            embedding = response.data[0].embedding
            return self._compress_embedding(embedding)

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
        except (AttributeError, TypeError, IndexError) as e:
            logger.error(f"Invalid API response format: {str(e)}")
            raise ValueError(f"Invalid API response format: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in embedding generation: {str(e)}")
            raise

    def update_page_embeddings(self, page):
        """
        Update embeddings for a given page using local OpenAI API.

        Args:
            page: The Page model instance to update embeddings for

        Raises:
            ValueError: If the API response is invalid
            openai.APIError: If the API request fails after retries
        """
        # Clean and prepare content
        content = self._clean_content(page)

        if not content:
            logger.info(f"No content found for page {page.id}, setting embedding to None")
            page.embedding = None
            page.save(update_fields=["embedding"])
            return

        try:
            embedding = self._generate_embedding(content)
            page.embedding = embedding
            page.save(update_fields=["embedding"])
            logger.info(f"Successfully updated embeddings for page {page.id}")
        except Exception as e:
            logger.error(f"Failed to update embeddings for page {page.id}: {str(e)}")
            page.embedding = None
            page.save(update_fields=["embedding"])
            raise  # Re-raise the exception after saving the null embedding

    def search_similar_pages(self, query, limit=5, similarity_threshold=0.7):
        """
        Search for pages with similar content using embedding similarity.

        Args:
            query (str): The search query
            limit (int): Maximum number of results to return
            similarity_threshold (float): Minimum cosine similarity score (0-1)

        Returns:
            QuerySet: QuerySet of pages with similarity scores, ordered by similarity
        """
        from django.db.models import FloatField, Func
        from django.db.models.functions import Cast

        query_embedding = self._generate_embedding(query)

        # Create a custom Func expression for vector similarity
        class CosineSimilarity(Func):
            function = ""
            template = "(1 - (%(expressions)s <=> '%(vector)s'::vector))"

            def __init__(self, expression, vector):
                vector_str = str(vector)  # Keep the square brackets
                super().__init__(expression, vector=vector_str)

        # Query using Django ORM
        return (
            Page.objects.filter(embedding__isnull=False, archived=False, in_trash=False)
            .annotate(similarity=Cast(CosineSimilarity("embedding", query_embedding), output_field=FloatField()))
            .filter(similarity__gte=similarity_threshold)
            .order_by("-similarity")[:limit]
        )
