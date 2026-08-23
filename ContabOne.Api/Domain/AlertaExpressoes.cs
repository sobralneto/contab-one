using System.Linq.Expressions;

namespace ContabOne.Api.Domain;

/// <summary>
/// Predicados de alerta compartilhados entre os endpoints e o job diário.
///
/// IMPORTANTE: nunca usar `a.Aberto` dentro de Where/Any — é propriedade
/// computada sem coluna e o EF lança InvalidOperationException ao traduzir.
/// O teste de tradução (ContabOne.Api.Tests/TraducaoLinqTest.cs) roda
/// ToQueryString() sobre estes predicados justamente para que uma regressão
/// a `a.Aberto` falhe a suíte em vez de estourar em produção.
/// </summary>
public static class AlertaExpressoes
{
    public static Expression<Func<Alerta, bool>> Aberto(
        Guid? escritorioId, TipoAlerta? tipo = null, Guid? clienteId = null)
        => a =>
            a.ResolvidoEm == null &&
            (escritorioId == null || a.EscritorioId == escritorioId) &&
            (tipo == null || a.Tipo == tipo) &&
            (clienteId == null || a.ClienteId == clienteId);
}
