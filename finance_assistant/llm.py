from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

SYSTEM_PROMPT = """\
Ты — точный финансовый аналитик-ассистент. Твоя задача — давать чёткие, структурированные, \
инсайтовые ответы исключительно на основе предоставленных финансовых данных.

ЖЁСТКИЕ ПРАВИЛА:
1. НИКОГДА не придумывай числа. Используй только цифры из поля "данные компании".
2. Если данных недостаточно — прямо скажи об этом.
3. Всегда объясняй логику расчётов словами.
4. Отвечай на русском языке.
5. Используй структурированный формат: заголовок, ключевые факты, вывод.
6. Когда нужен расчёт — показывай формулу и подставляй числа из данных.
7. Делай аналитические выводы, замечай тренды, аномалии, периоды ускорения/замедления.
8. Форматируй числа понятно: миллионы как "3.65 млн $", проценты как "25.2%".

ФОРМАТ ОТВЕТА:
- Начни с прямого ответа на вопрос (1-2 предложения).
- Присылай ответ без md форматирования (** и прочего).
- Затем детальный анализ с данными.
- Ответы нужны четкие и по факту.
- Используй символы ▶ для ключевых пунктов, → для выводов.
- Старайся давать ответы максимально короткие и понятные.

ПРИМЕРЫ ВОПРОСОВ-ОТВЕТОВ:
Вопрос:
В каком году был самый быстрый рост выручки?

Ожидаемый ответ:
Самый быстрый рост выручки был в 2006 году (≈ 29.2%).


Вопрос:
Как изменялась прибыльность компании со временем?

Ожидаемый ответ:
Если опираться строго на данные:
Операционная маржа на протяжении всех лет держится примерно на уровне ~25%
Чистая маржа также стабильно около ~25%
Это означает, что прибыльность компании практически не менялась со временем.
"""


def get_llm_answer(question: str, context: str, history: list[dict[str, str]]) -> str:
    """Try DeepSeek, fallback to rule-based if no API key."""
    answer = _try_deepseek(question, context, history)
    if answer:
        return answer

    return _rule_based_fallback(question, context)


def get_llm_answer_stream(
    question: str,
    context: str,
    history: list[dict[str, str]],
    on_token: Callable[[str], None],
) -> str:
    """
    Stream DeepSeek answer into console via on_token callback.
    Falls back to deterministic rule-based answer when DeepSeek isn't available.
    """
    answer = _try_deepseek_stream(question, context, history, on_token)
    if answer is not None:
        return answer
    return _rule_based_fallback(question, context)


def _try_deepseek(question: str, context: str, history: list[dict[str, str]]) -> str | None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})

        user_content = (
            f"Данные компании (все расчёты из financial_data.csv):\n```json\n{context}\n```\n\n"
            f"Вопрос пользователя:\n{question}"
        )
        messages.append({"role": "user", "content": user_content})

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


def _try_deepseek_stream(
    question: str,
    context: str,
    history: list[dict[str, str]],
    on_token: Callable[[str], None],
) -> str | None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        )
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})

        user_content = (
            f"Данные компании (все расчёты из financial_data.csv):\n```json\n{context}\n```\n\n"
            f"Вопрос пользователя:\n{question}"
        )
        messages.append({"role": "user", "content": user_content})

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
            stream=True,
        )

        chunks: list[str] = []
        for event in resp:
            try:
                delta = event.choices[0].delta
                token = None

                if isinstance(delta, dict):
                    token = delta.get("content")
                else:
                    token = getattr(delta, "content", None)
                    if token is None:
                        try:
                            token = delta.get("content")  # type: ignore[attr-defined]
                        except Exception:
                            token = None
            except Exception:
                token = None
            if token is not None and token != "":
                chunks.append(token)
                on_token(token)

        return "".join(chunks).strip()
    except Exception:
        return None


def _rule_based_fallback(question: str, context: str) -> str:
    """Simple deterministic fallback when no API key is set."""
    import json
    try:
        data = json.loads(context)
    except Exception:
        return "Ошибка: не удалось разобрать данные."

    s = data.get("summary", {})
    q = question.lower()

    fastest = s.get("fastest_revenue_growth")
    op = s.get("operating_margin_stats")
    net = s.get("net_margin_stats")
    rg = s.get("revenue_growth_stats")

    if "быстр" in q and "рост" in q:
        if fastest:
            return (
                f"▶ Самый быстрый рост выручки: {fastest['year']} год\n"
                f"  Рост составил ≈ {fastest['growth_percent']:.1f}%\n\n"
                f"→ Расчёт: (revenue[{fastest['year']}] - revenue[{fastest['year']-1}]) / revenue[{fastest['year']-1}] × 100"
            )

    if ("как" in q or "измен" in q or "тренд" in q) and "прибыль" in q:
        parts = []
        if op:
            parts.append(f"▶ Операционная маржа: {op['min_value']*100:.1f}% – {op['max_value']*100:.1f}% (среднее {op['avg_value']*100:.1f}%)")
        if net:
            parts.append(f"▶ Чистая маржа: {net['min_value']*100:.1f}% – {net['max_value']*100:.1f}% (среднее {net['avg_value']*100:.1f}%)")
        if parts:
            return "\n".join(parts) + "\n\n→ Прибыльность компании остаётся стабильной на протяжении всего периода."

    if "операционн" in q and "марж" in q:
        if op:
            return (
                f"▶ Операционная маржа {s.get('years_covered','')}\n"
                f"  Минимум: {op['min_value']*100:.2f}% ({op['min_year']})\n"
                f"  Максимум: {op['max_value']*100:.2f}% ({op['max_year']})\n"
                f"  Среднее: {op['avg_value']*100:.2f}%\n\n"
                f"→ Формула: (Revenue - COGS - OpEx) / Revenue × 100"
            )

    if "чист" in q and "марж" in q:
        if net:
            return (
                f"▶ Чистая маржа {s.get('years_covered','')}\n"
                f"  Минимум: {net['min_value']*100:.2f}% ({net['min_year']})\n"
                f"  Максимум: {net['max_value']*100:.2f}% ({net['max_year']})\n"
                f"  Среднее: {net['avg_value']*100:.2f}%\n\n"
                f"→ Формула: Net Income / Revenue × 100"
            )

    # Generic summary
    lines = []
    if fastest:
        lines.append(f"▶ Самый быстрый рост выручки: {fastest['year']} год ({fastest['growth_percent']:.1f}%)")
    if op:
        lines.append(f"▶ Операционная маржа: {op['min_value']*100:.1f}%–{op['max_value']*100:.1f}% (ср. {op['avg_value']*100:.1f}%)")
    if net:
        lines.append(f"▶ Чистая маржа: {net['min_value']*100:.1f}%–{net['max_value']*100:.1f}% (ср. {net['avg_value']*100:.1f}%)")
    lines.append(f"\n→ Период: {s.get('years_covered')}, выручка: {s.get('revenue_start'):,.0f} $ → {s.get('revenue_end'):,.0f} $")

    return "\n".join(lines) if lines else "Недостаточно данных для ответа."
