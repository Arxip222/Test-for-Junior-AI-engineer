from __future__ import annotations

from typing import Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    from rich.columns import Columns
    from rich import box
    from rich.style import Style
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def make_console() -> Any:
    if RICH_AVAILABLE:
        return Console()
    return None


def print_banner(console: Any) -> None:
    if not RICH_AVAILABLE or console is None:
        print("=" * 60)
        print("  ФИНАНСОВЫЙ AI-АССИСТЕНТ")
        print("=" * 60)
        return

    banner = Text()
    banner.append("╔══════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║  ", style="bold cyan")
    banner.append("📊 ФИНАНСОВЫЙ AI-АССИСТЕНТ", style="bold white")
    banner.append("  ║\n", style="bold cyan")
    banner.append("║  ", style="bold cyan")
    banner.append("Анализ данных компании 2005–2024    ", style="dim white")
    banner.append("║\n", style="bold cyan")
    banner.append("╚══════════════════════════════════════════╝", style="bold cyan")
    console.print(Align.center(banner))
    console.print()


def print_metrics_table(console: Any, metrics: dict[str, Any]) -> None:
    rows = metrics["metrics_by_year"]

    if not RICH_AVAILABLE or console is None:
        print("\n--- КЛЮЧЕВЫЕ МЕТРИКИ ---")
        print(f"{'Год':<6} {'Выручка $':>12} {'Рост %':>8} {'Оп.маржа %':>11} {'Чист.маржа %':>13}")
        print("-" * 55)
        for r in rows:
            rg = f"{r['revenue_growth']*100:.1f}%" if r["revenue_growth"] is not None else "—"
            om = f"{r['operating_margin']*100:.1f}%" if r["operating_margin"] is not None else "—"
            nm = f"{r['net_margin']*100:.1f}%" if r["net_margin"] is not None else "—"
            print(f"{r['year']:<6} {r['revenue']:>12,.0f} {rg:>8} {om:>11} {nm:>13}")
        return

    table = Table(
        title="📈 Финансовые показатели компании 2005–2024",
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold cyan",
        show_lines=False,
        title_style="bold white",
        expand=False,
    )

    table.add_column("Год", style="bold yellow", justify="center", width=6)
    table.add_column("Выручка ($)", justify="right", style="white", width=14)
    table.add_column("Рост выручки", justify="right", width=13)
    table.add_column("Оп. маржа", justify="right", width=11)
    table.add_column("Чистая маржа", justify="right", width=13)

    fastest_year = metrics["summary"]["fastest_revenue_growth"]["year"] if metrics["summary"]["fastest_revenue_growth"] else None

    for r in rows:
        rg_val = r["revenue_growth"]
        om_val = r["operating_margin"]
        nm_val = r["net_margin"]

        # Revenue growth cell
        if rg_val is None:
            rg_str = Text("—", style="dim")
        else:
            pct = rg_val * 100
            color = "bright_green" if pct >= 20 else "green" if pct >= 10 else "yellow"
            star = " ⭐" if r["year"] == fastest_year else ""
            rg_str = Text(f"{pct:.1f}%{star}", style=f"bold {color}" if r["year"] == fastest_year else color)

        om_str = Text(f"{om_val*100:.2f}%", style="cyan") if om_val is not None else Text("—", style="dim")
        nm_str = Text(f"{nm_val*100:.2f}%", style="magenta") if nm_val is not None else Text("—", style="dim")

        rev_fmt = f"${r['revenue']:>12,.0f}"

        table.add_row(
            str(r["year"]),
            rev_fmt,
            rg_str,
            om_str,
            nm_str,
        )

    console.print(table)


