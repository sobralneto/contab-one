namespace ContabOne.Api.Domain;

/// <summary>
/// Conteúdo da RegraColeta v1 semeada pela migration SeedRegraColetaV1 —
/// idêntico ao `BUNDLE_FABRICA` de Nfse.Agent/regras.py, que é congelado por
/// design ("o que o código sabia fazer sozinho na data em que foi escrito").
///
/// A migration interpola esta constante no momento em que é aplicada; o
/// BUNDLE_FABRICA nunca muda, então a migração continua equivalente em bancos
/// novos e antigos. O teste BundleSeedTest.cs garante que este conteúdo passa
/// no validador C# e é semanticamente igual ao corpus compartilhado
/// (testes/fixtures/bundles/bom.json) — se um divergir do outro, o teste
/// falha.
/// </summary>
public static class RegraSeedV1
{
    public const string Conteudo = """
        {
          "portal": {
            "urlLogin": "https://certificado.nfse.gov.br/EmissorNacional/Certificado",
            "urlNotas": "https://www.nfse.gov.br/EmissorNacional/Notas",
            "urlApiXml": "https://sefin.nfse.gov.br/sefinnacional/nfse",
            "maxDiasFiltro": 31,
            "paramPagina": "pg",
            "pausaEntreChamadasMs": 250,
            "listagens": {
              "recebidas": {
                "rota": "Recebidas",
                "executar": true,
                "colunas": ["geracao", "emitida_por", "competencia", "preco_servico", "situacao"]
              },
              "emitidas": {
                "rota": "Emitidas",
                "executar": false,
                "colunas": ["geracao", "emitida_para", "competencia", "municipio_emissor", "preco_servico", "situacao"]
              }
            }
          },
          "parsing": {
            "regexChave": "/Notas/Download/NFSe/(\\d{40,60})",
            "regexLinha": "<tr[^>]*>(.*?)</tr>",
            "regexTotalRegistros": "Total de\\s*(\\d+)\\s*registros?"
          }
        }
        """;
}
