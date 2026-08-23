using System.Text.Json;
using ContabOne.Api.Domain;
using Xunit;

namespace ContabOne.Api.Tests;

/// <summary>
/// O conteúdo semeado pela migration SeedRegraColetaV1 (RegraSeedV1.Conteudo)
/// precisa (a) passar no validador C# — senão a v1 seria publicada e rejeitada
/// por todos os agentes — e (b) continuar semanticamente idêntico ao corpus
/// compartilhado (testes/fixtures/bundles/bom.json), que espelha o
/// BUNDLE_FABRICA do agente.
/// </summary>
public class BundleSeedTest
{
    private static DirectoryInfo LocalizarCorpus()
    {
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
    public void ConteudoSemeado_PassaNoValidador()
    {
        var erros = RegraColetaValidator.Validar(RegraSeedV1.Conteudo);
        Assert.Empty(erros);
    }

    [Fact]
    public void ConteudoSemeado_IgualAoCorpusBom()
    {
        var corpus = LocalizarCorpus();
        var bom = File.ReadAllText(Path.Combine(corpus.FullName, "bom.json"));

        using var docSeed = JsonDocument.Parse(RegraSeedV1.Conteudo);
        using var docCorpus = JsonDocument.Parse(bom);

        // Comparação semântica (indentação pode diferir entre os arquivos).
        Assert.Equal(
            JsonSerializer.Serialize(docSeed.RootElement),
            JsonSerializer.Serialize(docCorpus.RootElement));
    }
}
