# Generated by Django 5.1.5 on 2025-01-27 22:14

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notion", "0009_page_notion_page_embedding_idx"),
    ]

    operations = [
        # Create the vector extension if it doesn't exist
        migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS vector;", "DROP EXTENSION IF EXISTS vector;"),
        # Convert embedding column to vector type
        migrations.RunSQL(
            "ALTER TABLE notion_page ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector;",
            # Revert back to array type if needed
            "ALTER TABLE notion_page ALTER COLUMN embedding TYPE double precision[] USING embedding::double precision[];",
        ),
        # Create an index on the vector column
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS notion_page_embedding_vector_idx ON notion_page USING ivfflat (embedding vector_cosine_ops);",
            "DROP INDEX IF EXISTS notion_page_embedding_vector_idx;",
        ),
    ]
