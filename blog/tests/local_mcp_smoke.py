"""Real stdio MCP -> local HTTP blog test using clearly identified sample history."""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def structured(result):
    if result.isError:
        raise AssertionError(result.content)
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(next(block.text for block in result.content if block.type == "text"))


async def main():
    base_url = os.getenv("BLOG_LOCAL_URL", "http://127.0.0.1:18973").rstrip("/")
    token = os.environ["BLOG_API_TOKEN"]
    with tempfile.TemporaryDirectory(prefix="devboot-mcp-history-test-") as directory:
        original = ("# Demonstração de histórico local\n\n"
            "Este resultado é fictício e serve apenas para testar a importação pelo MCP. "
            "Ele não foi obtido dos agendamentos da conta do usuário.\n\n"
            "O teste verifica a leitura da fonte, a identificação da edição e a publicação no blog local.")
        (Path(directory) / "demonstracao.md").write_text(original)
        params = StdioServerParameters(command=sys.executable,
            args=[str(Path(__file__).resolve().parent.parent / "local_mcp.py")],
            env={"BLOG_LOCAL_URL": base_url, "BLOG_API_TOKEN": token, "BLOG_HISTORY_DIR": directory})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {"list_history_entries", "read_history_entry", "create_history_article"}.issubset({tool.name for tool in tools.tools})
                history = structured(await session.call_tool("list_history_entries", {}))
                entry = history["entries"][0]
                source = structured(await session.call_tool("read_history_entry", {"entry_id": entry["entry_id"]}))
                assert source["content_markdown"] == original
                # Deterministic demo formatting; real editorial conversion is done by the assistant.
                article = dict(title="Demonstração: histórico importado pelo MCP", slug="demonstracao-historico-mcp",
                    excerpt="Uma demonstração local da leitura de histórico e publicação por MCP. Este conteúdo não veio dos seus agendamentos.",
                    content_markdown="## Demonstração do fluxo local\n\n" + original.split("\n\n", 1)[1],
                    category="Demonstração", status="published")
                args = {"entry_id": entry["entry_id"], "source_sha256": source["content_sha256"], "article": article}
                result = structured(await session.call_tool("create_history_article", args))
                assert result["article"]["status"] == "published"
                retry = structured(await session.call_tool("create_history_article", args))
                assert retry["created"] is False
                with urlopen(base_url + "/blog/demonstracao-historico-mcp/", timeout=10) as page:
                    assert "Demonstração do fluxo local" in page.read().decode()
                print("PASS: cliente MCP real -> histórico de exemplo -> fonte lida -> publicação HTTP -> página do blog -> reenvio sem duplicação.")
                print("A demonstração NÃO importou o histórico da conta ChatGPT.")


if __name__ == "__main__":
    asyncio.run(main())
