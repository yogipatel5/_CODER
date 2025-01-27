import openai


class EmbeddingsService:
    """Service for managing embeddings for Notion pages."""

    def __init__(self):
        """Initialize the OpenAI client with local endpoint."""
        self.client = openai.OpenAI(
            base_url="http://127.0.0.1:1234", api_key="not-needed"  # API key not needed for local endpoint
        )
        self.model = "deepseek-r1-distill-qwen-14b"

    def update_page_embeddings(self, page):
        """
        Update embeddings for a given page using local OpenAI API.

        Args:
            page: The Page model instance to update embeddings for
        """
        if not page.content:
            page.embedding = None
            page.save(update_fields=["embedding"])
            return

        try:
            # Generate embeddings using the OpenAI API
            response = self.client.embeddings.create(model=self.model, input=page.content)

            # Extract the embedding from the response
            embedding = response.data[0].embedding

            # Store the embedding in the page model
            page.embedding = embedding
            page.save(update_fields=["embedding"])
        except Exception as e:
            # Log the error but don't raise it to prevent breaking the application
            print(f"Error generating embedding for page {page.id}: {str(e)}")
            page.embedding = None
            page.save(update_fields=["embedding"])
