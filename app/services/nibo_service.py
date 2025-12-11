import httpx

class NiboService:
    BASE = "https://api.nibo.com.br/empresas/v1/"

    # ============================================================
    # PERFIL
    # ============================================================
    async def get_empresa_profile(self, token: str):
        data = await self._get(token, "organizations")

        if not isinstance(data, dict) or "items" not in data or len(data["items"]) == 0:
            raise Exception("Token Nibo inválido ou empresa inacessível.")

        empresa = data["items"][0]

        return {
            "nome": empresa.get("name"),
            "cnpj": empresa.get("cnpj"),
            "companyId": empresa.get("organizationId"),
        }

    # ============================================================
    # ENDPOINTS
    # ============================================================
    async def get_costcenters(self, token: str):
        return await self._get(token, "costcenters")

    async def get_receipts(self, token: str, skip: int = 0, top: int = 500):
        return await self._get_paginated_order_date(token, "receipts", skip, top)

    async def get_payments(self, token: str, skip: int = 0, top: int = 500):
        return await self._get_paginated_order_date(token, "payments", skip, top)

    # ============================================================
    # MÉTODOS BASE
    # ============================================================
    async def _get(self, token, endpoint):
        url = f"{self.BASE}{endpoint}"
        headers = {"accept": "application/json", "apitoken": token}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code >= 400:
            raise Exception(resp.text)

        return resp.json()

    async def _get_paginated_order_date(self, token: str, endpoint: str, skip: int, top: int):
        url = f"{self.BASE}{endpoint}?$orderby=date&$skip={skip}&$top={top}"
        headers = {"accept": "application/json", "apitoken": token}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)

        if resp.status_code >= 400:
            raise Exception(f"Erro Nibo GET paginado {endpoint}: {resp.text}")

        return resp.json()


# ============================================================
# FUNÇÃO DE PAGINAÇÃO RESILIENTE (para receipts/payments)
# ============================================================
async def fetch_all_pages(fetch_fn, token):
    results = []
    skip = 0
    top = 500

    while True:
        # fetch_fn aqui deve ser RECEIPTS ou PAYMENTS
        page = await fetch_fn(token, skip=skip, top=top)

        items = page.get("items") or page.get("value") or []

        results.extend(items)

        if len(items) < top:
            break

        skip += top

    return results

async def fetch_all(token, fetch_fn):
    try:
        data = await fetch_fn(token)
        return data.get("items") or []
    except Exception:
        return []


nibo_service = NiboService()
