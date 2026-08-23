using Microsoft.EntityFrameworkCore.Migrations;
using ContabOne.Api.Domain;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <inheritdoc />
    public partial class SeedRegraColetaV1 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Seed idempotente da regra v1 — conteúdo idêntico ao BUNDLE_FABRICA
            // de Nfse.Agent/regras.py (RegraSeedV1.Conteudo), para que todo
            // ambiente nasça com uma regra ativa e a publicação de v2 em diante
            // fique destravada. O BUNDLE_FABRICA é congelado por design, então
            // interpolar a constante aqui não muda o que bancos já migrados
            // receberam.
            //
            // WHERE NOT EXISTS (tabela vazia): se alguém já publicou regras
            // (ex.: v3), inserir uma v1 colidiria com o índice único de Versao
            // e regrediria a numeração. Estado inicial, aplicado uma vez.
            //
            // Escolhido sobre HasData de propósito: HasData faz o EF tratar a
            // linha como parte permanente do modelo e querer "restaurá-la" em
            // migrations futuras (ver design.md, Decisão 4).
            migrationBuilder.Sql($"""
                INSERT INTO "RegraColetas" ("Id", "Versao", "Conteudo", "PublicadaEm", "Ativa")
                SELECT '{Guid.NewGuid():D}', 1, '{RegraSeedV1.Conteudo.Replace("'", "''")}', now(), true
                WHERE NOT EXISTS (SELECT 1 FROM "RegraColetas");
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            // Só remove o que esta migration inseriu: a v1 semeada num banco
            // que não tinha regra nenhuma.
            migrationBuilder.Sql("""
                DELETE FROM "RegraColetas" WHERE "Versao" = 1
                  AND NOT EXISTS (SELECT 1 FROM "RegraColetas" WHERE "Versao" <> 1);
                """);
        }
    }
}
