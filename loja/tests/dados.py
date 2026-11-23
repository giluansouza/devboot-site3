"""Shared fixtures: a small valid data set that every refusal test mutates one field of."""
import copy
from pathlib import Path

ML = "https://www.mercadolivre.com.br/produto-de-teste/up/MLBU1"


def produto(slug, **over):
    p = {
        "slug": slug,
        "nome": "Câmera de teste " + slug,
        "marca": "Intelbras",
        "modelo": "T-100",
        "linha": "cameras-e-gravadores",
        "tipo": "câmeras",
        "status": "ativo",
        "link_ml": ML,
        "resumo": "Resumo curto do produto de teste.",
        "beneficios": ["Primeiro benefício", "Segundo benefício", "Terceiro benefício"],
        "specs": [["Resolução", "2 MP"], ["Lente", "2,8 mm"], ["Proteção", "IP67"]],
        "pictograma": "bullet",
        "fotos": [],
        "fonte": ["https://www.intelbras.com/pt-br/produto-de-teste"],
    }
    p.update(over)
    return p


def dados(*produtos):
    return copy.deepcopy({
        "loja": {
            "site": "https://www.devboot.com.br",
            "whatsapp": "5587991402037",
            "vendedor_ml": "VENDEDOR_TESTE",
            "perfil_ml": "https://perfil.mercadolivre.com.br/VENDEDOR_TESTE",
            "revenda": "Revenda autorizada Intelbras",
            "instalacao": "Petrolina, Juazeiro, Dormentes e região",
            "ano": 2026,
        },
        "linhas": {
            "cameras-e-gravadores": {
                "nome": "Câmeras e gravadores", "descricao": "Descrição da linha de câmeras.",
                "vazio": "Texto da linha vazia de câmeras.", "pictograma": "bullet",
                "tipos": ["câmeras", "kits", "gravadores"]},
            "controle-de-acesso": {
                "nome": "Controle de acesso", "descricao": "Descrição da linha de acesso.",
                "vazio": "Texto da linha vazia de acesso.", "pictograma": "face",
                "tipos": ["controladores faciais", "fechaduras"]},
        },
        "produtos": list(produtos) or [produto("camera-um"), produto(
            "controlador-um", linha="controle-de-acesso", tipo="controladores faciais",
            pictograma="face")],
    })
