To test the testcase generation:

run these series of command:
docker compose up -d
docker exec itp-ollama-1 ollama pull llama3.1:8b (only once)

python testcase_generation_scenario2_llm.py --file scenario2_captured.txt (for llama model)
OR
python testcase_generation_scenario2_llm.py --file scenario2_captured.txt --provider openai (for ChatGPT model)


