using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <summary>
    /// Quais ferramentas do hub cada escritório contratou.
    ///
    /// O backfill é a parte que não pode faltar: sem ele todo escritório
    /// nasceria com zero ferramentas e TODO agente em campo tomaria 401 no
    /// primeiro handshake depois do deploy. O critério é preservar o
    /// comportamento de hoje — até esta migration qualquer escritório podia
    /// usar qualquer ferramenta, então todos recebem todas as ativas. Restringir
    /// passa a ser ação deliberada do admin na tela de Escritórios.
    /// </summary>
    public partial class EscritorioProdutoContratado : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "EscritorioProdutos",
                columns: table => new
                {
                    EscritorioId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProdutoId = table.Column<Guid>(type: "uuid", nullable: false),
                    HabilitadoEm = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    DesabilitadoEm = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EscritorioProdutos", x => new { x.EscritorioId, x.ProdutoId });
                    table.ForeignKey(
                        name: "FK_EscritorioProdutos_Escritorios_EscritorioId",
                        column: x => x.EscritorioId,
                        principalTable: "Escritorios",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_EscritorioProdutos_Produtos_ProdutoId",
                        column: x => x.ProdutoId,
                        principalTable: "Produtos",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_EscritorioProdutos_ProdutoId",
                table: "EscritorioProdutos",
                column: "ProdutoId");

            // 1. Todo escritório existente recebe toda ferramenta ativa —
            //    preserva exatamente o que era possível antes desta migration.
            migrationBuilder.Sql("""
                INSERT INTO "EscritorioProdutos" ("EscritorioId", "ProdutoId", "HabilitadoEm")
                SELECT e."Id", p."Id", NOW()
                FROM "Escritorios" e
                CROSS JOIN "Produtos" p
                WHERE p."Ativo" = TRUE
                ON CONFLICT ("EscritorioId", "ProdutoId") DO NOTHING;
                """);

            // 2. Rede de segurança: escritório com agente de ferramenta INATIVA
            //    não seria coberto pelo passo 1 e o agente cairia. Quem já tem
            //    agente de um produto, tem o produto — sem exceção.
            migrationBuilder.Sql("""
                INSERT INTO "EscritorioProdutos" ("EscritorioId", "ProdutoId", "HabilitadoEm")
                SELECT DISTINCT a."EscritorioId", a."ProdutoId", NOW()
                FROM "Agentes" a
                ON CONFLICT ("EscritorioId", "ProdutoId") DO NOTHING;
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "EscritorioProdutos");
        }
    }
}
