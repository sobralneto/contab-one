using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ContabOne.Api.Migrations
{
    /// <summary>
    /// O catálogo de ferramentas do hub sai do enum e vira tabela.
    ///
    /// A ordem aqui é o ponto todo da migration, e é por isso que ela é
    /// escrita à mão: o scaffold do EF dropava "Produto" ANTES de migrar os
    /// dados e deixava todo agente com ProdutoId zerado, violando a FK e
    /// invalidando as chaves que estão nos config.toml dos clientes. A
    /// sequência correta é criar a tabela, semear, backfillar a partir do
    /// enum antigo, só então exigir NOT NULL e dropar a coluna velha.
    ///
    /// Os GUIDs dos produtos semeados são fixos de propósito: o backfill
    /// precisa referenciá-los, e uma reinstalação limpa tem que produzir os
    /// mesmos ids que um banco migrado.
    /// </summary>
    public partial class ProdutosComoTabela : Migration
    {
        // Valores do enum Produto que existia antes desta migration.
        private const int EnumNfse = 0;
        private const int EnumDet = 1;

        private const string IdNfse = "11111111-1111-4111-8111-111111111111";
        private const string IdDet = "22222222-2222-4222-8222-222222222222";

        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Produtos",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Codigo = table.Column<string>(type: "text", nullable: false),
                    Nome = table.Column<string>(type: "text", nullable: false),
                    Descricao = table.Column<string>(type: "text", nullable: false),
                    Ativo = table.Column<bool>(type: "boolean", nullable: false),
                    Ordem = table.Column<int>(type: "integer", nullable: false),
                    CriadoEm = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Produtos", x => x.Id);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Produtos_Codigo",
                table: "Produtos",
                column: "Codigo",
                unique: true);

            // Seed dos dois produtos que o enum já representava. `Codigo` é o
            // prefixo das chaves em campo — mexer nele quebra os agentes.
            migrationBuilder.Sql($"""
                INSERT INTO "Produtos" ("Id", "Codigo", "Nome", "Descricao", "Ativo", "Ordem", "CriadoEm")
                VALUES
                    ('{IdNfse}', 'nfse', 'NFS-e', 'Coleta de NFS-e no Portal Nacional', TRUE, 1, NOW() AT TIME ZONE 'UTC'),
                    ('{IdDet}', 'det', 'DET', 'Domicílio Eletrônico Trabalhista', TRUE, 2, NOW() AT TIME ZONE 'UTC');
                """);

            // Nullable primeiro: sem valor ainda para as linhas existentes.
            migrationBuilder.AddColumn<Guid>(
                name: "ProdutoId",
                table: "Agentes",
                type: "uuid",
                nullable: true);

            migrationBuilder.Sql($"""
                UPDATE "Agentes" SET "ProdutoId" = '{IdNfse}' WHERE "Produto" = {EnumNfse};
                UPDATE "Agentes" SET "ProdutoId" = '{IdDet}' WHERE "Produto" = {EnumDet};
                """);

            // Rede de segurança: qualquer linha que tenha escapado do mapa
            // acima vai para NFS-e, que é o único produto que existia quando
            // as chaves em campo foram emitidas. Sem isto o ALTER abaixo falha
            // e derruba o deploy inteiro.
            migrationBuilder.Sql($"""
                UPDATE "Agentes" SET "ProdutoId" = '{IdNfse}' WHERE "ProdutoId" IS NULL;
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "ProdutoId",
                table: "Agentes",
                type: "uuid",
                nullable: false);

            migrationBuilder.CreateIndex(
                name: "IX_Agentes_ProdutoId",
                table: "Agentes",
                column: "ProdutoId");

            migrationBuilder.AddForeignKey(
                name: "FK_Agentes_Produtos_ProdutoId",
                table: "Agentes",
                column: "ProdutoId",
                principalTable: "Produtos",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            // Só agora: os dados já estão do outro lado.
            migrationBuilder.DropColumn(
                name: "Produto",
                table: "Agentes");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<int>(
                name: "Produto",
                table: "Agentes",
                type: "integer",
                nullable: false,
                defaultValue: EnumNfse);

            // Volta o enum a partir da FK antes de perdê-la. Produto que não
            // existia no enum cai em NFS-e — o Down é caminho de emergência,
            // e deixar o agente autenticando importa mais que preservar a
            // distinção de um produto que a versão antiga não conhece.
            migrationBuilder.Sql($"""
                UPDATE "Agentes" SET "Produto" = {EnumDet} WHERE "ProdutoId" = '{IdDet}';
                UPDATE "Agentes" SET "Produto" = {EnumNfse} WHERE "ProdutoId" <> '{IdDet}';
                """);

            migrationBuilder.DropForeignKey(
                name: "FK_Agentes_Produtos_ProdutoId",
                table: "Agentes");

            migrationBuilder.DropIndex(
                name: "IX_Agentes_ProdutoId",
                table: "Agentes");

            migrationBuilder.DropColumn(
                name: "ProdutoId",
                table: "Agentes");

            migrationBuilder.DropTable(
                name: "Produtos");
        }
    }
}