def print_summary_panel(console: Any, metrics: dict[str, Any]) -> None:
    s = metrics["summary"]
    if not RICH_AVAILABLE or console is None:
        print(f"\nПериод: {s['years_covered']}")
        print(f"Выручка: ${s['revenue_start']:,.0f} → ${s['revenue_end']:,.0f} (+{s['total_revenue_growth_percent']:.0f}%)")
        return

    fastest = s.get("fastest_revenue_growth")
    op = s.get("operating_margin_stats")
    net_s = s.get("net_margin_stats")

    lines = []
    lines.append(f"[bold white]Период:[/bold white] {s['years_covered']}  •  {s['total_years']} лет данных")
    lines.append(
        f"[bold white]Выручка:[/bold white] [yellow]${s['revenue_start']:,.0f}[/yellow] "
        f"[dim]→[/dim] [bright_green]${s['revenue_end']:,.0f}[/bright_green] "
        f"[dim](+{s['total_revenue_growth_percent']:.0f}% за период)[/dim]"
    )
    lines.append(
        f"[bold white]Чистая прибыль:[/bold white] [yellow]${s['net_income_start']:,.0f}[/yellow] "
        f"[dim]→[/dim] [bright_green]${s['net_income_end']:,.0f}[/bright_green] "
        f"[dim](+{s['total_net_income_growth_percent']:.0f}%)[/dim]"
    )
    if fastest:
        lines.append(f"[bold white]Рекорд роста:[/bold white] [bold bright_green]{fastest['year']} год ({fastest['growth_percent']:.1f}%)[/bold bright_green]")
    if op:
        lines.append(
            f"[bold white]Оп. маржа:[/bold white] [cyan]{op['min_value']*100:.1f}%[/cyan] – [cyan]{op['max_value']*100:.1f}%[/cyan] "
            f"[dim](ср. {op['avg_value']*100:.1f}%)[/dim]"
        )
    if net_s:
        lines.append(
            f"[bold white]Чистая маржа:[/bold white] [magenta]{net_s['min_value']*100:.1f}%[/magenta] – [magenta]{net_s['max_value']*100:.1f}%[/magenta] "
            f"[dim](ср. {net_s['avg_value']*100:.1f}%)[/dim]"
        )

    panel = Panel(
        "\n".join(lines),
        title="[bold cyan]📋 Сводка по компании[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(panel)


def print_chat_prompt(console: Any) -> None:
    if not RICH_AVAILABLE or console is None:
        print("\n" + "=" * 60)
        print("РЕЖИМ ЧАТА. Задавайте вопросы о финансовых данных.")
        print("Команды: exit / quit / выход — для завершения")
        print("         help / помощь — подсказки")
        print("=" * 60 + "\n")
        return

    console.print()
    console.rule("[bold cyan]💬 Финансовый чат[/bold cyan]", style="cyan")
    console.print(
        Panel(
            "[dim]Задавайте любые вопросы о финансовых данных компании.\n"
            "Команды: [bold]exit[/bold] / [bold]quit[/bold] / [bold]выход[/bold] — завершить  •  "
            "[bold]help[/bold] / [bold]помощь[/bold] — подсказки  •  "
            "[bold]clear[/bold] — очистить историю[/dim]",
            border_style="dim cyan",
            padding=(0, 2),
        )
    )
    console.print()


def print_help(console: Any) -> None:
    examples = [
        "В каком году был самый быстрый рост выручки?",
        "Как изменялась прибыльность со временем?",
        "Объясни динамику операционной маржи",
        "Сравни 2010 и 2020 год по всем показателям",
        "Когда компания росла быстрее всего?",
        "Какой была выручка в 2015 году?",
        "Найди лучший и худший год по рентабельности",
        "Как менялась чистая маржа после 2015 года?",
    ]

    if not RICH_AVAILABLE or console is None:
        print("\nПримеры вопросов:")
        for i, ex in enumerate(examples, 1):
            print(f"  {i}. {ex}")
        return

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("№", style="bold yellow", width=3)
    table.add_column("Вопрос", style="white")

    for i, ex in enumerate(examples, 1):
        table.add_row(f"{i}.", ex)

    console.print(
        Panel(
            table,
            title="[bold cyan]💡 Примеры вопросов[/bold cyan]",
            border_style="cyan",
        )
    )


def print_user_message(console: Any, text: str) -> None:
    if not RICH_AVAILABLE or console is None:
        print(f"\n[ВЫ]: {text}")
        return
    console.print(f"\n[bold yellow]▶ Вы:[/bold yellow] [white]{text}[/white]")


def print_thinking(console: Any) -> Any:
    """Return a context manager or None for 'thinking' spinner."""
    if not RICH_AVAILABLE or console is None:
        print("  Анализирую...")
        return None
    from rich.status import Status
    return console.status("[dim cyan]🔍 Анализирую данные...[/dim cyan]", spinner="dots")


def print_assistant_answer(console: Any, text: str, turn: int) -> None:
    if not RICH_AVAILABLE or console is None:
        print(f"\n[АССИСТЕНТ]:\n{text}\n")
        return

    console.print()
    console.print(
        Panel(
            text,
            title=f"[bold cyan]🤖 Ассистент[/bold cyan] [dim]#{turn}[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )


def print_error(console: Any, text: str) -> None:
    if not RICH_AVAILABLE or console is None:
        print(f"[ОШИБКА]: {text}")
        return
    console.print(f"[bold red]⚠ {text}[/bold red]")


def print_history_cleared(console: Any) -> None:
    if not RICH_AVAILABLE or console is None:
        print("История диалога очищена.")
        return
    console.print("[dim]История диалога очищена.[/dim]")


def print_goodbye(console: Any) -> None:
    if not RICH_AVAILABLE or console is None:
        print("\nДо свидания!")
        return
    console.print()
    console.rule("[dim]До свидания! 👋[/dim]", style="dim cyan")
