## Course Finder

An app that uses LLMs to refine user prompts to do RAG on course syllabi to help with finding a course at Chalmers University of Technology. Hosted at https://course-finder.se/.

### Features
- Syllabus refinement using `gpt-oss:20b-cloud`, which runs on Ollama Cloud, to unify the language in the syllabi and make them of similar length for easier RAG.
- Course data and embeddings are persisted in a Chroma store under a small Chroma vector database in `.chroma/`. The syllabi are embedded using `mxbai-embed-large:335m`, which runs locally via Ollama.
- User course refinement using `gpt-oss:20b-cloud` to change a user's prompt into a "course syllabus" to match it to the ones in the database.
- The pipeline returns the closest matching courses from the database and returns them as a list. The syllabi in the list are also given to `gpt-oss:20b-cloud` along with the user prompt to pick the most relevant courses (or none) to show to the user as the recommendation, along with the extracted list from database.
- The app uses FastAPI to expose the pipeline as an HTTP API that the frontend calls.


### Rebuilding the course data / vector store

```sh
uv run -m recommender.data_extracting --scrape --parse
uv run -m recommender.db
```

### Local run

```sh
uv sync
ollama signin
ollama pull mxbai-embed-large:335m
uv run uvicorn recommender:app --port 8000 --host 0.0.0.0
```

### Deployment

Runs on an Oracle Cloud VM as a `systemd` service, exposed through a Cloudflare tunnel. Full setup steps and config templates are in [deploy/](deploy/).
