using System.Text.Json;
using System.Text.RegularExpressions;

namespace ContabOne.Api.Domain;

/// <summary>
/// Validação de schema do bundle de regras de coleta — espelho de
/// `regras.validar_bundle()` (Nfse.Agent/regras.py), que é a autoridade: um
/// bundle que o agente rejeita não é adotado, aconteça o que acontecer no
/// servidor. Este validador é um portão de usabilidade para o admin, não uma
/// fronteira de segurança.
///
/// As mensagens seguem o texto do Python para que o corpus compartilhado
/// (Nfse.Agent/testes/fixtures/bundles/manifest.json) confira os mesmos
/// vereditos nos dois validadores — exceto o detalhe do erro de regex, que
/// difere entre as engines (ver BundleCorpusTest).
///
/// Nunca lança: devolve a lista de campos/mensagens problemáticas (vazia =
/// válido), no mesmo princípio de dado vindo da rede não ser confiável.
/// </summary>
public static class RegraColetaValidator
{
    private static readonly string[] CamposUrl = ["urlLogin", "urlNotas", "urlApiXml"];
    private static readonly string[] TiposListagem = ["recebidas", "emitidas"];
    private static readonly string[] CamposRegex = ["regexChave", "regexLinha", "regexTotalRegistros"];

    public static List<string> Validar(string? conteudoJson)
    {
        var erros = new List<string>();

        JsonDocument? doc;
        try
        {
            doc = JsonDocument.Parse(conteudoJson ?? "null");
        }
        catch (JsonException)
        {
            doc = null;
        }

        if (doc is null || doc.RootElement.ValueKind != JsonValueKind.Object)
            return ["conteúdo não é um objeto JSON"];

        var raiz = doc.RootElement;

        // ── portal ──
        JsonElement portal;
        if (!raiz.TryGetProperty("portal", out portal) || portal.ValueKind != JsonValueKind.Object)
        {
            erros.Add("'portal' ausente ou não é um objeto");
            portal = default;
        }

        if (portal.ValueKind == JsonValueKind.Object)
        {
            foreach (var campo in CamposUrl)
            {
                if (!TryGetString(portal, campo, out var valor) || !valor.StartsWith("https://"))
                    erros.Add($"portal.{campo} ausente ou não é uma URL https");
            }

            if (!portal.TryGetProperty("maxDiasFiltro", out var maxDias) ||
                maxDias.ValueKind != JsonValueKind.Number ||
                !maxDias.TryGetInt32(out var maxDiasInt) ||
                maxDiasInt <= 0 || maxDiasInt > 366)
            {
                erros.Add("portal.maxDiasFiltro ausente ou fora da faixa esperada (1-366)");
            }

            if (!TryGetString(portal, "paramPagina", out var paramPagina) || string.IsNullOrEmpty(paramPagina))
                erros.Add("portal.paramPagina ausente ou vazio");

            if (!portal.TryGetProperty("listagens", out var listagens) || listagens.ValueKind != JsonValueKind.Object)
            {
                erros.Add("portal.listagens ausente ou não é um objeto");
                listagens = default;
            }

            if (listagens.ValueKind == JsonValueKind.Object)
            {
                foreach (var tipo in TiposListagem)
                {
                    if (!listagens.TryGetProperty(tipo, out var lst) || lst.ValueKind != JsonValueKind.Object)
                    {
                        erros.Add($"portal.listagens.{tipo} ausente ou não é um objeto");
                        continue;
                    }

                    if (!TryGetString(lst, "rota", out var rota) || string.IsNullOrEmpty(rota))
                        erros.Add($"portal.listagens.{tipo}.rota ausente ou vazia");

                    if (!lst.TryGetProperty("executar", out var executar) ||
                        executar.ValueKind != JsonValueKind.True && executar.ValueKind != JsonValueKind.False)
                    {
                        erros.Add($"portal.listagens.{tipo}.executar ausente ou não é booleano");
                    }

                    if (!lst.TryGetProperty("colunas", out var colunas) ||
                        colunas.ValueKind != JsonValueKind.Array ||
                        colunas.GetArrayLength() == 0 ||
                        colunas.EnumerateArray().Any(c => c.ValueKind != JsonValueKind.String))
                    {
                        erros.Add($"portal.listagens.{tipo}.colunas ausente ou inválida");
                    }
                }
            }
        }

        // ── parsing ──
        JsonElement parsing;
        if (!raiz.TryGetProperty("parsing", out parsing) || parsing.ValueKind != JsonValueKind.Object)
        {
            erros.Add("'parsing' ausente ou não é um objeto");
            parsing = default;
        }

        if (parsing.ValueKind == JsonValueKind.Object)
        {
            foreach (var campo in CamposRegex)
            {
                if (!TryGetString(parsing, campo, out var padrao) || string.IsNullOrEmpty(padrao))
                {
                    erros.Add($"parsing.{campo} ausente ou vazio");
                    continue;
                }
                try
                {
                    _ = new Regex(padrao, RegexOptions.None, TimeSpan.FromSeconds(1));
                }
                catch (RegexParseException)
                {
                    // Sem o detalhe do erro: o texto da exceção difere entre
                    // .NET e Python, e o veredito do corpus compara campos.
                    erros.Add($"parsing.{campo} não é uma expressão regular válida");
                }
            }
        }

        return erros;
    }

    private static bool TryGetString(JsonElement obj, string nome, out string valor)
    {
        if (obj.TryGetProperty(nome, out var el) && el.ValueKind == JsonValueKind.String)
        {
            valor = el.GetString()!;
            return true;
        }
        valor = string.Empty;
        return false;
    }
}
