from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from finance_assistant.data import load_financial_data
from finance_assistant.metrics import compute_metrics, format_context
from finance_assistant.llm import get_llm_answer, get_llm_answer_stream
from finance_assistant.display import (
    make_console,
    print_banner,
    print_metrics_table,
    print_summary_panel,
    print_chat_prompt,
    print_help,
    print_user_message,
    print_thinking,
    print_assistant_answer,
    print_error,
    print_history_cleared,
    print_goodbye,
)


def _load_env() -> None:
    base = Path(__file__).resolve().parent.parent
    for name in [".env", "../.env"]:
        p = base / name
        if p.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(p)
            except ModuleNotFoundError:
                with open(p) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break


def _detect_llm_mode() -> str:
    if os.getenv("DEEPSEEK_API_KEY"):
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        return f"DeepSeek ({model})"
    return "rule-based (нет DEEPSEEK_API_KEY)"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

    _load_env()

    base = Path(__file__).resolve().parent.parent
    csv_path = base / "financial_data.csv"
    if not csv_path.exists():
        csv_path = Path("financial_data.csv")
    if not csv_path.exists():
        print("Ошибка: файл financial_data.csv не найден.")
        sys.exit(1)

    console = make_console()

    print_banner(console)

    try:
        rows = load_financial_data(str(csv_path))
        metrics = compute_metrics(rows)
        context = format_context(metrics)
    except Exception as e:
        print_error(console, f"Не удалось загрузить данные: {e}")
        sys.exit(1)

    mode = _detect_llm_mode()
    if console is not None:
        from rich.panel import Panel
        llm_color = "green" if "Deep" in mode else "yellow"
        console.print(
            Panel(
                f"[dim]Данные загружены: [bold white]{len(rows)} лет[/bold white]  •  "
                f"Режим LLM: [bold {llm_color}]{mode}[/bold {llm_color}][/dim]",
                border_style="dim",
                padding=(0, 2),
            )
        )
        console.print()
    else:
        print(f"Данные загружены. Режим LLM: {mode}\n")

    print_metrics_table(console, metrics)
    console.print() if console else print()
    print_summary_panel(console, metrics)
    print_chat_prompt(console)

    conversation_history: list[dict[str, str]] = []
    turn = 0

    while True:
        try:
            if console is not None:
                from rich.prompt import Prompt
                question = Prompt.ask("[bold yellow]Вопрос[/bold yellow]").strip()
            else:
                question = input("Вопрос > ").strip()
        except (EOFError, KeyboardInterrupt):
            print_goodbye(console)
            break

        if not question:
            continue

        q_lower = question.lower()

        if q_lower in {"exit", "quit", "выход", "q"}:
            print_goodbye(console)
            break

        if q_lower in {"help", "помощь", "?"}:
            print_help(console)
            continue

        if q_lower in {"clear", "очистить", "reset"}:
            conversation_history.clear()
            turn = 0
            print_history_cleared(console)
            continue

        print_user_message(console, question)

        conversation_history.append({"role": "user", "content": question})

        spinner = print_thinking(console)
        try:
            use_stream = console is not None and os.getenv("DEEPSEEK_API_KEY")
            if use_stream:
                from rich.live import Live
                from rich.text import Text

                buf: list[str] = []

                def on_token(tok: str) -> None:
                    buf.append(tok)
                    live.update(Text("".join(buf)))

                with Live(Text(""), console=console, refresh_per_second=30) as live:
                    answer = get_llm_answer_stream(
                        question,
                        context,
                        conversation_history[:-1],
                        on_token,
                    )
            else:
                if spinner is not None:
                    with spinner:
                        answer = get_llm_answer(question, context, conversation_history[:-1])
                else:
                    answer = get_llm_answer(question, context, conversation_history[:-1])
        except Exception as e:
            answer = f"Произошла ошибка при обращении к LLM: {e}"

        turn += 1
        conversation_history.append({"role": "assistant", "content": answer})


        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        print_assistant_answer(console, answer, turn)
