import asyncio
import aiohttp
import time

k_url = "http://127.0.0.1"
URL = k_url + ":5000/api/v1/ollama/ask_async"

# Lista de perguntas diferentes
QUESTIONS = [
    {"agent": "qwen3:1.7b", "content": "/no_think"+"Olá! Explique a relatividade.", "template": "/no_think"+"Explique de forma simples"},
    {"agent": "qwen2.5:1.5b", "content": "/no_think"+"Você pode resumir a teoria das cordas?", "template": "/no_think"+"Explicação detalhada"},
    {"agent": "deepseek-r1:1.5b", "content": "/no_think"+"O que é inteligência artificial?", "template": "/no_think"+"Explique para iniciantes"}]

NUM_REQUESTS = len(QUESTIONS)

async def fetch(session, idx, payload):
    start = time.perf_counter()
    response_text = ""
    try:
        async with session.post(URL, json=payload, timeout=None) as resp:
            async for chunk in resp.content.iter_any():
                text = chunk.decode("utf-8")
                response_text += text
            elapsed = time.perf_counter() - start
            return elapsed, resp.status, response_text
    except Exception as e:
        return None, str(e), ""

async def main():
    async with aiohttp.ClientSession() as session:

        tasks = [fetch(session, i, QUESTIONS[i]) for i in range(NUM_REQUESTS)]
        start_all = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_all

    times = [r[0] for r in results if r[0] is not None]
    statuses = [r[1] for r in results]

    print(f"🚀 Total de requisições: {NUM_REQUESTS}")
    print(f"⏱️ Tempo total: {total_time:.2f}s")
    print(f"📊 Tempo médio por requisição: {sum(times)/len(times):.2f}s")
    print(f"✅ Sucessos: {statuses.count(200)}")
    print(f"❌ Falhas: {len([s for s in statuses if s != 200])}")
    print("\n📄 Respostas:\n")
    for i, r in enumerate(results):
        print(f"Pergunta {i+1}: {QUESTIONS[i]['content']}")
        print(f"Resposta: {r[2]}\n{'-'*50}\n")

if __name__ == "__main__":
    asyncio.run(main())
