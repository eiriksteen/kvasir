from typing import List, Optional
from google import genai
from google.genai import types

from kvasir_api.app_secrets import GOOGLE_API_KEY, EMBEDDING_DIM


async def embed(
    texts: List[str],
    embedding_dimensions: int = EMBEDDING_DIM,
    embedding_model: str = "gemini-embedding-001",
    client: Optional[genai.Client] = None
) -> List[List[float]]:
    """
    Embed a list of texts using the specified embedding model.
    """

    if embedding_model == "gemini-embedding-001":
        if client is None:
            client = genai.Client(api_key=GOOGLE_API_KEY)

        result = await client.aio.models.embed_content(
            model=embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=embedding_dimensions
            )
        )

        return [e.values for e in result.embeddings]

    raise ValueError(f"Unsupported embedding model: {embedding_model}")
