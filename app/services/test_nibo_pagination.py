import httpx
import json
import asyncio

BASE = "https://api.nibo.com.br/empresas/v1/"
TOKEN = "DEA8947BAF0B47FE9725D53EB414436D"

ENDPOINT = "costcenters"   # ou "payments", "costcenters", etc.


async def fetch_page(url):
    headers = {"accept": "application/json", "apitoken": TOKEN}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)

    print("\n=======================================")
    print("URL CONSULTADA:", url)
    print("STATUS:", resp.status_code)
    print("=======================================\n")

    try:
        data = resp.json()
    except:
        print("RESPOSTA NÃO É JSON")
        print(resp.text)
        return None

    print(json.dumps(data, indent=2))  # <-- imprime TUDO da API

    return data


async def main():
    # Primeira requisição SEM paginação
    url = f"{BASE}{ENDPOINT}"
    page = await fetch_page(url)

    if not isinstance(page, dict):
        print("Resposta não é um objeto dict")
        return

    # Tentar achar campos de paginação automaticamente
    keys = list(page.keys())
    print("\nCHAVES ENCONTRADAS NA PÁGINA:")
    print(keys)

    next_page_candidates = [
        k for k in keys if "next" in k.lower() or "token" in k.lower() or "link" in k.lower()
    ]

    print("\nCAMPOS POSSÍVEIS DE PAGINAÇÃO:")
    print(next_page_candidates)

    # Se existir nextPageToken
    if "nextPageToken" in page and page["nextPageToken"]:
        print("\n⚠️ ACHOU nextPageToken, testando próxima página...")
        next_url = f"{BASE}{ENDPOINT}?pageToken={page['nextPageToken']}"
        await fetch_page(next_url)
        return

    # Se existir continuationToken
    if "continuationToken" in page and page["continuationToken"]:
        print("\n⚠️ ACHOU continuationToken, testando próxima página...")
        next_url = f"{BASE}{ENDPOINT}?continuationToken={page['continuationToken']}"
        await fetch_page(next_url)
        return

    # Se existir nextLink ou @odata.nextLink
    for key in ["nextLink", "@odata.nextLink", "odata.nextLink"]:
        if key in page:
            print(f"\n⚠️ ACHOU {key}, testando próxima página...")
            next_url = page[key]
            await fetch_page(next_url)
            return

    print("\n❌ Nenhum campo de paginação detectado.")
    print("Provavelmente este endpoint NÃO pagina por token.")


if __name__ == "__main__":
    asyncio.run(main())
