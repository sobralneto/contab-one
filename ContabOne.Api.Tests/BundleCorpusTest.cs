using System.Text.Json;
using ContabOne.Api.Domain;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// Roda o validador C# (RegraColetaValidator) contra o MESMO corpus que o
/// teste Python (Nfse.Agent/testes/teste_corpus_bundles.py) roda contra
/// `regras.validar_bundle()` — manifest em
/// Nfse.Agent/testes/fixtures/bundles/manifest.json. Se os dois validadores
/// divergirem, um dos dois testes falha.
///
/// O veredito compara CAMPOS problemáticos (primeira palavra de cada
/// mensagem, sem aspas), não o texto completo: o detalhe do erro de regex
/// difere entre as engines.
/// </summary>
public class BundleCorpusTest
{
    private static string CampoDaMensagem(string mensagem)
        => mensagem.Trim().Trim('\'').Split(' ', 2)[0];

    private static DirectoryInfo LocalizarCorpus()
    {
        // CWD é ContabOne.Api.Tests/ durante o dotnet test; sobe até achar a
        // pasta do agente (raiz do repo).
        var dir = new DirectoryInfo(Environment.CurrentDirectory);
        while (dir != null)
        {
            var candidato = Path.Combine(dir.FullName, "Nfse.Agent", "testes", "fixtures", "bundles");
            if (Directory.Exists(candidato))
                return new DirectoryInfo(candidato);
            dir = dir.Parent;
        }
        throw new DirectoryNotFoundException(
            "Corpus de bundles não encontrado (Nfse.Agent/testes/fixtures/bundles)");
    }

    [Fact]
    public void ValidadorConfereTodosOsVerditosDoCorpus()
    {
        var corpus = LocalizarCorpus();
        var manifest = JsonDocument.Parse(
            File.ReadAllText(Path.Combine(corpus.FullName, "manifest.json")));

        var casos = manifest.RootElement.GetProperty("casos").EnumerateArray().ToList();
        Assert.True(casos.Count >= 8, "o corpus tem pelo menos os casos essenciais");

        foreach (var caso in casos)
        {
            var arquivo = caso.GetProperty("arquivo").GetString()!;
            var esperado = caso.GetProperty("campos").EnumerateArray()
                .Select(c => c.GetString()!)
                .ToHashSet();

            var conteudo = File.ReadAllText(Path.Combine(corpus.FullName, arquivo));
            var erros = RegraColetaValidator.Validar(conteudo);
            var obtido = erros.Select(CampoDaMensagem).ToHashSet();

            Assert.True(obtido.SetEquals(esperado),
                $"{arquivo}: campos problemáticos [{string.Join(", ", obtido)}] != [{string.Join(", ", esperado)}]");
        }
    }
}
